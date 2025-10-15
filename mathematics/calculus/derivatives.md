# Calculus - Derivatives

## Introduction

A derivative represents the rate of change of a function. Geometrically, it's the slope of the tangent line to a curve at a point.

## Definition

The derivative of f(x) at point x is:

```
f'(x) = lim(h→0) [f(x+h) - f(x)] / h
```

## Basic Derivative Rules

### Power Rule
```
d/dx(x^n) = n * x^(n-1)

Examples:
d/dx(x²) = 2x
d/dx(x³) = 3x²
d/dx(√x) = d/dx(x^(1/2)) = (1/2)x^(-1/2) = 1/(2√x)
```

### Constant Rule
```
d/dx(c) = 0

Example:
d/dx(5) = 0
```

### Constant Multiple Rule
```
d/dx(c·f(x)) = c·f'(x)

Example:
d/dx(3x²) = 3·2x = 6x
```

### Sum/Difference Rule
```
d/dx[f(x) ± g(x)] = f'(x) ± g'(x)

Example:
d/dx(x² + 3x) = 2x + 3
```

### Product Rule
```
d/dx[f(x)·g(x)] = f'(x)·g(x) + f(x)·g'(x)

Example:
d/dx(x²·sin(x)) = 2x·sin(x) + x²·cos(x)
```

### Quotient Rule
```
d/dx[f(x)/g(x)] = [f'(x)·g(x) - f(x)·g'(x)] / [g(x)]²

Example:
d/dx(sin(x)/x) = [cos(x)·x - sin(x)·1] / x²
```

### Chain Rule
```
d/dx[f(g(x))] = f'(g(x))·g'(x)

Example:
d/dx(sin(x²)) = cos(x²)·2x = 2x·cos(x²)
```

## Common Derivatives

```
d/dx(sin(x)) = cos(x)
d/dx(cos(x)) = -sin(x)
d/dx(tan(x)) = sec²(x)
d/dx(e^x) = e^x
d/dx(ln(x)) = 1/x
d/dx(a^x) = a^x·ln(a)
```

## Python Implementation

```python
import numpy as np
import matplotlib.pyplot as plt

def numerical_derivative(f, x, h=1e-5):
    """
    Compute numerical derivative using finite differences.
    
    Args:
        f: Function to differentiate
        x: Point at which to compute derivative
        h: Small step size
        
    Returns:
        Approximate derivative f'(x)
    """
    return (f(x + h) - f(x - h)) / (2 * h)

# Example functions and their derivatives
def f(x):
    """f(x) = x²"""
    return x**2

def f_prime(x):
    """f'(x) = 2x"""
    return 2*x

def g(x):
    """g(x) = sin(x)"""
    return np.sin(x)

def g_prime(x):
    """g'(x) = cos(x)"""
    return np.cos(x)

# Test numerical derivative
x = 2.0
print(f"Numerical derivative of x² at x={x}: {numerical_derivative(f, x):.6f}")
print(f"Analytical derivative: {f_prime(x):.6f}")

x = np.pi/4
print(f"\nNumerical derivative of sin(x) at x=π/4: {numerical_derivative(g, x):.6f}")
print(f"Analytical derivative: {g_prime(x):.6f}")

# Visualize function and its derivative
x_values = np.linspace(-2, 2, 100)

plt.figure(figsize=(12, 5))

# Plot x²
plt.subplot(1, 2, 1)
plt.plot(x_values, f(x_values), label='f(x) = x²', linewidth=2)
plt.plot(x_values, f_prime(x_values), label="f'(x) = 2x", linewidth=2)
plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)
plt.grid(True, alpha=0.3)
plt.legend()
plt.title('Quadratic Function and Its Derivative')

# Plot sin(x)
x_values_2 = np.linspace(-2*np.pi, 2*np.pi, 100)
plt.subplot(1, 2, 2)
plt.plot(x_values_2, g(x_values_2), label='g(x) = sin(x)', linewidth=2)
plt.plot(x_values_2, g_prime(x_values_2), label="g'(x) = cos(x)", linewidth=2)
plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)
plt.grid(True, alpha=0.3)
plt.legend()
plt.title('Sine Function and Its Derivative')

plt.tight_layout()
plt.savefig('derivatives.png', dpi=100, bbox_inches='tight')
print("\nPlot saved as derivatives.png")
```

## Applications

### 1. Optimization
Finding maximum/minimum values:
- Set f'(x) = 0
- Solve for x (critical points)
- Use second derivative test

### 2. Physics
- Velocity = derivative of position
- Acceleration = derivative of velocity
- Rate of change in any physical quantity

### 3. Machine Learning
- Gradient descent optimization
- Backpropagation in neural networks
- Computing gradients for loss functions

### 4. Economics
- Marginal cost/revenue
- Rate of change in demand
- Optimization of profit

## Practice Problems

1. Find f'(x) for f(x) = 3x⁴ - 2x² + 5
2. Find f'(x) for f(x) = (x² + 1)(x³ - 2)
3. Find f'(x) for f(x) = sin(3x²)
4. Find f'(x) for f(x) = e^(x²)
5. Find the equation of the tangent line to y = x³ at x = 2

## Solutions

```python
# 1. f(x) = 3x⁴ - 2x² + 5
# f'(x) = 12x³ - 4x

# 2. f(x) = (x² + 1)(x³ - 2)  [Product rule]
# f'(x) = 2x(x³ - 2) + (x² + 1)(3x²)
#       = 2x⁴ - 4x + 3x⁴ + 3x²
#       = 5x⁴ + 3x² - 4x

# 3. f(x) = sin(3x²)  [Chain rule]
# f'(x) = cos(3x²) · 6x = 6x·cos(3x²)

# 4. f(x) = e^(x²)  [Chain rule]
# f'(x) = e^(x²) · 2x = 2x·e^(x²)

# 5. Tangent line to y = x³ at x = 2
# y' = 3x², at x=2: y'(2) = 12
# Point: (2, 8)
# Equation: y - 8 = 12(x - 2)
#           y = 12x - 16
```

## Key Concepts to Master

- [ ] Definition and geometric interpretation
- [ ] All derivative rules
- [ ] Common function derivatives
- [ ] Higher-order derivatives
- [ ] Implicit differentiation
- [ ] Related rates
- [ ] Optimization problems
- [ ] L'Hôpital's rule

## Resources
- [Khan Academy - Calculus](https://www.khanacademy.org/math/calculus-1)
- [3Blue1Brown - Essence of Calculus](https://www.youtube.com/playlist?list=PLZHQObOWTQDMsr9K-rj53DwVRMYO3t5Yr)
- [Paul's Online Math Notes](https://tutorial.math.lamar.edu/)
