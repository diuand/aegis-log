# PyYAML reads the workflow key `on:` as `True`

**Correction.** The B-09 tests parse `.github/workflows/*.yml` with
`yaml.safe_load`. PyYAML follows YAML 1.1, where a bare `on` is a boolean,
so `wf["on"]` raises `KeyError`: the triggers sit under the key `True`.

**Rule.** Read triggers with `wf.get("on", wf.get(True))` (see
`_triggers()` in `tests/test_seeded_bugs.py`). Never "fix" this by quoting
`"on":` in workflow files; GitHub reads both forms and the tests must cope
with the common one.
