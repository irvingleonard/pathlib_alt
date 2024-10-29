#!python
"""
Unix filename pattern matching

This is a backport from newer versions of the module (currently Python 3.13.0).
"""

import re

def _join_translated_parts(inp, STAR):
	# Deal with STARs.
	res = []
	add = res.append
	i, n = 0, len(inp)
	# Fixed pieces at the start?
	while i < n and inp[i] is not STAR:
		add(inp[i])
		i += 1
	# Now deal with STAR fixed STAR fixed ...
	# For an interior `STAR fixed` pairing, we want to do a minimal
	# .*? match followed by `fixed`, with no possibility of backtracking.
	# Atomic groups ("(?>...)") allow us to spell that directly.
	# Note: people rely on the undocumented ability to join multiple
	# translate() results together via "|" to build large regexps matching
	# "one of many" shell patterns.
	while i < n:
		assert inp[i] is STAR
		i += 1
		if i == n:
			add(".*")
			break
		assert inp[i] is not STAR
		fixed = []
		while i < n and inp[i] is not STAR:
			fixed.append(inp[i])
			i += 1
		fixed = "".join(fixed)
		if i == n:
			add(".*")
			add(fixed)
		else:
			add(f"(?>.*?{fixed})")
	assert i == n
	res = "".join(res)
	return fr'(?s:{res})\Z'

def _translate(pat, STAR, QUESTION_MARK):
	res = []
	add = res.append
	i, n = 0, len(pat)
	while i < n:
		c = pat[i]
		i = i+1
		if c == '*':
			# compress consecutive `*` into one
			if (not res) or res[-1] is not STAR:
				add(STAR)
		elif c == '?':
			add(QUESTION_MARK)
		elif c == '[':
			j = i
			if j < n and pat[j] == '!':
				j = j+1
			if j < n and pat[j] == ']':
				j = j+1
			while j < n and pat[j] != ']':
				j = j+1
			if j >= n:
				add('\\[')
			else:
				stuff = pat[i:j]
				if '-' not in stuff:
					stuff = stuff.replace('\\', r'\\')
				else:
					chunks = []
					k = i+2 if pat[i] == '!' else i+1
					while True:
						k = pat.find('-', k, j)
						if k < 0:
							break
						chunks.append(pat[i:k])
						i = k+1
						k = k+3
					chunk = pat[i:j]
					if chunk:
						chunks.append(chunk)
					else:
						chunks[-1] += '-'
					# Remove empty ranges -- invalid in RE.
					for k in range(len(chunks)-1, 0, -1):
						if chunks[k-1][-1] > chunks[k][0]:
							chunks[k-1] = chunks[k-1][:-1] + chunks[k][1:]
							del chunks[k]
					# Escape backslashes and hyphens for set difference (--).
					# Hyphens that create ranges shouldn't be escaped.
					stuff = '-'.join(s.replace('\\', r'\\').replace('-', r'\-')
									 for s in chunks)
				# Escape set operations (&&, ~~ and ||).
				stuff = re.sub(r'([&~|])', r'\\\1', stuff)
				i = j+1
				if not stuff:
					# Empty range: never match.
					add('(?!)')
				elif stuff == '!':
					# Negated empty range: match any character.
					add('.')
				else:
					if stuff[0] == '!':
						stuff = '^' + stuff[1:]
					elif stuff[0] in ('^', '['):
						stuff = '\\' + stuff
					add(f'[{stuff}]')
		else:
			add(re.escape(c))
	assert i == n
	return res

def translate(pat):
	"""Translate a shell PATTERN to a regular expression.

	There is no way to quote meta-characters.
	"""

	STAR = object()
	parts = _translate(pat, STAR, '.')
	return _join_translated_parts(parts, STAR)
