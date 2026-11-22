# Security policy

aegis-log is a university lab project. It is deliberately vulnerable at the
`baseline-vulnerable` tag and is meant to run only on `127.0.0.1`.

## Reporting

Open a private security advisory on this repository (Security tab, "Report a
vulnerability"), or contact the repository owner directly. Do not open a
public issue for an unfixed vulnerability.

## Scope

- In scope: the code on `main`, the CI workflows, the agent configuration.
- Out of scope: the ten seeded bugs on `baseline-vulnerable` (B-01 to B-10).
  They are documented on purpose in `docs/BUG-REPORT.md`.

## Rules for testing

Proofs of exploitation stay local and benign: tests against the app on
localhost with a harmless marker. Never scan or send traffic to any other
host. Every secret in this repository is a placeholder; real keys live only
in the git-ignored `.env`.
