#!/usr/bin/env bash
set -euo pipefail

# weekly-changes.sh
# Generate diffs for branches that had commits in the last N days
# Usage: ./weekly-changes.sh [base_branch] [days] [output_root]
# Example: ./weekly-changes.sh main 7 ./docs/tools/weekly_diff_$(date +%Y-%m-%d)

BASE_BRANCH="${1:-main}"
DAYS="${2:-7}"
OUTPUT_ROOT="${3:-./docs/tools/weekly_diff_$(date +%Y-%m-%d)}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXPORT_SCRIPT="$SCRIPT_DIR/export_branch_diff.sh"

SINCE_DESC="$DAYS days ago"

echo "Starting weekly diff export"
echo "Base branch: $BASE_BRANCH"
echo "Since: $SINCE_DESC"
echo "Output root: $OUTPUT_ROOT"
echo "Using export script: $EXPORT_SCRIPT"
echo

if [ ! -f "$EXPORT_SCRIPT" ]; then
	echo "Error: export script not found at $EXPORT_SCRIPT"
	exit 1
fi

if ! command -v git >/dev/null 2>&1; then
	echo "Error: git is required but not found in PATH"
	exit 1
fi

mkdir -p "$OUTPUT_ROOT"

echo "Collecting branches with commits since $SINCE_DESC..."

# Local branches
mapfile -t local_branches < <(git for-each-ref --format='%(refname:short)' refs/heads/)

# Remote origin branches (strip leading 'origin/')
mapfile -t remote_branches_raw < <(git for-each-ref --format='%(refname:short)' refs/remotes/origin/ || true)
remote_branches=()
for r in "${remote_branches_raw[@]:-}"; do
	# skip HEAD pointer like origin/HEAD
	if [[ "$r" == "origin/HEAD" ]]; then
		continue
	fi
	remote_branches+=("${r#origin/}")
done

# Combine and dedupe
all_branches=()
declare -A seen
for b in "${local_branches[@]:-}" "${remote_branches[@]:-}"; do
	if [ -z "$b" ]; then
		continue
	fi
	if [ -z "${seen[$b]:-}" ]; then
		all_branches+=("$b")
		seen[$b]=1
	fi
done

found=0
for branch in "${all_branches[@]:-}"; do
	# skip the base branch itself
	if [ "$branch" = "$BASE_BRANCH" ]; then
		continue
	fi

	# Check if this branch has commits in the given time window
	if git log --since="$SINCE_DESC" --pretty=oneline "$branch" | grep -q .; then
		found=$((found+1))
		echo
		echo "Processing branch: $branch"
		OUT_DIR="$OUTPUT_ROOT/$(echo "$branch" | sed 's|/|_|g')"
		mkdir -p "$OUT_DIR"
		# Call existing export script to create diffs for this branch
		bash "$EXPORT_SCRIPT" "$branch" "$BASE_BRANCH" "$OUT_DIR"
	fi
done

if [ "$found" -eq 0 ]; then
	echo "No branches with commits in the last $DAYS days were found."
	echo "Nothing to export."
else
	echo
	echo "✅ Export completed for $found branch(es)."
	echo "Files exported under: $OUTPUT_ROOT"
fi

echo
echo "Done."

