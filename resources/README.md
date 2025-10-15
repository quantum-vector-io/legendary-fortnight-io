# Resources

A curated collection of learning resources, cheat sheets, and references.

## 📚 Learning Platforms

### General Programming
- [freeCodeCamp](https://www.freecodecamp.org/) - Free coding education
- [The Odin Project](https://www.theodinproject.com/) - Full-stack curriculum
- [Codecademy](https://www.codecademy.com/) - Interactive coding lessons
- [Udemy](https://www.udemy.com/) - Video courses (often on sale)
- [Pluralsight](https://www.pluralsight.com/) - Tech skills platform
- [Coursera](https://www.coursera.org/) - University courses online

### Computer Science
- [MIT OpenCourseWare](https://ocw.mit.edu/) - Free MIT course materials
- [Stanford Online](https://online.stanford.edu/) - Stanford courses
- [CS50](https://cs50.harvard.edu/) - Harvard's intro to CS

### Algorithms & Data Structures
- [LeetCode](https://leetcode.com/) - Coding interview prep
- [HackerRank](https://www.hackerrank.com/) - Programming challenges
- [CodeWars](https://www.codewars.com/) - Coding kata
- [AlgoExpert](https://www.algoexpert.io/) - Interview prep (paid)
- [NeetCode](https://neetcode.io/) - Curated problem lists

### Mathematics
- [Khan Academy](https://www.khanacademy.org/) - K-12 through college math
- [Brilliant](https://brilliant.org/) - Interactive STEM learning
- [3Blue1Brown](https://www.youtube.com/c/3blue1brown) - Visual math videos
- [Paul's Online Math Notes](https://tutorial.math.lamar.edu/) - Calculus notes

### System Design
- [System Design Primer](https://github.com/donnemartin/system-design-primer)
- [Grokking the System Design Interview](https://www.educative.io/courses/grokking-the-system-design-interview)
- [High Scalability Blog](http://highscalability.com/)

## 📖 Books

### Programming
- **Clean Code** by Robert C. Martin
- **The Pragmatic Programmer** by Hunt & Thomas
- **Code Complete** by Steve McConnell
- **Refactoring** by Martin Fowler

### Algorithms
- **Introduction to Algorithms (CLRS)** - The classic textbook
- **Algorithm Design Manual** by Steven Skiena
- **Grokking Algorithms** by Aditya Bhargava

### System Design
- **Designing Data-Intensive Applications** by Martin Kleppmann
- **System Design Interview** by Alex Xu (Vol 1 & 2)
- **Building Microservices** by Sam Newman

### Language Specific
- **Fluent Python** by Luciano Ramalho
- **JavaScript: The Good Parts** by Douglas Crockford
- **Effective Java** by Joshua Bloch
- **The Rust Programming Language** (The Book)

## 🎥 YouTube Channels

### Programming
- [Traversy Media](https://www.youtube.com/c/TraversyMedia) - Web development
- [The Net Ninja](https://www.youtube.com/c/TheNetNinja) - Full-stack tutorials
- [Fireship](https://www.youtube.com/c/Fireship) - Quick tech overviews
- [Web Dev Simplified](https://www.youtube.com/c/WebDevSimplified)

### Computer Science
- [CS Dojo](https://www.youtube.com/c/CSDojo)
- [William Fiset](https://www.youtube.com/c/WilliamFiset-videos) - Algorithms
- [Abdul Bari](https://www.youtube.com/c/AbdulBari) - Algorithms

### System Design
- [Gaurav Sen](https://www.youtube.com/c/GauravSensei)
- [System Design Interview](https://www.youtube.com/c/SystemDesignInterview)

## 🛠️ Tools & Utilities

### Editors & IDEs
- [VS Code](https://code.visualstudio.com/)
- [JetBrains IDEs](https://www.jetbrains.com/)
- [Vim](https://www.vim.org/) / [Neovim](https://neovim.io/)

### Version Control
- [Git](https://git-scm.com/)
- [GitHub](https://github.com/)
- [Pro Git Book](https://git-scm.com/book/en/v2)

### Documentation
- [DevDocs](https://devdocs.io/) - API documentation browser
- [MDN Web Docs](https://developer.mozilla.org/)
- [Stack Overflow](https://stackoverflow.com/)

### Practice & Challenges
- [Project Euler](https://projecteuler.net/) - Math + programming
- [Advent of Code](https://adventofcode.com/) - December coding challenges
- [Exercism](https://exercism.org/) - Code practice with mentorship

## 📝 Cheat Sheets

### Git
```bash
# Basic commands
git init                    # Initialize repository
git clone <url>            # Clone repository
git status                 # Check status
git add .                  # Stage all changes
git commit -m "message"    # Commit changes
git push                   # Push to remote
git pull                   # Pull from remote

# Branching
git branch <name>          # Create branch
git checkout <branch>      # Switch branch
git checkout -b <branch>   # Create and switch
git merge <branch>         # Merge branch
git branch -d <branch>     # Delete branch

# History
git log                    # View history
git log --oneline          # Compact history
git diff                   # View changes
```

### Vim
```
# Modes
i                    # Insert mode
Esc                  # Normal mode
:                    # Command mode

# Navigation
h, j, k, l          # Left, down, up, right
w                    # Next word
b                    # Previous word
0                    # Start of line
$                    # End of line
gg                   # Start of file
G                    # End of file

# Editing
dd                   # Delete line
yy                   # Copy line
p                    # Paste
u                    # Undo
Ctrl+r               # Redo

# Save & Quit
:w                   # Save
:q                   # Quit
:wq                  # Save and quit
:q!                  # Quit without saving
```

### Python
```python
# List comprehension
[x**2 for x in range(10)]
[x for x in range(10) if x % 2 == 0]

# Dictionary comprehension
{k: v for k, v in zip(keys, values)}

# Lambda functions
lambda x: x**2
map(lambda x: x**2, [1, 2, 3])
filter(lambda x: x % 2 == 0, [1, 2, 3, 4])

# String formatting
f"Hello {name}"
"Hello {}".format(name)

# File operations
with open('file.txt', 'r') as f:
    content = f.read()
```

### JavaScript
```javascript
// Array methods
arr.map(x => x * 2)
arr.filter(x => x > 0)
arr.reduce((acc, x) => acc + x, 0)
arr.forEach(x => console.log(x))

// Destructuring
const {name, age} = person
const [first, second] = array

// Spread operator
const newArr = [...arr1, ...arr2]
const newObj = {...obj1, ...obj2}

// Async/await
async function fetchData() {
  const response = await fetch(url)
  const data = await response.json()
  return data
}

// Arrow functions
const add = (a, b) => a + b
```

## 🔗 Useful Links

### Communities
- [Reddit /r/learnprogramming](https://www.reddit.com/r/learnprogramming/)
- [Reddit /r/cscareerquestions](https://www.reddit.com/r/cscareerquestions/)
- [Dev.to](https://dev.to/)
- [Hashnode](https://hashnode.com/)

### Roadmaps
- [roadmap.sh](https://roadmap.sh/) - Developer roadmaps
- [GitHub Skills](https://skills.github.com/) - GitHub learning paths

### Interview Prep
- [Tech Interview Handbook](https://www.techinterviewhandbook.org/)
- [Coding Interview University](https://github.com/jwasham/coding-interview-university)

## 💡 Tips

1. **Learn by doing** - Build projects, not just tutorials
2. **Read documentation** - Official docs are often the best resource
3. **Join communities** - Ask questions, help others
4. **Practice daily** - Consistency beats intensity
5. **Build in public** - Share your learning journey
6. **Review regularly** - Spaced repetition works

## 📅 Stay Updated

- Follow developers on Twitter/X
- Subscribe to newsletters (JavaScript Weekly, Python Weekly, etc.)
- Read tech blogs (Medium, Dev.to, Hashnode)
- Watch conference talks
- Listen to programming podcasts

---

Remember: The best resource is the one you actually use! Start with one or two and expand as needed.
