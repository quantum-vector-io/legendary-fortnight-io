# Two Sum

## Problem Statement
Given an array of integers `nums` and an integer `target`, return indices of the two numbers such that they add up to `target`.

You may assume that each input would have exactly one solution, and you may not use the same element twice.

You can return the answer in any order.

## Examples

**Example 1:**
```
Input: nums = [2,7,11,15], target = 9
Output: [0,1]
Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].
```

**Example 2:**
```
Input: nums = [3,2,4], target = 6
Output: [1,2]
```

**Example 3:**
```
Input: nums = [3,3], target = 6
Output: [0,1]
```

## Constraints
- 2 <= nums.length <= 10^4
- -10^9 <= nums[i] <= 10^9
- -10^9 <= target <= 10^9
- Only one valid answer exists.

## Approach

### Brute Force (Not Optimal)
Check every pair of numbers - O(n²) time, O(1) space

### Hash Map (Optimal)
1. Create a hash map to store value -> index
2. For each number, check if (target - number) exists in the hash map
3. If found, return both indices
4. Otherwise, add current number to hash map

## Time Complexity: O(n)
## Space Complexity: O(n)

## Solution (Python)

```python
def two_sum(nums, target):
    """
    Find two numbers that add up to target.
    
    Args:
        nums: List of integers
        target: Target sum
        
    Returns:
        List of two indices
    """
    seen = {}  # value -> index
    
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    
    return []  # No solution found

# Test cases
assert two_sum([2,7,11,15], 9) == [0,1]
assert two_sum([3,2,4], 6) == [1,2]
assert two_sum([3,3], 6) == [0,1]
print("All tests passed!")
```

## Solution (JavaScript)

```javascript
function twoSum(nums, target) {
  const seen = new Map(); // value -> index
  
  for (let i = 0; i < nums.length; i++) {
    const complement = target - nums[i];
    if (seen.has(complement)) {
      return [seen.get(complement), i];
    }
    seen.set(nums[i], i);
  }
  
  return []; // No solution found
}

// Test cases
console.assert(JSON.stringify(twoSum([2,7,11,15], 9)) === JSON.stringify([0,1]));
console.assert(JSON.stringify(twoSum([3,2,4], 6)) === JSON.stringify([1,2]));
console.assert(JSON.stringify(twoSum([3,3], 6)) === JSON.stringify([0,1]));
console.log("All tests passed!");
```

## Notes
- This is LeetCode #1, a classic interview question
- Hash map provides O(1) lookup time
- Trade-off: Use extra space for better time complexity
- Watch out for edge cases like duplicate numbers
- Can be solved with sorting + two pointers, but that modifies indices

## Follow-up
- What if the array is sorted? (Use two pointers)
- What if there are multiple solutions? (Return all pairs)
- What if you need to return values instead of indices?
