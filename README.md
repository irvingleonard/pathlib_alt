# pathlib_, a reimplementation of the python standard library's pathlib

ProofThe main reason to attempt such work is because of the deep-rooted limitations found in the standard library's pathlib and also to improve the OOP focus of the library. The limitations identified so far:
1. It would seem that the original idea was that a path is a string, and most of the module works around that. It could also be that it was trying to leverage as much as possible the existing functions from `os.path` which work with such assumption. This module takes a different approach (the OOP approach) and assumes that a path is a sequence of components separated by a "separator".
2. The official module can't decide if paths are immutable or not, making extensive use of properties (which suggest mutability) but then the `__str__` method, the workhorse in a world of paths as strings, looks like
	```
	try:
		return self._str
	except AttributeError:
		self._str = self._format_parsed_parts(self.drive, self.root, self._tail) or '.'
		return self._str
	```
	basically making the paths immutable for all intents and purposes.
3. There are only two possible paths formats in this world, you're POSIX or Windows, period. This assumption is deeply rooted in the code, almost impossible to work around.
4. Even if you were to work with the previous constraint and try to make a "POSIX-like flavour" (or a Windows-like one) your implementation would be a new module with functions and variables/constants, like the `posixpath` or `ntpath` modules, no inheriting and overriding or re-implementing (the OOP way).

Which such limitations in mind, this implementation follows a different path :P
- Paths are immutable sequences, `BasePurePath`, which are based on a `tuple`, and which is the root of the inheritance tree.
- Paths components are separated by a "separator" that your child class can/should/must override (defaults to `/`)
- The complex part of parsing a path is the "prefix" part, what is called "anchor" (the "drive" and/or "root"). Such analysis should be implemented by the child class via the `_parse_path` method, which should take a string as argument and return a tuple of `("drive", "root", [parts])`
- Anything that can't be generalized to all paths is not implemented on the base class and should come from the children, like `as_posix` (questionable method, but kept for complete compatibility), `as_uri` (different systems prefer different `file://` URIs), or `match` (pattern globbing depends on your current shell).
- Some other methods can be overridden as needed based on specifics, but their default implementation usually cover the generally accepted conventions (like `_parse_name`)
