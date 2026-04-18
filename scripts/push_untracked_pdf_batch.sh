#!/usr/bin/env bash

# Usage: ./scripts/push_untracked_pdf_batch.sh [BATCH_SIZE] [COMMIT_MESSAGE]
# Example: ./scripts/push_untracked_pdf_batch.sh 30 "chore: add rolling report batch"

set -euo pipefail

BATCH_SIZE="${1:-30}"
COMMIT_MESSAGE="${2:-chore: add rolling report batch}"

if ! [[ "$BATCH_SIZE" =~ ^[1-9][0-9]*$ ]]; then
  echo "BATCH_SIZE must be a positive integer: $BATCH_SIZE" >&2
  exit 1
fi

mapfile -t pdf_files < <(
  git ls-files --others --exclude-standard -- 'reports_raw/*.pdf' 'reports_raw/**/*.pdf' \
    | head -n "$BATCH_SIZE"
)

if [[ "${#pdf_files[@]}" -eq 0 ]]; then
  echo "No untracked reports_raw PDF files found. Nothing to commit."
  exit 0
fi

for pdf_file in "${pdf_files[@]}"; do
  git add -- "$pdf_file"
done

git commit -m "$COMMIT_MESSAGE"

echo "Committed ${#pdf_files[@]} untracked PDF file(s)."
