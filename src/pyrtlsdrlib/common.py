from __future__ import annotations
import sys
import typing as tp
import enum
import dataclasses
from dataclasses import dataclass
from pathlib import Path
from pkg_resources import resource_filename

__all__ = ('BuildType', 'FileType', 'BuildFile')

def get_lib_root() -> Path:
    modname = '.'.join(__name__.split('.')[:-1])
    # modname = __name__.split('.')[-1]
    # modname = f'{modname}.lib'
    return Path(resource_filename(modname, 'lib'))

# class FlagMixin:
#     @classmethod
#     def iter_members(cls) -> tp.Iterable[BuildType]:
#         yield from cls
#         # for atype in cls:
#         #     if atype == cls.all_os or atype == cls.unknown:
#         #         continue
#         #     yield atype

#     @classmethod
#     def from_str(cls, s: str):
#         if '|' in s:
#             result = None
#             for name in s.split('|'):
#                 item = cls.from_str(name)
#                 if result is None:
#                     result = item
#                 else:
#                     result |= item
#             if result is None:
#                 raise ValueError('Invalid string parameters')
#             return result
#         return getattr(cls, s.lower())

#     def to_str(self) -> str:
#         if self.name is None:
#             return '|'.join((obj.name for obj in self))
#         return self.name

#     def __iter__(self) -> tp.Iterable[BuildType]:
#         for atype in self.iter_members():
#             if atype & self == atype:
#                 yield atype

#     def __len__(self):
#         return len([v for v in self])

#     def __or__(self, other: BuildType|str):
#         if isinstance(other, str):
#             other = self.from_str(other)
#         return super().__or__(other)

#     def __and__(self, other: BuildType|str):
#         if isinstance(other, str):
#             other = self.from_str(other)
#         return super().__and__(other)

#     def __xor__(self, other: BuildType|str):
#         if isinstance(other, str):
#             other = self.from_str(other)
#         return super().__xor__(other)


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

    x86_x64 = enum.auto()
    i686 = enum.auto()
    aarch64 = enum.auto()
    arm64 = enum.auto()
    universal2 = enum.auto()

    all_os = macos | windows | ubuntu
    all_archs = w32 | w64 | x86_x64 | i686 | aarch64 | arm64 | universal2

    @classmethod
    def iter_members(cls) -> tp.Iterable[BuildType]:
        for atype in cls:
            if atype == cls.all_os or atype == cls.unknown:
                continue
            yield atype

    @classmethod
    def from_str(cls, s: str) -> BuildType:
        # return super().from_str(s)
        if '|' in s:
            result = BuildType.unknown
            for name in s.split('|'):
                result |= BuildType.from_str(name)
            if result != BuildType.unknown:
                result ^= BuildType.unknown
            return result
        return getattr(BuildType, s.lower())

    def filter_options(self) -> BuildType:
        to_exclude = self.from_str('all_os|source|all_archs')
        return self & ~to_exclude

    def filter_archs(self) -> BuildType:
        return self & BuildType.all_archs

    def filter_os(self) -> BuildType:
        return self & BuildType.all_os

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
            if atype & self == atype:
                yield atype

    def __len__(self):
        return len([v for v in self])

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

    @classmethod
    def from_str(cls, s: str) -> FileType:
        return getattr(FileType, s.lower())
        # return super().from_str(s)

    def to_str(self) -> str:
        return self.name

