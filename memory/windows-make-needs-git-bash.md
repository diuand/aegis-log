# On Windows, run make from Git Bash

**Correction.** GNU make on Windows falls back to `cmd.exe` when no `sh` is on
PATH, which breaks `VAR=1 command` lines and forward-slash paths, and the
virtualenv puts executables in `.venv/Scripts/` instead of `.venv/bin/`.

**Rule.** The Makefile picks `BIN` and the Python launcher from `$(OS)`; docs
tell Windows users to run `make` from Git Bash. Shell scripts are invoked as
`bash script.sh` so they do not depend on the executable bit.
