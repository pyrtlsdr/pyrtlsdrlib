from __future__ import annotations
import typing as tp
import os
import enum
import shutil
import tempfile
import datetime
from pathlib import Path
import dataclasses

from loguru import logger

from pyrtlsdrlib import BuildType, FileType, BuildFile
import requests
import jsonfactory
from github import Github
import click

REPO_NAME = 'librtlsdr/librtlsdr'
ROOT_DIR = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT_DIR / 'build_assets'
PROJECT_LIB_DIR = ROOT_DIR / 'src' / 'pyrtlsdrlib' / 'lib'

BUILD_DEFAULT = BuildType.from_str('all_os|w32|w64|static')

DT_FMT = '%Y-%m-%dT%H:%M:%SZ'


def get_meta_filename(dir_or_filename: Path) -> Path:
    if dir_or_filename.is_dir():
        fn = dir_or_filename / 'build-meta.json'
    else:
        fn = dir_or_filename
    return fn

def read_build_meta(dir_or_filename: Path):
    fn = get_meta_filename(dir_or_filename)
    return jsonfactory.loads(fn.read_text())

def write_build_meta(dir_or_filename: Path, data):
    fn = get_meta_filename(dir_or_filename)
    fn.write_text(jsonfactory.dumps(data, indent=2))

def normalize_filenames(infiles: tp.Sequence[BuildFile]):
    for f in infiles:
        if f.filename.is_absolute():
            fn = f.filename.relative_to(ROOT_DIR)
            f.filename = fn


class ObjBase:
    def __init__(self, parent: 'ObjBase'|None = None, **kwargs):
        self.parent = parent
        self._metadata_matches = None
        self.children = []

    @property
    def metadata_matches(self) -> bool:
        r = self._metadata_matches
        if r is None:
            r = True
        child_matches = [c.metadata_matches for c in self.children]
        if len(child_matches):
            return r and all(child_matches)
        return r
    @metadata_matches.setter
    def metadata_matches(self, value: bool):
        self._metadata_matches = value

    def get_build_meta(self):
        p = self.parent
        if p is not None:
            data = p.get_build_meta()
        else:
            data = {}
        return data

    def _compare_build_meta(self, local_data, remote_data):
        p = self.parent
        if p is not None:
            r = p._compare_build_meta(local_data, remote_data)
        return 0

    def __repr__(self):
        return f'<{self.__class__.__name__}: "{self}">'

class Repository(ObjBase):
    def __init__(self, repo_name: str = REPO_NAME):
        self.repo_name = repo_name
        self._repo = None
        self._latest_release = None
        self._gh = None
        super().__init__()

    @property
    def gh(self) -> Github:
        g = self._gh
        if g is None:
            token = os.environ.get('GITHUB_API_TOKEN')
            g = self._gh = Github(token)
            del token
        return g

    @property
    def repo(self) -> 'github.Repository':
        r = self._repo
        if r is None:
            r = self._repo = self.gh.get_repo(self.repo_name)
        return r

    @property
    def latest_release(self) -> 'Release':
        r = self._latest_release
        if r is None:
            gh_rel = self.repo.get_latest_release()
            r = self._latest_release = Release(gh_rel, parent=self)
            self.children.append(r)
        return r

    def get_license(self, dest_dir: Path) -> Path:
        content = self.repo.get_license()
        p = dest_dir / content.name
        p.write_bytes(content.decoded_content)
        return p

    def __str__(self):
        return self.repo_name

