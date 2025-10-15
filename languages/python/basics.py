"""
Python Basics - Hello World and Common Patterns

This file demonstrates fundamental Python concepts.
"""

# 1. Basic printing
print("Hello, World!")

# 2. Variables and data types
name = "Learning Lab"
age = 2025
is_active = True
pi = 3.14159

# 3. String formatting
print(f"Welcome to {name}!")
print(f"The value of pi is approximately {pi:.2f}")

# 4. Lists and loops
languages = ["Python", "JavaScript", "Java", "Go", "Rust"]
print("\nProgramming Languages:")
for lang in languages:
    print(f"  - {lang}")

# 5. Functions
def greet(name):
    """Return a greeting message."""
    return f"Hello, {name}!"

def fibonacci(n):
    """Generate Fibonacci sequence up to n terms."""
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib

# 6. List comprehension
squares = [x**2 for x in range(10)]
print(f"\nSquares: {squares}")

# 7. Dictionary
person = {
    "name": "John Doe",
    "age": 30,
    "skills": ["Python", "JavaScript", "SQL"]
}
print(f"\nPerson: {person['name']}, Skills: {', '.join(person['skills'])}")

# 8. Exception handling
def safe_divide(a, b):
    """Safely divide two numbers."""
    try:
        result = a / b
        return result
    except ZeroDivisionError:
        print("Error: Cannot divide by zero!")
        return None
    except TypeError:
        print("Error: Invalid input type!")
        return None

# 9. Class definition
class Calculator:
    """A simple calculator class."""
    
    def add(self, a, b):
        return a + b
    
    def subtract(self, a, b):
        return a - b
    
    def multiply(self, a, b):
        return a * b
    
    def divide(self, a, b):
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

# Main execution
if __name__ == "__main__":
    print("\n" + "="*50)
    print("Python Basics Examples")
    print("="*50)
    
    # Test greeting
    print(f"\n{greet('Python Learner')}")
    
    # Test Fibonacci
    fib_sequence = fibonacci(10)
    print(f"\nFirst 10 Fibonacci numbers: {fib_sequence}")
    
    # Test calculator
    calc = Calculator()
    print(f"\nCalculator: 10 + 5 = {calc.add(10, 5)}")
    print(f"Calculator: 10 - 5 = {calc.subtract(10, 5)}")
    print(f"Calculator: 10 * 5 = {calc.multiply(10, 5)}")
    print(f"Calculator: 10 / 5 = {calc.divide(10, 5)}")
    
    # Test safe divide
    print(f"\nSafe division: 10 / 2 = {safe_divide(10, 2)}")
    print(f"Safe division: 10 / 0 = {safe_divide(10, 0)}")
