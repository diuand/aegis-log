# Memory index

One file per real correction made while building aegis-log. Changes go
through a pull request reviewed by the code owner.

- [pyyaml-reads-on-as-true.md](pyyaml-reads-on-as-true.md): workflow tests must read the `on:` key as `True`
- [bandit-nosec-comment-order.md](bandit-nosec-comment-order.md): put the tracking tag before `nosec`, not after
- [evidence-must-be-masked.md](evidence-must-be-masked.md): evidence leaked the fake key and home paths until masked
- [negative-sample-must-miss.md](negative-sample-must-miss.md): a negative sample must differ in the field the rule keys on
- [windows-make-needs-git-bash.md](windows-make-needs-git-bash.md): run make from Git Bash; venv uses `Scripts/` on Windows
- [quarantined-workflow-shortcuts.md](quarantined-workflow-shortcuts.md): the poisoned baseline note, kept quarantined as a record (B-10)
