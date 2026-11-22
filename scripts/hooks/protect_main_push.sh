#!/usr/bin/env bash
# pre-push guard: refuse pushes to main, deletion of main and force pushes.
#
# Works under pre-commit (PRE_COMMIT_* variables) and as a plain git
# pre-push hook (ref lines on stdin). It is a local control: a human can skip
# it with --no-verify, which CONTRIBUTING.md forbids and the governance
# workflow would expose.
set -euo pipefail

ZERO=0000000000000000000000000000000000000000
status=0

check() {
  local local_sha="$1" remote_ref="$2" remote_sha="$3"
  if [[ "$remote_ref" == "refs/heads/main" ]]; then
    if [[ "$local_sha" == "$ZERO" ]]; then
      echo "refused: deleting main is not allowed" >&2
    else
      echo "refused: direct push to main. Open a pull request instead." >&2
    fi
    status=1
    return
  fi
  if [[ "$remote_sha" != "$ZERO" && "$local_sha" != "$ZERO" ]]; then
    if ! git cat-file -e "${remote_sha}^{commit}" 2>/dev/null \
       || ! git merge-base --is-ancestor "$remote_sha" "$local_sha"; then
      echo "refused: non-fast-forward (force) push to ${remote_ref#refs/heads/}" >&2
      status=1
    fi
  fi
}

if [[ -n "${PRE_COMMIT_REMOTE_BRANCH:-}" ]]; then
  check "${PRE_COMMIT_TO_REF:-$ZERO}" "$PRE_COMMIT_REMOTE_BRANCH" "${PRE_COMMIT_FROM_REF:-$ZERO}"
else
  while read -r _local_ref local_sha remote_ref remote_sha; do
    [[ -z "${remote_ref:-}" ]] && continue
    check "$local_sha" "$remote_ref" "$remote_sha"
  done
fi
exit "$status"
