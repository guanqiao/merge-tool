import sys
sys.path.insert(0, '.')

from src.diff_engine import DiffEngine, DiffType

# Test 1: Compare identical lines
result = DiffEngine.compare_lines(['a', 'b', 'c'], ['a', 'b', 'c'])
assert result.change_count == 0, f"Expected 0 changes, got {result.change_count}"
print("✓ Test 1 passed: Identical files have 0 changes")

# Test 2: Compare different lines
result = DiffEngine.compare_lines(['a', 'b', 'c'], ['a', 'x', 'c'])
assert result.change_count == 1, f"Expected 1 change, got {result.change_count}"
print("✓ Test 2 passed: Different files detected")

# Test 3: Insertions
result = DiffEngine.compare_lines(['a', 'b'], ['a', 'b', 'c', 'd'])
assert result.change_count == 2, f"Expected 2 changes, got {result.change_count}"
print("✓ Test 3 passed: Insertions detected")

# Test 4: Deletions
result = DiffEngine.compare_lines(['a', 'b', 'c', 'd'], ['a', 'b'])
assert result.change_count == 2, f"Expected 2 changes, got {result.change_count}"
print("✓ Test 4 passed: Deletions detected")

print("\n✅ All diff engine tests passed!")
