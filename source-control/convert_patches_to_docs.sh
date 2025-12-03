#!/usr/bin/env bash

# Convert git format-patch files into per-commit markdown docs
# Output: docs/patch_docs/<patch-file>.md

set -euo pipefail

PATCH_DIR="patches"
OUT_DIR="docs/patch_docs"

if [ ! -d "$PATCH_DIR" ]; then
  echo "Error: patches directory '$PATCH_DIR' not found. Run 'git format-patch' first." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

echo "Converting patches in '$PATCH_DIR' -> '$OUT_DIR'"

count=0
for patch in "$PATCH_DIR"/*.patch; do
  [ -e "$patch" ] || continue
  base=$(basename "$patch" .patch)
  out="$OUT_DIR/$base.md"

  # Extract header fields (first matches)
  subject=$(grep -m1 '^Subject:' "$patch" || true)
  subject=${subject#Subject: }
  # Remove common '[PATCH]' or '[PATCH n/m]' prefix
  subject=$(echo "$subject" | sed -E 's/^\[[Pp][Aa][Tt][Cc][Hh][^]]*]\s*//')

  from=$(grep -m1 '^From:' "$patch" || true)
  from=${from#From: }
  date=$(grep -m1 '^Date:' "$patch" || true)
  date=${date#Date: }

  # Extract commit message: the block after headers and before the first '---' separator or before the diff section
  commit_msg=$(awk 'BEGIN{p=0;h=0} /^Subject:/ {h=1; next} h==1 && /^$/ {p=1; next} p==1 { if (/^---$/) exit; print }' "$patch" || true)

  # Extract diff content (from first diff --git to end). If there's no 'diff --git' fallback to everything after '---'
  if grep -q '^diff --git' "$patch"; then
    diff_section=$(sed -n '/^diff --git/,$p' "$patch")
  else
    # fallback: everything after the first '---' separator
    diff_section=$(awk 'BEGIN{p=0} /^---$/ { p=1; next } p==1{ print }' "$patch" || true)
  fi

  # Compose markdown
  {
    echo "# $subject"
    echo ""
    echo "**Source file:** $patch"
    echo "**Author:** $from"
    echo "**Date:** $date"
    echo ""
    echo "---"
    echo ""
    echo "## Commit message"
    echo ""
    if [ -n "$commit_msg" ]; then
      echo "\
$commit_msg\
"
    else
      echo "_(no commit message found)_"
    fi
    echo ""
    echo "## Diff"
    echo ""
    echo '\```diff'
    # Print the diff content unmodified
    echo "$diff_section"
    echo '\```'
  } > "$out"

  count=$((count+1))
done

echo "Done — converted $count patch(es). Output in '$OUT_DIR'"

exit 0
