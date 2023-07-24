from __future__ import annotations
import typing as tp
import os
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
import subprocess
import shlex

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

from pyrtlsdrlib import BuildType, FileType, BuildFile, get_os_type

from common import *

def sh(cmd_str, check=True, **kwargs):
    logger.debug(f'$ {cmd_str}')
    return subprocess.run(shlex.split(cmd_str), check=check, **kwargs)

@contextmanager
def build_dir_maker(p: Path|None = None, use_tmp: bool = False, cleanup: bool = True):
    if use_tmp:
        p = tempfile.mkdtemp()
    try:
        yield Path(p)
    finally:
        if use_tmp and cleanup:
            shutil.rmtree(p)

class Builder:
    def __init__(self, release: 'github.GitRelease', asset, lib_dest: Path):
        self.release = release
        self.asset = asset
        self.lib_dest = lib_dest
        self.tmpdir = None
        self.source_dir = None
        self.cmake_build_dir = None
        self._acquired = False
        self._orig_cwd = None

    def __enter__(self):
        if self._acquired:
            raise Exception('Already acquired')
        self._acquired = True
        self._orig_cwd = Path.cwd()
        return self

    def __exit__(self, *args):
        if self._acquired:
            self._acquired = False
            if self._orig_cwd is not None and self._orig_cwd.exists():
                logger.debug(f'chdir to {self._orig_cwd}')
                os.chdir(self._orig_cwd)
        self._orig_cwd = None
        self.tmpdir = None
        self.source_dir = None
        self.cmake_build_dir = None
        self._orig_cwd = None

    @logger.catch
    def build(self) -> tp.List[BuildFile]:
        # with tempfile.TemporaryDirectory() as tmpdir:
        with build_dir_maker(None, use_tmp=True, cleanup=True) as tmpdir:
            logger.info(f'Building source asset: {self.asset}')
            tmpdir = self.tmpdir = Path(tmpdir)
            tar_fn = self.asset.download_to(tmpdir)
            logger.debug(f'unpacking {tar_fn} to {tmpdir}')
            shutil.unpack_archive(tar_fn, tmpdir)
            src_dir = [p for p in tmpdir.iterdir() if p.is_dir() and p != tar_fn]
            logger.debug(f'{src_dir=}')
            assert len(src_dir) == 1
            self.source_dir = src_dir[0]
            self.do_cmake()
            build_files = self.copy_builds_to_project()
            logger.success('Build complete')
            return build_files

    def do_cmake(self):
        logger.info('Running cmake')
        assert self.source_dir is not None
        self.cmake_build_dir = self.source_dir / 'build'
        self.cmake_build_dir.mkdir()
        sh(f'cmake -S {self.source_dir} -B {self.cmake_build_dir}')
        logger.debug(f'chdir to {self.cmake_build_dir}')
        os.chdir(self.cmake_build_dir)
        assert Path.cwd().samefile(self.cmake_build_dir)
        sh('make -j 4')
        logger.success('cmake complete')

    def copy_builds_to_project(self) -> tp.List[BuildFile]:
        assert self.cmake_build_dir is not None
        src = self.cmake_build_dir / 'src'
        src = src.resolve()
        logger.info(f'Copying builds from {src} to {self.lib_dest}')

        source_filenames = set(src.glob('librtlsdr*'))
        symlinks = []
        build_files = []
        build_type = get_os_type()
        assert build_type.filter_archs() == BuildType.arm64

        for src_fn in source_filenames.copy():
            if not src_fn.is_symlink():
                continue
            linked_file = src_fn.resolve().relative_to(src)
            dest_fn = self.lib_dest / src_fn.name
            bf = BuildFile(
                file_type=FileType.lib,
                build_type=build_type,
                filename=self.lib_dest / src_fn.name,
                is_symlink=True,
                symlink_target=self.lib_dest / linked_file.name,
            )
            symlinks.append(bf)
            source_filenames.discard(src_fn)
            logger.debug(f'Found symlink {src_fn} -> {linked_file}')

        for src_fn in source_filenames:
            dest_fn = self.lib_dest / src_fn.name
            logger.debug(f'Copying {src_fn} -> {dest_fn}')
            shutil.copy2(src_fn, dest_fn)
            bf = BuildFile(
                file_type=FileType.lib,
                build_type=build_type,
                filename=dest_fn,
            )
            build_files.append(bf)

        for bf in symlinks:
            symlink_target = bf.symlink_target
            symlink_rel = symlink_target.relative_to(self.lib_dest)
            bf.symlink_target = symlink_rel
            logger.debug(f'Symlinking {bf.filename} to {symlink_target}')
            assert symlink_target.exists()
            if bf.filename.exists():
                bf.filename.unlink()
            bf.filename.symlink_to(symlink_rel)
            build_files.append(bf)

        return build_files
