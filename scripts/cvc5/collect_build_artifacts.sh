#!/bin/bash
# Collect CVC5 build artifacts preserving build directory structure
# This script collects everything needed for coverage analysis:
# - Headers, binary, CMake files, .gcno files
# - All files preserve their relative paths from build/
# Note: Source .cpp files are NOT collected - they're available from CVC5 checkout
#
# Usage: ./collect_build_artifacts.sh <build_dir> <output_dir>
# Example: ./collect_build_artifacts.sh cvc5/build artifacts

set -e

BUILD_DIR="${1:-cvc5/build}"
OUTPUT_DIR="${2:-artifacts}"

if [ ! -d "$BUILD_DIR" ]; then
    echo "Error: Build directory not found: $BUILD_DIR"
    exit 1
fi

echo "📦 Collecting build artifacts from $BUILD_DIR"
echo "   Output directory: $OUTPUT_DIR"
echo "   Preserving build directory structure..."

mkdir -p "$OUTPUT_DIR"

# Collect binary
if [ -f "$BUILD_DIR/bin/cvc5" ]; then
    mkdir -p "$OUTPUT_DIR/bin"
    cp "$BUILD_DIR/bin/cvc5" "$OUTPUT_DIR/bin/cvc5"
    chmod +x "$OUTPUT_DIR/bin/cvc5"
    BINARY_SIZE=$(du -h "$OUTPUT_DIR/bin/cvc5" | cut -f1)
    echo "   ✓ Binary copied ($BINARY_SIZE)"
else
    echo "   ⚠ Warning: Binary not found at $BUILD_DIR/bin/cvc5"
fi

# Collect compile_commands.json
if [ -f "$BUILD_DIR/compile_commands.json" ]; then
    cp "$BUILD_DIR/compile_commands.json" "$OUTPUT_DIR/compile_commands.json"
    echo "   ✓ compile_commands.json copied"
fi

# Collect CMakeCache.txt
if [ -f "$BUILD_DIR/CMakeCache.txt" ]; then
    cp "$BUILD_DIR/CMakeCache.txt" "$OUTPUT_DIR/CMakeCache.txt"
    echo "   ✓ CMakeCache.txt copied"
fi

# Collect all CTestTestfile.cmake files (preserving structure)
CTEST_COUNT=0
find "$BUILD_DIR" -name "CTestTestfile.cmake" -type f 2>/dev/null | while read -r ctest_file; do
    rel_path="${ctest_file#$BUILD_DIR/}"
    target_path="$OUTPUT_DIR/$rel_path"
    mkdir -p "$(dirname "$target_path")"
    cp "$ctest_file" "$target_path"
    CTEST_COUNT=$((CTEST_COUNT + 1))
done 2>/dev/null || true

CTEST_COUNT=$(find "$OUTPUT_DIR" -name "CTestTestfile.cmake" -type f 2>/dev/null | wc -l || echo "0")
if [ "$CTEST_COUNT" -gt 0 ]; then
    echo "   ✓ Collected $CTEST_COUNT CTestTestfile.cmake files"
fi

# Collect all headers (.h, .hpp, .hxx) preserving structure
HEADER_COUNT=0
find "$BUILD_DIR" -type f \( -name "*.h" -o -name "*.hpp" -o -name "*.hxx" \) 2>/dev/null | while read -r header; do
    rel_path="${header#$BUILD_DIR/}"
    target_path="$OUTPUT_DIR/$rel_path"
    mkdir -p "$(dirname "$target_path")"
    cp "$header" "$target_path"
done 2>/dev/null || true

HEADER_COUNT=$(find "$OUTPUT_DIR" -type f \( -name "*.h" -o -name "*.hpp" -o -name "*.hxx" \) 2>/dev/null | wc -l || echo "0")
if [ "$HEADER_COUNT" -gt 0 ]; then
    echo "   ✓ Collected $HEADER_COUNT header files"
fi

# Collect all .gcno files (coverage notes) preserving structure
GCNO_COUNT=0
find "$BUILD_DIR" -name "*.gcno" -type f 2>/dev/null | while read -r gcno_file; do
    rel_path="${gcno_file#$BUILD_DIR/}"
    target_path="$OUTPUT_DIR/$rel_path"
    mkdir -p "$(dirname "$target_path")"
    cp "$gcno_file" "$target_path"
done 2>/dev/null || true

GCNO_COUNT=$(find "$OUTPUT_DIR" -name "*.gcno" -type f 2>/dev/null | wc -l || echo "0")
if [ "$GCNO_COUNT" -gt 0 ]; then
    echo "   ✓ Collected $GCNO_COUNT .gcno files"
fi

# Note: We do NOT collect source .cpp files because:
# 1. .gcno files contain absolute paths pointing to cvc5/src/... (source directory)
# 2. Source files are already available from the CVC5 checkout in coverage workflow
# 3. fastcov will find source files at their absolute paths from .gcno files

# Summary
echo ""
echo "✅ Artifact collection complete!"
echo "   All files preserve build directory structure"
echo ""
echo "📊 Summary:"
echo "   Headers: $HEADER_COUNT"
echo "   .gcno files: $GCNO_COUNT"
echo "   CTestTestfile.cmake: $CTEST_COUNT"
if [ -f "$OUTPUT_DIR/bin/cvc5" ]; then
    echo "   Binary: ✓"
else
    echo "   Binary: ✗"
fi
if [ -f "$OUTPUT_DIR/compile_commands.json" ]; then
    echo "   compile_commands.json: ✓"
fi
if [ -f "$OUTPUT_DIR/CMakeCache.txt" ]; then
    echo "   CMakeCache.txt: ✓"
fi