class Release(ObjBase):
    def __init__(self, gh_rel: 'github.GitRelease', **kwargs):
        self.gh_rel = gh_rel
        self._assets = None
        super().__init__(**kwargs)

    @property
    def assets(self) -> tp.Dict[str, 'AssetBase']:
        a = self._assets
        if a is None:
            assets = [Asset(a, parent=self) for a in self.gh_rel.get_assets()]
            assets.append(SourceAsset(self.gh_rel.zipball_url, parent=self))
            self.children.extend(assets)
            a = self._assets = {a.name:a for a in assets}
        return a

    def get_build_meta(self):
        data = super().get_build_meta()
        data.update(dict(
            tag_name=self.gh_rel.tag_name,
            release_url=self.gh_rel.html_url,
            release_id=self.gh_rel.id,
            created=self.gh_rel.created_at,
            published=self.gh_rel.published_at,
        ))
        return data

    def _compare_build_meta(self, local_data, remote_data) -> int:
        match_keys = {'tag_name', 'release_url', 'release_id'}
        for key in match_keys.copy():
            if remote_data[key] == local_data.get(key):
                match_keys.discard(key)
        if not len(match_keys):
            self.metadata_matches = True
            return 0
        logger.debug(f'{match_keys=}')
        dt_keys = {'created', 'published'}
        dt_comps = []
        for key in dt_keys.copy():
            local_dt, remote_dt = local_data.get(key), remote_data[key]
            if local_dt is None:
                # dt_keys.discard(key)
                logger.debug(f'local_dt for {key} is None')
                continue
            if local_dt > remote_dt:
                r = -1
            elif local_dt < remote_dt:
                r = 1
            else:
                r = 0
            logger.debug(f'dt comp for {key} = {r}')
            dt_comps.append(r)
        if len(dt_comps):
            r = max(dt_comps)
            self.metadata_matches = r < 1
        self.metadata_matches = False
        return 1

    def __repr__(self):
        return f'<{self.__class__.__name__}: "{self}">'

    def __str__(self):
        return self.gh_rel.title

