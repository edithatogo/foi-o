#!/usr/bin/env bash
set -euo pipefail

OWNER="${REPO_OWNER:-edithatogo}"
REPO="${REPO_NAME:-foi-o-nz}"
VISIBILITY="${REPO_VISIBILITY:-public}"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI 'gh' is required for repository bootstrap." >&2
  exit 1
fi

if gh repo view "${OWNER}/${REPO}" >/dev/null 2>&1; then
  echo "Repository ${OWNER}/${REPO} already exists."
else
  if [[ "${VISIBILITY}" == "private" ]]; then
    gh repo create "${OWNER}/${REPO}" --private --source=. --remote=origin --push
  else
    gh repo create "${OWNER}/${REPO}" --public --source=. --remote=origin --push
  fi
fi

gh variable set HF_REPO_ID --repo "${OWNER}/${REPO}" --body "${HF_REPO_ID:-edithatogo/foi-o-nz}"
gh variable set ARCHIVE_TITLE --repo "${OWNER}/${REPO}" --body "${ARCHIVE_TITLE:-FOI-O NZ}"
gh variable set ARCHIVE_LICENSE --repo "${OWNER}/${REPO}" --body "${ARCHIVE_LICENSE:-MIT}"

echo "Bootstrap complete: https://github.com/${OWNER}/${REPO}"
