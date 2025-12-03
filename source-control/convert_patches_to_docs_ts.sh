#!/usr/bin/env bash

set -euo pipefail

# Convert git format-patch files into per-commit markdown docs
# Only include diffs for .ts files under src/
# Usage: convert_patches_to_docs_ts.sh [patch_dir] [out_dir]

PATCH_DIR="patches"
OUT_DIR="docs/patch_docs_ts"

if [ $# -ge 1 ]; then
  PATCH_DIR="$1"
fi
if [ $# -ge 2 ]; then
  OUT_DIR="$2"
fi

if [ ! -d "$PATCH_DIR" ]; then
  echo "Error: patches directory '$PATCH_DIR' not found. Run 'git format-patch' first." >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

echo "Converting patches in '$PATCH_DIR' -> '$OUT_DIR' (TS files under src/)"

count=0
skipped=0
for patch in "$PATCH_DIR"/*.patch; do
  [ -e "$patch" ] || continue
  base=$(basename "$patch" .patch)
  out="$OUT_DIR/$base.md"

  # Collect metadata lines
  subject=$(grep -m1 '^Subject:' "$patch" || true)
  subject=${subject#Subject: }
  # strip common [PATCH] tokens
  subject=$(echo "$subject" | sed -E 's/^\[[Pp][Aa][Tt][Cc][Hh][^]]*]\s*//')

  from=$(grep -m1 '^From:' "$patch" || true)
  from=${from#From: }
  date=$(grep -m1 '^Date:' "$patch" || true)
  date=${date#Date: }

  # Enhanced commit message extraction:
  # Find the line number of the first 'Subject:' header. Then find the first blank line following the header block.
  # The commit message is normally the paragraph(s) between the first blank line after the headers and the line that starts with '---' or 'diff --git'
  msg=""
  # Use awk to capture the body after the patch headers and before the diff separator
  msg=$(awk '
    BEGIN{collect=0}
    /^Subject:/ {subject_seen=1; next}
    subject_seen && /^$/ {collect=1; next}
    collect==1 && (/^---$|^diff --git /){exit}
    collect==1 {print}
  ' "$patch" | sed '1{/^$/d}' || true)

  # Trim leading/trailing whitespace from msg
  msg=$(echo "$msg" | sed -E 's/^\s+//; s/\s+$//')

  # If no commit message body was found, use the subject as a fallback (many format-patch outputs only contain Subject)
  if [ -z "$msg" ] && [ -n "$subject" ]; then
    msg="$subject"
  fi

  # Now we need to extract only diffs that affect src/ and end with .ts
  # We'll scan for diff --git lines and collect subsequent hunk until next diff --git
  # For each diff --git a/path b/path, test if either path matches ^a/src/.*\.ts$

  # read whole file and split by diff --git sections
  matched_diff=""
  awk -v RS='^diff --git ' 'NR>1{print "diff --git " $0}' "$patch" | while IFS= read -r section; do
    # find the a/ and b/ paths from the diff header
    header=$(echo "$section" | sed -n '1p')
    a_path=$(echo "$header" | awk '{print $3}' || true)
    b_path=$(echo "$header" | awk '{print $4}' || true)
    # paths are like a/src/..., b/src/...
    if [[ "$a_path" =~ ^a/src/.*\.ts$ || "$b_path" =~ ^b/src/.*\.ts$ ]]; then
      # append this section
      matched_diff+="$section\n"
    fi
  done

  # Because we're inside a pipe, matched_diff may be empty — to correctly capture we re-run different approach using perl for portability
  matched_diff=$(perl -0777 -ne 'while(/(^diff --git .*?)(?=^diff --git |\z)/msg){ $sec=$1; if($sec=~/^diff --git\s+(\S+)\s+(\S+)/){ $a=$1; $b=$2; if($a=~/^a\/src\/.*\.ts$/ || $b=~/^b\/src\/.*\.ts$/){ print $sec } } }' "$patch" || true)

  if [ -z "$matched_diff" ]; then
    # nothing to include for ts under src
    skipped=$((skipped+1))
    continue
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
    if [ -n "$msg" ]; then
      echo "$msg"
    else
      echo "_(no commit message found)_"
    fi
    echo ""
    echo "## Diff (only .ts files under src/)"
    echo ""
    echo '\```diff'
    # print the matched_diff raw
    printf "%s" "$matched_diff"
    echo '\```'
  } > "$out"

  count=$((count+1))
done

echo "Done — converted $count patch(es). Skipped $skipped patches with no src/*.ts diffs. Output in '$OUT_DIR'"

exit 0