class AssetBase(ObjBase):
    build_files: tp.List[BuildFile]
    def __init__(self, *args, **kwargs):
        self._name = None
        self._type = None
        self.build_files = []
        self.files_updated = False
        super().__init__(**kwargs)

    @property
    def name(self) -> str:
        n = self._name
        if n is None:
            n = self._name = self._get_name()
        return n

    @property
    def type(self) -> BuildType:
        t = self._type
        if t is None:
            t = self._type = self._get_type()
        return t

    @property
    def download_url(self) -> str:
        return self._get_download_url()

    @property
    def download_filename(self) -> str:
        return self.download_url.split('/')[-1]

    def _get_name(self) -> str:
        raise NotImplementedError

    def _get_type(self) -> BuildType:
        raise NotImplementedError

    def _get_download_url(self) -> str:
        raise NotImplementedError

    def needs_update(self, dest_dir: Path) -> bool:
        local_data = self.read_metadata(dest_dir)
        if local_data is None:
            return True
        remote_data = self.get_build_meta()
        cmp = self._compare_build_meta(local_data, remote_data)
        return cmp == 1

    def get_build_meta(self):
        data = super().get_build_meta()
        data.update(dict(
            asset_type=self.type,
            asset_name=self.name,
            asset_url=self.download_url,
            metadata_matches=self.metadata_matches,
            files_updated=self.files_updated,
            build_files=self.build_files,
        ))
        return data

    def _compare_build_meta(self, local_data, remote_data) -> int:
        parent_r = super()._compare_build_meta(local_data, remote_data)
        r = 0
        for key in ['asset_type', 'asset_name', 'asset_url']:
            lval, rval = local_data.get(key), remote_data[key]
            if lval != rval:
                logger.debug(f'{key=}, {lval=}, {rval=}')
                r = 1
                break
        r = max(r, parent_r)
        self.metadata_matches = r < 1
        return r

    def get_dest_dirname(self) -> str:
        if self.type & 'ubuntu|macos':
            return self.type.name
        elif self.type & 'windows':
            suffixes = ['w32', 'w64', 'dlldep', 'static', 'udpsrv']
            dirname = ['windows']
            for suffix in suffixes:
                if self.type & suffix:
                    dirname.append(suffix)
            return '_'.join(dirname)
        elif self.type & 'source':
            return 'source'
        raise ValueError('Could not determine dest_dirname')

    def download_to(self, dest_dir: Path) -> Path:
        dest_filename = dest_dir / self.download_filename
        url = self.download_url
        logger.info(f'Downloading file to {dest_filename}, ({url=})')
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with dest_filename.open('wb') as fd:
            for chunk in r.iter_content(chunk_size=128):
                fd.write(chunk)
        logger.success(f'Download complete: {dest_filename}')
        return dest_filename

    def extract_to(self, dest_root: Path) -> tp.List[BuildFile]:
        dest_dir = dest_root / self.get_dest_dirname()
        dest_dir.mkdir(exist_ok=True)
        logger.info(f'{self!r} extracting to: {dest_dir}')
        lib_dir = dest_dir / 'lib'
        bin_dir = dest_dir / 'bin'
        for p in [lib_dir, bin_dir]:
            if p.exists():
                logger.info(f'{p.name} directory exists. Removing')
                assert p.is_dir()
                shutil.rmtree(p)
            p.mkdir()
        dest_map = {FileType.lib:lib_dir, FileType.bin:bin_dir}

        results = self.build_files = []

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            extract_dir = tmpdir / 'expanded'
            extract_dir.mkdir()
            archive_file = self.download_to(tmpdir)
            logger.info(f'Extracting archive "{archive_file}" to {extract_dir}')
            shutil.unpack_archive(archive_file, extract_dir)
            tar_files = [f for f in extract_dir.glob('*.tar.gz')]
            if len(tar_files):
                assert len(tar_files) == 1
                tf = tar_files[0]
                new_tf = tmpdir / tf.name
                logger.debug(f'Moving archive {tf} to {new_tf}')
                tf = tf.rename(new_tf)
                logger.debug(f'Extracting packed archive {tf}')
                shutil.unpack_archive(tf, extract_dir)
            logger.success(f'Archive extracted: {extract_dir}')

            # find symlinks first to rebuild them later
            symlinks = []
            for filename in extract_dir.iterdir():
                if not filename.is_symlink():
                    continue
                ftype = self._get_filetype(filename)
                fdest_dir = dest_map.get(ftype)
                if fdest_dir is None:
                    continue
                linked_file = filename.resolve().relative_to(extract_dir)
                filename = fdest_dir / filename.name
                build_file = BuildFile(
                    build_type=self.type,
                    file_type=ftype,
                    filename=filename,
                    is_symlink=True,
                    symlink_target=linked_file,
                )
                symlinks.append(build_file)
                logger.debug(f'found symlink: {build_file}')

            # move files to `bin/` or `lib/`
            for filename in extract_dir.iterdir():
                logger.debug(f'Processing file: {filename}')
                if filename.is_symlink():
                    continue
                assert filename.is_file()
                ftype = self._get_filetype(filename)
                logger.debug(f'{ftype=}, {filename.name=}')
                fdest_dir = dest_map.get(ftype)
                if fdest_dir is None:
                    continue
                logger.info(f'Adding {filename.name} to {fdest_dir}')
                filename = filename.rename(fdest_dir / filename.name)
                build_file = BuildFile(build_type=self.type, file_type=ftype, filename=filename)
                results.append(build_file)

            # rebuild any symlinks found earlier
            for build_file in symlinks:
                fn = build_file.filename.name
                sym_fn = build_file.symlink_target.name
                fdest_dir = build_file.filename.parent

                symlink_target = fdest_dir / sym_fn
                symlink_rel = symlink_target.relative_to(fdest_dir)
                build_file.symlink_target = symlink_rel

                logger.debug(f'Processing symlink: {build_file}')
                assert symlink_target.exists()
                build_file.filename.symlink_to(symlink_rel)
                results.append(build_file)

        normalize_filenames(results)

        logger.debug('Writing build metadata')
        self.files_updated = True
        self.write_metadata(dest_dir)

        logger.success(f'{self!r} extraction complete')
        return results

    def read_metadata(self, dest_dir: Path, deserialize: bool = True):
        if dest_dir.name != self.get_dest_dirname():
            dest_dir = dest_dir / self.get_dest_dirname()
        try:
            data = read_build_meta(dest_dir)
        except FileNotFoundError:
            logger.debug('No metadata file')
            return None
        return data

    def write_metadata(self, dest_dir: Path):
        if dest_dir.name != self.get_dest_dirname():
            dest_dir = dest_dir / self.get_dest_dirname()
        data = self.get_build_meta()
        write_build_meta(dest_dir, data)

    def update_metadata(self, dest_dir: Path):
        if dest_dir.name != self.get_dest_dirname():
            dest_dir = dest_dir / self.get_dest_dirname()
        data = self.read_metadata(dest_dir, deserialize=False)
        data.update(dict(
            files_updated=self.files_updated,
            metadata_matches=self.metadata_matches,
        ))
        write_build_meta(dest_dir, data)
        return data

    def _get_filetype(self, filename: Path) -> FileType:
        if self.type & 'windows':
            suffixes = [s.lower() for s in filename.suffixes]
            if '.exe' in suffixes:
                return FileType.bin
            elif '.dll' in suffixes:
                return FileType.lib
        elif self.type & 'macos|ubuntu':
            if filename.name.startswith('lib'):
                return FileType.lib
            elif filename.name.startswith('rtl_'):
                return FileType.bin
        return FileType.other

    def __repr__(self):
        return f'<{self.__class__.__name__}: "{self}">'

    def __str__(self):
        return self.name


