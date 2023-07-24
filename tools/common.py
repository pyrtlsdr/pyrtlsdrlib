from __future__ import annotations
import typing as tp
from pathlib import Path
import enum
import datetime
import dataclasses

import jsonfactory

from pyrtlsdrlib import BuildType, FileType, BuildFile
from pyrtlsdrlib.lib import resource_filename

__all__ = (
    'REPO_NAME', 'ROOT_DIR', 'BUILD_DIR', 'PROJECT_LIB_DIR', 'CUSTOM_LIB_DIR',
    'BUILD_DEFAULT', 'DT_FMT', 'get_meta_filename', 'read_build_meta', 'write_build_meta',
    'update_build_meta',
)

REPO_NAME = 'librtlsdr/librtlsdr'
ROOT_DIR = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT_DIR / 'build_assets'
PROJECT_LIB_DIR = Path(resource_filename('pyrtlsdrlib.lib', ''))
CUSTOM_LIB_DIR = Path(resource_filename('pyrtlsdrlib.lib.custom_build', ''))

BUILD_DEFAULT = BuildType.from_str('all_os|w32|w64|x86_x64|static')

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

def write_build_meta(dir_or_filename: Path, data: dict, overwrite: bool = True):
    if not overwrite:
        update_build_meta(dir_or_filename, data)
        return
    fn = get_meta_filename(dir_or_filename)
    fn.write_text(jsonfactory.dumps(data, indent=2))

def update_build_meta(dir_or_filename: Path, data):
    fn = get_meta_filename(dir_or_filename)
    if fn.exists():
        existing_data = jsonfactory.loads(fn.read_text())
    else:
        existing_data = {}
    existing_data.update(data)
    fn.write_text(jsonfactory.dumps(existing_data, indent=2))

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
