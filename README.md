# pathlib_, a reimplementation of the python standard library's pathlib

## Rationale

The main reason to attempt such work is because of the deep-rooted limitations found in the standard library's pathlib and also to improve the OOP focus of the library. The limitations identified so far:
1. It would seem that the original idea was that a path is a string, and most of the module works around that. It could also be that it was trying to leverage as much as possible the existing functions from `os.path` which work with such assumption. This module takes a different approach (the OOP approach) and assumes that a path is a sequence of components (strings) separated by a "separator".
2. The official module uses `slots`, apparently to improve the performance. Here we use lazy computation which should help with the processing requirements and simplified path versions as the base which should improve the memory footprint.
3. There are only two possible paths formats in this world, you're POSIX or Windows, period. This assumption is deeply rooted in the code, almost impossible to work around.
4. Even if you were to work with the previous constraint and try to make a "POSIX-like flavour" (or a Windows-like one) your implementation would be a new module with functions and variables/constants, like the `posixpath` or `ntpath` modules, no inheriting and overriding or re-implementing (the OOP way).

Which such limitations in mind, this implementation follows a different path :P
- Paths are immutable sequences, `BasePurePath`, which are based on a `tuple`, and which is the root of the inheritance tree.
- Paths components are separated by a "separator" that your child class can/should/must override (defaults to `/`)
- The complex part of parsing a path is the "prefix" part, what is called "anchor" (the "drive" and/or "root"). Such analysis should be implemented by the child class via the `_parse_path` method, which should take a string as argument and return a tuple of `("drive", "root", [parts])`
- Anything that can't be generalized to all paths is not implemented on the base class and should come from the children, like `as_posix` (questionable method, but kept for complete compatibility), or `as_uri` (different systems prefer different `file://` URIs).
- Some other methods can be overridden as needed based on specifics, but their default implementation usually cover the generally accepted conventions (like `_parse_name`)

## Finite computing machines

The `BasePurePath` class, which is the root parent defined in this module (it inherits from `tuple` itself), keeps 2 versions of the path around:
- exactly the same path that was used to build the instance. The components are available in the `parts` attribute and the string can be build with `str()` (also used by `repr()`). basically recreating the behavior of the original module
- the "simplified" version of the path. The components are available in the actual value of the instance (you can slice it to get a copy) and a string can be build with `os.fspath()`

On many operating systems there's the concept of a relative path pointing to the parent directory (usually `../` and this module's default) which enable the possibility of infinite paths pointing to the same "concrete" path. E.g.:
- `foo`
- `foo/../foo`
- `foo/../foo/../foo`
- ...
- `foo` + `../foo` * n

This is a simple example, more complex constructs exist that are harder to identify. E.g.: `foo/bar/baz/../spam/../../eggs/..`. By using the "simplified" version's components for the underlying tuple, the whole infinite paths issue gets resolved. The solution is based on the fact that the hash of all equivalent paths will be the same, meaning that the interpreter will only keep one of the instances around. A side effect is that the "actual path" that gets used (stored) depends on the code path followed on each run, meaning that if you DEFINITELY need to keep the LITERAL path around for whatever reason, you better avoid using instances of this class and turn to their string equivalents instead.