class Asset(AssetBase):
    def __init__(self, gh_asset: 'github.GitReleaseAsset', **kwargs):
        self.gh_asset = gh_asset
        super().__init__(**kwargs)

    def _get_name(self) -> str:
        return self.gh_asset.name

    def _get_type(self) -> BuildType:
        name = self.name
        os_names = ['macos', 'ubuntu']

        for os_name in os_names:
            if os_name in name:
                return BuildType.from_str(os_name)
        tp_val = BuildType.unknown
        suffixes = ['w32', 'w64', 'dlldep', 'static', 'udpsrv']
        for suffix in suffixes:
            if suffix in name:
                tp_val |= suffix
        assert tp_val != BuildType.unknown
        tp_val |= 'windows'
        tp_val ^= 'unknown'
        return tp_val

    def _get_download_url(self) -> str:
        return self.gh_asset.browser_download_url

class SourceAsset(AssetBase):
    def __init__(self, src_url: str, **kwargs):
        self.src_url = src_url
        super().__init__(**kwargs)

    def _get_name(self) -> str:
        return 'Source'

    def _get_type(self) -> BuildType:
        return BuildType.source

    def _get_download_url(self) -> str:
        return self.src_url

@logger.catch
def extract(
    dest_dir: Path = BUILD_DIR,
    repo_name: str = REPO_NAME,
    asset_types: BuildType = BUILD_DEFAULT,
) -> tp.Dict[str, tp.Dict[tp.Any]]:

    repo = Repository(repo_name)

    results = {}
    files_changed = []

    changed = False

    for asset in repo.latest_release.assets.values():
        if not asset_types.contains(asset.type):
            logger.info(f'Skipping asset: {asset}')
            continue
        if not asset.needs_update(dest_dir):
            logger.info(f'No update needed for "{asset!r}"')
            assert asset.metadata_matches
            meta = asset.update_metadata(dest_dir)
            results[asset.name] = meta
            continue
        files = asset.extract_to(dest_dir)
        if len(files):
            changed = True
            files_changed.extend(files)
            meta = asset.get_build_meta()
        else:
            assert asset.metadata_matches
            meta = asset.update_metadata(dest_dir)
        results[asset.name] = meta

    write_build_meta(dest_dir, results)

    return results

def copy_builds_to_project(build_dir: Path = BUILD_DIR, dest_dir: Path = PROJECT_LIB_DIR):
    build_meta = read_build_meta(build_dir)
    try:
        project_meta = read_build_meta(dest_dir)
    except FileNotFoundError:
        project_meta = {}

    updates_needed = {}

    logger.info('Checking for project file updates...')
    for asset_name, asset_data in build_meta.items():
        if asset_name not in project_meta:
            updates_needed[asset_name] = asset_data['build_files'].copy()
            continue
        build_files = asset_data['build_files']
        normalize_filenames(build_files)
        build_files = {f.filename: f for f in build_files}
        _updates = []
        proj_asset = project_meta[asset_name]
        for data in proj_asset.values():
            needs_update = False
            if not data['proj_file'].exists():
                needs_update = True
            elif data['tag_name'] != asset_data['tag_name']:
                needs_update = True
            if needs_update:
                bf = build_files[data['build_file'].filename]
                _updates.append(bf)
        if len(_updates):
            updates_needed[asset_name] = _updates

    meta_updates = {}

    num_updates = 0
    for asset_name, build_files in updates_needed.items():
        logger.info(f'Updating files for "{asset_name}"')
        asset_data = build_meta[asset_name]
        _updates = {}
        symlinks = []
        for f in build_files:
            if f.file_type != FileType.lib:
                continue
            if f.build_type & 'macos':
                if f.filename.suffix != '.dylib':
                    continue
                dest_fn = f.filename.name
            elif f.build_type & 'ubuntu':
                if '.so' not in f.filename.suffixes:
                    continue
                dest_fn = f.filename.name
            elif f.build_type & 'windows':
                dest_fn = [f.filename.stem]
                for suffix in ['w32', 'w64', 'static', 'dlldep', 'udpsrv']:
                    if f.build_type & suffix:
                        dest_fn.append(suffix)
                dest_fn = '_'.join(dest_fn)
                dest_fn = f'{dest_fn}{f.filename.suffix}'
            dest_fn = dest_dir / dest_fn
            if f.filename.is_symlink():
                symlinks.append((f, dest_fn))
                continue
            logger.debug(f'copying {f.filename} to {dest_fn}')
            shutil.copy2(f.filename, dest_fn)
            _updates[str(dest_fn)] = dict(
                tag_name=asset_data['tag_name'],
                build_file=f,
                proj_file=dest_fn,
            )

        for f, dest_fn in symlinks:
            sym_fn = f.symlink_target.name
            symlink_target = dest_dir / sym_fn
            symlink_rel = symlink_target.relative_to(dest_dir)
            logger.debug(f'Symlinking {dest_fn} -> {symlink_target}')
            assert symlink_target.exists()
            if dest_fn.exists():
                dest_fn.unlink()
            dest_fn.symlink_to(symlink_rel)
            assert dest_fn.resolve() == symlink_target != dest_fn
            _updates[str(dest_fn)] = dict(
                tag_name=asset_data['tag_name'],
                build_file=f,
                proj_file=dest_fn,
            )
        _num_updates = len(_updates)
        if _num_updates:
            meta_updates[asset_name] = _updates
            logger.success(f'Updated {_num_updates} files for "{asset_name}"')
        num_updates += _num_updates

    if len(meta_updates):
        logger.debug(f'Updating project_meta')
        for asset_name, updates in meta_updates.items():
            existing = project_meta.setdefault(asset_name, {})
            existing.update(updates)
        write_build_meta(dest_dir, project_meta)
        logger.success(f'Updated {num_updates} total project files')
    else:
        logger.info('Project files up to date')

