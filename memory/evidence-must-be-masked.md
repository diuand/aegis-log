# Evidence must be masked before it is committed

**Correction.** The first `baseline-red.txt` contained the seeded fake key
(pytest prints both sides of a failed comparison) and the author's home
directory in tracebacks. A first masking pass still missed paths printed as
Python reprs, where every backslash is doubled.

**Rule.** Every evidence file goes through `scripts/mask_evidence.py`, which
masks `aegk_` keys (also when pytest elides them with `...`), bearer tokens,
the repository root and any `Users/` or `/home/` path, in plain and
repr-escaped form. The `evidence-*` make targets call it automatically.
After masking, grep the file for the key prefix and the user name.
