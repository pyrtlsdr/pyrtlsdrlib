from __future__ import annotations
import sys
import typing as tp
import enum
import dataclasses
from dataclasses import dataclass
from pathlib import Path

__all__ = ('BuildType', 'FileType', 'BuildFile')

class BuildType(enum.Flag):
    unknown = enum.auto()
    macos = enum.auto()
    windows = enum.auto()
    ubuntu = enum.auto()
    source = enum.auto()

    w32 = enum.auto()
    w64 = enum.auto()
    dlldep = enum.auto()
    static = enum.auto()
    udpsrv = enum.auto()

    all_os = macos | windows | ubuntu

    @classmethod
    def iter_members(cls) -> tp.Iterator[BuildType]:
        for atype in cls:
            if atype == cls.all_os or atype == cls.unknown:
                continue
            yield atype

    @staticmethod
    def from_str(s: str) -> BuildType:
        if '|' in s:
            result = BuildType.unknown
            for name in s.split('|'):
                result |= BuildType.from_str(name)
            if result != BuildType.unknown:
                result ^= BuildType.unknown
            return result
        return getattr(BuildType, s.lower())

    def filter_options(self) -> BuildType:
        to_exclude = self.from_str('all_os|source')
        return self ^ to_exclude

    def contains(self, other: BuildType|str) -> bool:
        if isinstance(other, str):
            other = BuildType.from_str(other)
        if self & 'windows' and other & 'windows':
            arch_types = self & 'w32|w64'
            if not other & arch_types:
                return False
            lib_types = self & 'dlldep|static'
            if not other & lib_types:
                return False
            if self & 'udpsrv' != other & 'udpsrv':
                return False
            return True
        return bool(self & other)

    def to_str(self) -> str:
        if self.name is None:
            return '|'.join((obj.name for obj in self))
        return self.name

    def __iter__(self) -> tp.Iterator[BuildType]:
        for atype in self.iter_members():
            if atype & self:
                yield atype

    def __or__(self, other: BuildType|str):
        if isinstance(other, str):
            other = self.from_str(other)
        return super().__or__(other)

    def __and__(self, other: BuildType|str):
        if isinstance(other, str):
            other = self.from_str(other)
        return super().__and__(other)

    def __xor__(self, other: BuildType|str):
        if isinstance(other, str):
            other = self.from_str(other)
        return super().__xor__(other)


class FileType(enum.Enum):
    bin = enum.auto()
    lib = enum.auto()
    other = enum.auto()

    @staticmethod
    def from_str(s: str) -> FileType:
        return getattr(FileType, s.lower())

    def to_str(self) -> str:
        return self.name

@dataclass
class BuildFile:
    build_type: BuildType
    file_type: FileType
    filename: Path
    is_symlink: bool = False
    symlink_target: Path|None = None

    _field_map: tp.ClassVar[tp.Dict[str, type]]|None = None

    @classmethod
    def _get_field_map(cls) -> tp.Dict[str, type]:
        fields = cls._field_map
        if fields is None:
            fields = {}
            for field in dataclasses.fields(cls):
                ftype = field.type
                if isinstance(ftype, str):
                    if '|' in ftype:
                        ftypes = set([t.strip(' ') for t in ftype.split('|')])
                        ftypes.discard('None')
                        assert len(ftypes) == 1
                        ftype = ftypes.pop()

                    if '.' in ftype:
                        modname = '.'.join(ftype.split('.')[:-1])
                        objname = ftype.split('.')[-1]
                    else:
                        objname = ftype
                        b = __builtins__
                        if not isinstance(b, dict):
                            b = b.__dict__
                        if objname in b:
                            modname = 'builtins'
                        else:
                            modname = cls.__module__
                    m = sys.modules[modname]
                    ftype = getattr(m, objname)
                fields[field.name] = ftype
            cls._field_map = fields
        return fields

    @classmethod
    def _deserialize(cls, data: tp.Dict[str, tp.Any]) -> BuildFile:
        kw = {}
        for fname, ftype in cls._get_field_map().items():
            val = data.get(fname)
            if val is None:
                continue
            if isinstance(ftype, enum.EnumMeta) and not isinstance(val, enum.Enum):
                val = ftype.from_str(val)
            elif ftype is Path and not isinstance(val, Path):
                assert isinstance(val, str)
                val = Path(val)
            kw[fname] = val

        obj = cls(**kw)
        if obj.symlink_target is not None:
            sym_fn = obj.symlink_target.name
            sym_dir = obj.filename.parent
            obj.symlink_target = sym_dir / sym_fn
        return obj

    def _serialize(self) -> tp.Dict[str, tp.Any]:
        d = dataclasses.asdict(self)
        for key in d:
            val = d[key]
            if isinstance(val, (BuildType, FileType)):
                val = val.to_str()
            elif isinstance(val, Path):
                val = str(val)
            else:
                continue
            d[key] = val
        return d