@dataclass
class BuildFile:
    build_type: BuildType
    file_type: FileType
    filename: Path
    is_symlink: bool = False
    # relative_to: Path|None = None
    symlink_target: Path|None = None
    # package_name: str|None = None
    _field_map: tp.ClassVar[tp.Dict[str, type]]|None = None

    # def package_name_from_filename(self, filename: Path|None = None) -> str:
    #     if filename is None:
    #         filename = self.filename
    #     lib_root = get_lib_root()
    #     if filename.is_absolute():
    #         filename = filename.relative_to(lib_root)
    #     return '.'.join(filename.parts[:-1])

    # def filename_from_package_name(
    #     self,
    #     package_name: str|None = None,
    #     relative: bool = False,
    # ) -> Path:
    #     if package_name is None:
    #         package_name = self.package_name
    #     # lib_root = get_lib_root()
    #     # modname = '.'.join(__name__.split('.')[:-1])
    #     # modname = f'{modname}.lib'
    #     # if '.' in package_name:
    #     #     modname = f'{modname}.{package_name}'
    #     #     package_name = ''
    #     if '.' in package_name:
    #         resource_name = package_name.split('.')[-1]
    #         package_name = '.'.join(package_name.split('.')[:-1])
    #     else:
    #         resource_name = ''
    #     p = Path(resource_filename(package_name, resource_name))
    #     if relative:
    #         p = p.relative_to(get_lib_root())
    #     return p

    # def make_filename_relative(self):
    #     if self.package_name is None:
    #         self.package_name = self.package_name_from_filename()
    #     filename = self.filename_from_package_name(relative=True)
    #     self.filename = filename

    # @property
    # def filename_abs(self) -> Path:
    #     relative_to = self.relative_to
    #     if relative_to is None:
    #         return self.filename.resolve()
    #     # else:
    #     #     assert self.relative_to is not None
    #     #     assert not self.filename.is_absolute()
    #     #     return self.relative_to / self.filename
    #     if not relative_to.is_absolute():
    #         relative_to = relative_to.resolve()
    #     if self.filename.is_absolute():
    #         return self.filename.relative_to(relative_to).resolve()
    #     else:
    #         return relative_to / self.filename
    # @filename_abs.setter
    # def filename_abs(self, value: Path):
    #     if self.relative_to is None:
    #         assert value.is_absolute()
    #         self.filename = value
    #     else:
    #         relative_to = self.relative_to
    #         if not relative_to.is_absolute():
    #             relative_to = relative_to.resolve()
    #         self.filename = value.relative_to(relative_to)

    #     # assert self.relative_to is not None
    #     # assert value.is_absolute()
    #     # self.filename = value.relative_to(self.relative_to)

    # def set_relative_to(self, relative_to: Path):
    #     # assert self.filename.is_absolute()
    #     if self.filename.is_absolute():
    #         fn = self.filename_abs.relative_to(relative_to.resolve())
    #         self.filename = fn
    #         self.relative_to = relative_to
    #         # if relative_to.is_absolute():
    #         #     fn = self.filename_abs.relative_to(relative_to)
    #         # else:
    #         #     # fn = relative_to / self.filename_abs
    #         #     fn = self.filename_abs.relative_to(relative_to.resolve())
    #     else:
    #         fn = self.filename_abs.relative_to(relative_to.resolve())
    #         self.relative_to = relative_to
    #         # self.filename_abs = relative_to / self.filename

    #         # fn = relative_to / self.filename
    #     # self.filename = fn
    #     # self.relative_to = relative_to

    # def normalize_filename(self):
    #     if self.relative_to is None:
    #         return
    #     if self.filename.is_absolute():
    #         self.relative_to = None
    #         self.set_relative_to(self.relative_to)
    #         # fn = self.filename.relative_to(self.relative_to)
    #         # self.filename = fn

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


# @dataclass
# class BuildMeta:
#     build_type: BuildType
#     build_dir: Path
#     build_files: dict[str, BuildFile]|None = dataclasses.field(default_factory=dict)
#     child_metas: dict[str, BuildMeta]|None = dataclasses.field(default_factory=dict)
#     parent: BuildMeta|None = None
#     meta_filename: Path|None = None
#     def __post_init__(self, **kwargs):
#         if self.meta_filename is None:
#             self.meta_filename = self.build_dir / 'build.json'

#     def add_file(self, build_file: BuildFile):
#         if not build_file.build_type & self.build_type:
#             raise ValueError(f'Incompatible build types: {build_file.build_type}, {self.build_type}')
#         rel_fn = self._get_build_file_rel(build_file)
#         key = str(rel_fn)
#         if key in self.build_files:
#             raise KeyError(f'{key} already exists')
#         self.build_files[key] = build_file
#         build_file.filename = rel_fn

#     def add_child(self, child: BuildMeta):
#         rel_fn = self._get_child_rel(child)
#         key = str(rel_fn)
#         if key in self.child_metas:
#             raise KeyError(f'{key} already exists')
#         self.child_metas[key] = child
#         child.parent = self
#         child.build_dir = rel_fn
#         child.meta_filename = child.meta_filename.relative_to(self.build_dir)