@jsonfactory.register
class JSONEncoder:
    classes: tp.Tuple[type] = (datetime.datetime, Path, BuildType, FileType, BuildFile)
    @classmethod
    def cls_to_str(cls, obj):
        is_enum_cls = isinstance(obj, enum.EnumMeta)
        is_enum_obj = isinstance(obj, enum.Enum)
        if is_enum_obj:
            the_class = obj.__class__
        elif is_enum_cls:
            the_class = obj
        elif type(obj) is not type:
            the_class = obj.__class__
        else:
            the_class = obj
        if Path in the_class.mro() and the_class is not Path:
            the_class = Path
        return '.'.join([the_class.__module__, the_class.__name__])
    @classmethod
    def str_to_cls(cls, s):
        for the_class in cls.classes:
            if cls.cls_to_str(the_class) == s:
                return the_class
    def encode(self, o):
        if isinstance(o, enum.Enum):
            d = {'__class__':self.cls_to_str(o)}
            d['value'] = o.to_str()
        elif isinstance(o, BuildFile):
            d = {'__class__':self.cls_to_str(o)}
            d.update(dataclasses.asdict(o))
        elif isinstance(o, Path):
            d = {'__class__':self.cls_to_str(o)}
            d['value'] = str(o)
        elif isinstance(o, datetime.datetime):
            d = {'__class__':self.cls_to_str(o)}
            d['value'] = o.strftime(DT_FMT)
        else:
            return
        return d
    def decode(self, d):
        if '__class__' not in d:
            return d
        cls = self.str_to_cls(d['__class__'])
        if cls is None:
            raise Exception(str(d))
        if isinstance(cls, enum.EnumMeta):
            return cls.from_str(d['value'])
        elif cls is BuildFile:
            del d['__class__']
            for key in d:
                val = d[key]
                if isinstance(val, dict) and '__class__' in val:
                    if 'value' in val:
                        d[key] = val['value']
                    else:
                        val.pop('__class__')
                        d[key] = val
            return cls._deserialize(d)
        elif cls is Path:
            return Path(d['value'])
        elif cls is datetime.datetime:
            return datetime.datetime.strptime(d['value'], DT_FMT)
        return d

@click.command()
@click.option('--build-dir', type=click.Path(file_okay=False), default=BUILD_DIR)
@click.option('--project-lib-dir', type=click.Path(file_okay=False), default=PROJECT_LIB_DIR)
@click.option('--repo-name', default=REPO_NAME)
@click.option(
    '--build-types',
    type=click.Choice([m.name for m in BuildType.iter_members()]),
    multiple=True,
    default=BUILD_DEFAULT.to_str().split('|'),
)
def main(build_dir, project_lib_dir, repo_name, build_types):
    build_types = BuildType.from_str('|'.join(build_types))
    extract(dest_dir=build_dir, repo_name=repo_name, asset_types=build_types)
    copy_builds_to_project(build_dir=build_dir, dest_dir=project_lib_dir)
    repo = Repository(repo_name)
    repo.get_license(project_lib_dir)


if __name__ == '__main__':
    main()
