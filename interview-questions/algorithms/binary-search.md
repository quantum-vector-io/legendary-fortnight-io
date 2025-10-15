# Binary Search

## Problem Statement
Given a sorted array of integers `nums` and a target value, return the index of the target if it exists in the array. If it doesn't exist, return -1.

You must write an algorithm with O(log n) runtime complexity.

## Examples

**Example 1:**
```
Input: nums = [-1,0,3,5,9,12], target = 9
Output: 4
Explanation: 9 exists in nums and its index is 4
```

**Example 2:**
```
Input: nums = [-1,0,3,5,9,12], target = 2
Output: -1
Explanation: 2 does not exist in nums so return -1
```

## Constraints
- 1 <= nums.length <= 10^4
- -10^4 < nums[i], target < 10^4
- All integers in nums are unique
- nums is sorted in ascending order

## Approach

Binary search repeatedly divides the search space in half:
1. Set left = 0, right = length - 1
2. While left <= right:
   - Calculate mid = (left + right) // 2
   - If nums[mid] == target, return mid
   - If nums[mid] < target, search right half (left = mid + 1)
   - If nums[mid] > target, search left half (right = mid - 1)
3. If not found, return -1

## Time Complexity: O(log n)
## Space Complexity: O(1)

## Solution (Python)

```python
def binary_search(nums, target):
    """
    Binary search for target in sorted array.
    
    Args:
        nums: Sorted list of integers
        target: Value to find
        
    Returns:
        Index of target, or -1 if not found
    """
    left, right = 0, len(nums) - 1
    
    while left <= right:
        mid = (left + right) // 2
        
        if nums[mid] == target:
            return mid
        elif nums[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

# Test cases
assert binary_search([-1,0,3,5,9,12], 9) == 4
assert binary_search([-1,0,3,5,9,12], 2) == -1
assert binary_search([5], 5) == 0
print("All tests passed!")
```

## Solution (JavaScript)

```javascript
function binarySearch(nums, target) {
  let left = 0;
  let right = nums.length - 1;
  
  while (left <= right) {
    const mid = Math.floor((left + right) / 2);
    
    if (nums[mid] === target) {
      return mid;
    } else if (nums[mid] < target) {
      left = mid + 1;
    } else {
      right = mid - 1;
    }
  }
  
  return -1;
}

// Test cases
console.assert(binarySearch([-1,0,3,5,9,12], 9) === 4);
console.assert(binarySearch([-1,0,3,5,9,12], 2) === -1);
console.assert(binarySearch([5], 5) === 0);
console.log("All tests passed!");
```

## Notes
- Classic divide-and-conquer algorithm
- Only works on sorted arrays
- Be careful with integer overflow when calculating mid in some languages
- Use `mid = left + (right - left) // 2` to avoid overflow
- Can be implemented recursively or iteratively

## Variations
- First/last occurrence of target
- Search in rotated sorted array
- Find insertion position
- Search in 2D matrix

## Common Mistakes
- Off-by-one errors with indices
- Infinite loops if not updating left/right correctly
- Not handling empty array case
