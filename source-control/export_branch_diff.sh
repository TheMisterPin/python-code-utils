#!/bin/bash

# Git Branch Diff Export Script
# Usage: ./export_branch_diff.sh <target_branch> [base_branch] [output_dir]
# Example: ./export_branch_diff.sh feature/my-branch main ./diff_export

# Default values
BASE_BRANCH="master"
OUTPUT_DIR="./branch_diff_export"

# Parse arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <target_branch> [base_branch] [output_dir]"
    echo "Example: $0 feature/my-branch main ./diff_export"
    exit 1
fi

TARGET_BRANCH="$1"
if [ $# -ge 2 ]; then
    BASE_BRANCH="$2"
fi
if [ $# -ge 3 ]; then
    OUTPUT_DIR="$3"
fi

echo "🚀 Starting diff export..."
echo "Exporting diff between '$BASE_BRANCH' and '$TARGET_BRANCH'"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Check if branches exist
if ! git show-ref --verify --quiet refs/heads/$TARGET_BRANCH && ! git show-ref --verify --quiet refs/remotes/origin/$TARGET_BRANCH; then
    echo "Error: Branch '$TARGET_BRANCH' does not exist"
    exit 1
fi

if ! git show-ref --verify --quiet refs/heads/$BASE_BRANCH && ! git show-ref --verify --quiet refs/remotes/origin/$BASE_BRANCH; then
    echo "Error: Base branch '$BASE_BRANCH' does not exist"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Get list of modified files
echo "🔍 Getting list of modified files..."
MODIFIED_FILES=$(git diff --name-only $BASE_BRANCH..$TARGET_BRANCH)

if [ -z "$MODIFIED_FILES" ]; then
    echo "ℹ️  No files differ between $BASE_BRANCH and $TARGET_BRANCH"
    echo "Press any key to continue..."
    read -n 1 -s
    exit 0
fi

echo "📝 Found $(echo "$MODIFIED_FILES" | wc -l) modified files"
echo ""

# Process each modified file
while IFS= read -r file; do
    if [ -z "$file" ]; then
        continue
    fi

    echo "📄 Processing: $file"

    # Create directory structure in output
    file_dir=$(dirname "$file")
    if [ "$file_dir" != "." ]; then
        mkdir -p "$OUTPUT_DIR/$file_dir"
    fi

    # Generate diff for this file and save as .txt
    output_file="$OUTPUT_DIR/${file}.txt"

    # Add header to the diff file
    {
        echo "========================================"
        echo "DIFF: $file"
        echo "Base branch: $BASE_BRANCH"
        echo "Target branch: $TARGET_BRANCH"
        echo "========================================"
        echo ""

        # Generate the actual diff
        git diff $BASE_BRANCH..$TARGET_BRANCH -- "$file"

    } > "$output_file"

done <<< "$MODIFIED_FILES"

echo ""
echo "=========================================="
echo "✅ DIFF EXPORT COMPLETED!"
echo "=========================================="
echo "Files exported to: $OUTPUT_DIR"
echo "Total files processed: $(find "$OUTPUT_DIR" -name "*.txt" 2>/dev/null | wc -l)"
echo ""
echo "📁 Summary file structure:"
find "$OUTPUT_DIR" -name "*.txt" 2>/dev/null | head -10
if [ $(find "$OUTPUT_DIR" -name "*.txt" 2>/dev/null | wc -l) -gt 10 ]; then
    echo "... and $(( $(find "$OUTPUT_DIR" -name "*.txt" 2>/dev/null | wc -l) - 10 )) more files"
fi
echo ""
echo "🎉 All done! Check the '$OUTPUT_DIR' folder for your diff files."
echo ""
echo "Press any key to continue..."
read -n 1 -s
