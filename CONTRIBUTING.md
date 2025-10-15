# Contributing to Your Learning Journey

This is your personal learning repository, so feel free to organize it however works best for you! However, here are some guidelines to keep things organized and maximize your learning.

## Adding New Content

### When Adding a New Language

1. Create the language directory if it doesn't exist
2. Add a `README.md` with:
   - Setup instructions
   - Learning path
   - Project ideas
   - Useful resources
3. Organize content into subdirectories:
   ```
   language-name/
   ├── README.md
   ├── basics/
   ├── projects/
   ├── snippets/
   └── exercises/
   ```

### When Adding Interview Questions

1. Choose the appropriate category (algorithms, data-structures, system-design, etc.)
2. Create a markdown file with:
   - Clear problem statement
   - Examples with input/output
   - Constraints
   - Your approach/solution
   - Time/space complexity
   - Test cases
3. Include solutions in multiple languages if possible
4. Add notes about what you learned

### When Adding Math Content

1. Explain concepts clearly
2. Include formulas and examples
3. Provide code implementations when applicable
4. Add visualizations or diagrams
5. Link to external resources
6. Create practice problems

### When Adding Experiments

1. Create a dated folder: `YYYY-MM-DD-experiment-name/`
2. Include a README explaining:
   - What you're trying to learn
   - Technologies used
   - Setup instructions
   - Findings and learnings
3. Clean up after 3 months (archive or delete)

## Code Quality

### Python
- Follow PEP 8 style guide
- Use type hints when appropriate
- Write docstrings for functions and classes
- Include examples in docstrings

```python
def fibonacci(n: int) -> list[int]:
    """
    Generate Fibonacci sequence up to n terms.
    
    Args:
        n: Number of terms to generate
        
    Returns:
        List of Fibonacci numbers
        
    Example:
        >>> fibonacci(5)
        [0, 1, 1, 2, 3]
    """
    # Implementation here
```

### JavaScript/TypeScript
- Use ESLint for linting
- Follow Airbnb or Standard style guide
- Use meaningful variable names
- Add JSDoc comments for functions

```javascript
/**
 * Generate Fibonacci sequence up to n terms
 * @param {number} n - Number of terms
 * @returns {number[]} Array of Fibonacci numbers
 * @example
 * fibonacci(5) // [0, 1, 1, 2, 3]
 */
function fibonacci(n) {
    // Implementation here
}
```

### General Guidelines
- **Comment your code** - Explain the "why", not just the "what"
- **Test your solutions** - Verify correctness with test cases
- **Handle edge cases** - Empty inputs, null values, etc.
- **Optimize when needed** - But readability first
- **Learn from mistakes** - Document what didn't work

## Documentation

### Writing Good READMEs

Every directory should have a README that includes:
- Purpose of the directory
- How content is organized
- Getting started guide
- Links to resources

### Code Comments

```python
# Good comment - explains WHY
# Using binary search because array is sorted - O(log n) vs O(n)
result = binary_search(arr, target)

# Bad comment - states the obvious
# Loop through array
for item in arr:
    pass
```

### Learning Notes

When solving problems or learning new concepts, document:
- What you learned
- Challenges you faced
- How you overcame them
- Resources that helped
- What you'd do differently next time

## Version Control

### Commit Messages

Follow conventional commits format:

```
feat: add binary search implementation
fix: correct edge case in fibonacci function
docs: update Python learning roadmap
refactor: simplify two-sum solution
test: add test cases for linked list
```

Types:
- `feat`: New feature or content
- `fix`: Bug fix or correction
- `docs`: Documentation changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

### Branching

For experiments or major additions:
```bash
git checkout -b feature/react-tutorial
git checkout -b experiment/ml-model
git checkout -b topic/system-design
```

Merge back to main when complete.

## Organization Tips

### File Naming
- Use lowercase with hyphens: `two-sum.md`, `binary-search.py`
- Be descriptive: `fibonacci-recursive.js` vs `fib.js`
- Include date for experiments: `2024-10-15-websocket-chat/`

### Directory Structure
Keep it clean and organized:
```
language/
├── basics/           # Fundamentals
├── intermediate/     # More advanced topics
├── advanced/         # Expert level
├── projects/         # Complete projects
└── snippets/         # Reusable code snippets
```

## Learning Strategy

### Daily Practice
1. Pick a topic or problem
2. Study the concept
3. Implement it yourself
4. Test your implementation
5. Document what you learned
6. Commit your work

### Weekly Review
- Review what you learned this week
- Revisit difficult concepts
- Refactor old code
- Update documentation

### Monthly Goals
- Set learning objectives
- Track progress in README
- Celebrate achievements
- Identify areas for improvement

## Resources to Add

When you find a helpful resource:
1. Add it to the appropriate README
2. Include why it's helpful
3. Note your personal rating
4. Keep the list curated (quality over quantity)

## Keeping Things Fresh

- **Archive old experiments** after learning from them
- **Update solutions** as you learn better approaches
- **Refactor code** using new techniques
- **Add new languages** as you learn them
- **Remove outdated content** that no longer serves you

## Remember

This repository is for YOUR learning. Customize these guidelines to fit your learning style and needs. The goal is to:
- Learn effectively
- Track your progress
- Build a portfolio of knowledge
- Have fun coding!

Happy learning! 🚀
