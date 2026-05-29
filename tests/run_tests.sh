#!/bin/bash
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD"

echo "=== MisfitsLauncher Test Suite ==="
echo ""

run_test() {
    echo "--- $1 ---"
    python3 -m pytest "$2" "$1" -v --tb=short 2>/dev/null || \
    python3 -m unittest "$1" -v
    echo ""
}

# Run each test file
for test_file in tests/test_*.py; do
    basename=$(basename "$test_file" .py)
    echo "=== $basename ==="
    python3 -m unittest "tests.$basename" -v
    echo ""
done

echo "=== All tests completed ==="