#     def iter_files(
#         self,
#         file_type: FileType|str = 'bin|lib|other',
#         build_type: BuildType|str|None = None,
#         recursive: bool = True,
#     ) -> tp.Iterable[BuildFile]:
#         if isinstance(file_type, str):
#             file_type = FileType.from_str(file_type)
#         if isinstance(build_type, str):
#             build_type = BuildType.from_str(build_type)
#         for build_file in self.build_files.values():
#             if not build_file.file_type & file_type:
#                 continue
#             if build_type is not None:
#                 if not build_type.build_type & build_type:
#                     continue
#             yield build_file
#         if recursive:
#             for child in self.iter_children(file_type, build_type, True):
#                 yield from child.iter_files(file_type, build_type, False)

#     def iter_children(
#         self,
#         file_type: FileType|str = 'bin|lib|other',
#         build_type: BuildType|str|None = None,
#         recursive: bool = True
#     ) -> tp.Iterable[BuildMeta]:
#         if isinstance(file_type, str):
#             file_type = FileType.from_str(file_type)
#         if isinstance(build_type, str):
#             build_type = BuildType.from_str(build_type)
#         for child in self.child_metas.values():
#             if not child.file_type & file_type:
#                 continue
#             if build_type is not None:
#                 if not child.build_type & build_type:
#                     continue
#             yield child
#             if recursive:
#                 yield from child.iter_children(file_type, build_type, True)

#     def _get_build_file_rel(self, build_file: BuildFile) -> Path:
#         fn = abs_fn = build_file.filename
#         if not fn.is_absolute():
#             abs_fn = self.build_dir / fn
#         rel_fn = abs_fn.relative_to(self.build_dir)
#         return rel_fn

#     def _get_child_rel(self, child: BuildMeta) -> Path:
#         fn = abs_fn = child.build_dir
#         if not fn.is_absolute():
#             abs_fn = self.build_dir / fn
#         rel_fn = abs_fn.relative_to(self.build_dir)
#         return rel_fn

#     def _check_build_files(self):
#         for key, build_file in self.build_files.items():
#             if not build_file.build_type & self.build_type:
#                 raise ValueError(f'Incompatible build types: {build_file.build_type}, {self.build_type}')
#             rel_fn = self._get_build_file_rel(build_file)
#             if build_file.filename != rel_fn:
#                 raise ValueError(f'BuildFile filename error: {build_file.filename} != {rel_fn}')
#             if key != str(rel_fn):
#                 raise KeyError(f'BuildFile key error: {build_file.filename} != {key}')

#     def _check_children(self):
#         for key, child in self.child_metas.items():
#             rel_fn = self._get_build_file_rel(child)
#             if child.build_dir != rel_fn:
#                 raise ValueError(f'Child filename error: {child.build_dir} != {rel_fn}')
#             if key != str(rel_fn):
#                 raise KeyError(f'BuildFile key error: {child.build_dir} != {key}')

#     @classmethod
#     def _deserialize(cls, data: tp.Dict[str, tp.Any]) -> 'BuildMeta':
#         kw = dict(
#             build_type=Path(data['build_type']),
#             build_dir=Path(data['build_dir']),
#             build_files={k:BuildFile._deserialize(v) for k,v in data['build_files'].items()},
#             meta_filename=Path(data['meta_filename']),
#             child_metas={},
#         )

#         obj = cls(**kw)
#         for child_key, child_data in data['child_metas'].items():
#             child = cls._deserialize(child_data)
#             obj.add_child(child)
#         # obj._check_build_files()
#         return obj

#     def _serialize(self) -> tp.Dict[str, Any]:
#         self._check_build_files()
#         self._check_children()
#         # d = dataclasses.asdict(self)
#         d = dict(
#             build_type=self.build_type.to_str(),
#             build_dir=str(self.build_dir),
#             meta_filename=str(self.meta_filename),
#             build_files={k:v._serialize() for k,v in self.build_files.items()},
#             child_metas={k:v._serialize() for k,v in self.child_metas.items()},
#         )
#         # d['build_files'] = {k:v._serialize() for k,v in self.build_files.items()}
#         return d
