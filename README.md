# pathlib_, a reimplementation of the python standard library's pathlib

## Rationale

The main reason to attempt such work is because of the deep-rooted limitations found in the standard library's pathlib and also to improve the OOP focus of the library. The limitations identified so far:
1. The upstream module relies heavily on the `posixpath` and `ntpath` modules, which are very low level and work with strings (and bytes). That leaked into the classes and it looks like strings are the basis of paths there. This module takes a different approach and assumes that a path is a sequence of components (strings) separated by a "separator".
2. The official module uses `slots`, apparently to improve the performance. Here we use lazy computation which should help with the processing requirements and simplified path versions which should improve the memory footprint.
3. There are only two possible paths formats in this world, you're POSIX or Windows, period. This assumption is deeply rooted in the code, almost impossible to work around.
4. Even if you were to work with the previous constraint and try to make a "POSIX-like flavour" (or a Windows-like one) your implementation would be a new module with functions and variables/constants, like the `posixpath` or `ntpath` modules, no inheriting and overriding or re-implementing (the OOP way).

Which such limitations in mind, this implementation follows a different path :P
- Paths are immutable sequences, `BasePurePath`, which are based on a `tuple`, and which is the root of the inheritance tree.
- Paths components are separated by a "separator" that your child class can/should/must override (defaults to `/`)
- The complex part of parsing a path is the "prefix" part, what is called "anchor" (the "drive" and/or "root"). Such analysis should be implemented by the child class via the `_parse_path` method, which should take a string as argument and return a tuple of `("drive", "root", [parts])`
- Anything that can't be generalized to all paths is not implemented on the base class and should come from the children, like `as_posix` (questionable method, but kept for complete compatibility), or `as_uri` (different systems prefer different `file://` URIs).
- Some other methods can be overridden as needed based on specifics, but their default implementation usually cover the generally accepted conventions (like `_parse_name`)

### Commonalities

One of the project goals it to keep compatibility with the upstream module which means that if is not advertised as a difference then every upstream feature should be available here. This will be true about the public interface and not about the implementation details. The major point about this relates to the classes structure.

In general, it should be used just like `pathlib`:
```
from pathlib_ import Path, PurePath

a = PurePath('/some/theoretical/path')
b = Path() / 'my_dir'
```

### Classes

This module keeps the Pure vs "Impure" (concrete?) distinction, effectively revolving around I/O access: pure methods don't generate actual I/O to the file system, they can be described as "conceptual paths". The base classes are `BasePurePath` and `BasePath` which are not part of the upstream public interface but they're used here to actually describe it (most of their methods are abstract). The `BasePath` and its children are effectively mixins and can't be instantiated directly; they should be used together with `BasePurePath` or one of its children to create an actual `Path`.

With `BasePurePath` and `BasePath` describing the public interface, the process of "creating a new file structure" would start by creating a children of each and customizing them appropriately (should at least implement the missing methods, critically the `BasePurePath._parse_path` one). You concrete (impure) custom class inheritance should look like
```
MyPurePath(BasePurePath):
    def _parse_name(self, path_instance):
        ...
        # return '', '', [] # empty ("current") path
    
MyPath(BasePath, MyPurePath):
    ...
```

Alternatively there are the `BaseOSPurePath` and `BaseOSPath` that reduce the original abstraction into the POSIX vs Windows world. They include implementations for functionalities that are common to these systems. Then they're further refined by `PurePosixPath` & `PosixPath` and `PureWindowsPath` & `WindowsPath`. There are also the "convenient factories" that will instantiate the "right" class based on the value of `os.name`. With a value of `nt`, instantiating `PurePath` will yield `PureWindowsPath` and `Path` will yield `WindowsPath`. With any other value, instantiating `PurePath` will yield `PurePosixPath` and `Path` will yield `PosixPath`.

## Enhancements and extra functionality

This module doesn't behave "exactly" like the upstream module at all times. A basic difference is the way the classes are defined. Functionalities are defined directly as class methods opposed to forwarding them to other modules (`posixpath` & `ntpath`). The classes are regular classes and don't use `slots`.

There's a major difference in the behavior of the `joinpath` method, which builds a new path based on the path described by the instance and all the components provided as arguments. This method is leveraged by the `addition` (`+`) and `realdiv` (`/`) operators. The upstream behavior is that the resulting path will be the concatenation of the latest provided anchored path and all the following segments. It means that `('/', 'tmp').joinpath('esdferts-asf328', '/usr/local/bin/my_script.sh', '/etc', 'shadow')` would yield `('/', 'etc', 'shadow')`. In the other hand, this module's version won't accept anchored arguments and will raise a `ValueError` instead. You could still enable the upstream behavior by setting the `JOINPATH_INSANE_BEHAVIOR` constant in the instance to `True`.

There's no counterpart to the `suffixes` attribute in the upstream module. Here we added it, it's called `pure_stem`, and their relation is `pure_stem + ''.join(suffixes) == name`. For complete symmetry the `with_pure_stem` and `with_suffixes` methods were added (the latter is incredibly missing from upstream).

There's a new `child(name)` method that will build a new path by adding such name to the original one. It's a single component version of the `joinpath` functionality. Although it would seem like a redundant version of `joinpath` it's a specific case optimization instead. This `child` method doesn't require a run of `_parse_path` which could be very expensive and simply adds the new component to the original `tail` instead.

### Finite computing machines

The `BasePurePath` class, which is the root parent defined in this module (it inherits from `tuple` itself), keeps 2 versions of the path around:
- exactly the same path that was used to build the instance. The components are available in the `parts` attribute and the string can be built with `str()` (also used by `repr()`). basically recreating the behavior of the original module
- the "simplified" version of the path. The components are available in the actual value of the instance (you can slice it to get a copy) and a string can be built with `os.fspath()`. There's also a new version of the tail with these components called `simplified_tail`.

On many operating systems there's the concept of a relative path pointing to the parent directory (usually `../` and this module's default) which enable the possibility of infinite paths pointing to the same "concrete" path. E.g.:
- `foo`
- `foo/../foo`
- `foo/../foo/../foo`
- ...
- `foo` + `../foo` * n

This is a simple example, more complex constructs exist that are harder to identify. E.g.: `foo/bar/baz/../spam/../../eggs/..`. By using the "simplified" version's components for the underlying tuple, the whole infinite paths issue gets resolved. The solution is based on the fact that the hash of all equivalent paths will be the same, meaning that the interpreter will only keep one of the instances around. A side effect is that the "actual path" that gets used (stored) depends on the code path followed on each run, meaning that if you DEFINITELY need to keep the LITERAL path around for whatever reason, you better avoid using instances of this class and turn to their string equivalents instead.

## Note on bytes

Paths described as bytes are not supported yet, sorry.