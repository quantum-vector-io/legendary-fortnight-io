# Linear Algebra - Vectors and Matrices

## Vectors

A vector is an ordered list of numbers representing magnitude and direction.

### Vector Operations

#### Addition
```
v = [1, 2, 3]
w = [4, 5, 6]
v + w = [5, 7, 9]
```

#### Scalar Multiplication
```
v = [1, 2, 3]
2 * v = [2, 4, 6]
```

#### Dot Product
```
v · w = v₁w₁ + v₂w₂ + ... + vₙwₙ
[1, 2, 3] · [4, 5, 6] = 1*4 + 2*5 + 3*6 = 32
```

#### Magnitude (Length)
```
||v|| = √(v₁² + v₂² + ... + vₙ²)
||[3, 4]|| = √(9 + 16) = 5
```

### Python Implementation

```python
import math

class Vector:
    def __init__(self, components):
        self.components = components
    
    def __add__(self, other):
        """Vector addition."""
        return Vector([a + b for a, b in zip(self.components, other.components)])
    
    def __mul__(self, scalar):
        """Scalar multiplication."""
        return Vector([scalar * x for x in self.components])
    
    def dot(self, other):
        """Dot product."""
        return sum(a * b for a, b in zip(self.components, other.components))
    
    def magnitude(self):
        """Vector magnitude."""
        return math.sqrt(sum(x**2 for x in self.components))
    
    def normalize(self):
        """Return unit vector."""
        mag = self.magnitude()
        return Vector([x / mag for x in self.components])
    
    def __repr__(self):
        return f"Vector({self.components})"

# Examples
v = Vector([1, 2, 3])
w = Vector([4, 5, 6])

print(f"v = {v}")
print(f"w = {w}")
print(f"v + w = {v + w}")
print(f"2 * v = {v * 2}")
print(f"v · w = {v.dot(w)}")
print(f"||v|| = {v.magnitude():.2f}")
print(f"normalized v = {v.normalize()}")
```

## Matrices

A matrix is a rectangular array of numbers.

### Matrix Operations

#### Addition
```
A = [[1, 2],    B = [[5, 6],    A + B = [[6, 8],
     [3, 4]]         [7, 8]]             [10, 12]]
```

#### Scalar Multiplication
```
2 * A = [[2, 4],
         [6, 8]]
```

#### Matrix Multiplication
```
A (m×n) × B (n×p) = C (m×p)
C[i][j] = Σ A[i][k] * B[k][j]
```

#### Transpose
```
A = [[1, 2, 3],    A^T = [[1, 4],
     [4, 5, 6]]            [2, 5],
                           [3, 6]]
```

### Python Implementation

```python
class Matrix:
    def __init__(self, data):
        self.data = data
        self.rows = len(data)
        self.cols = len(data[0]) if data else 0
    
    def __add__(self, other):
        """Matrix addition."""
        result = []
        for i in range(self.rows):
            row = []
            for j in range(self.cols):
                row.append(self.data[i][j] + other.data[i][j])
            result.append(row)
        return Matrix(result)
    
    def __mul__(self, other):
        """Matrix multiplication or scalar multiplication."""
        if isinstance(other, (int, float)):
            # Scalar multiplication
            result = [[other * x for x in row] for row in self.data]
            return Matrix(result)
        else:
            # Matrix multiplication
            result = []
            for i in range(self.rows):
                row = []
                for j in range(other.cols):
                    sum_val = sum(self.data[i][k] * other.data[k][j] 
                                 for k in range(self.cols))
                    row.append(sum_val)
                result.append(row)
            return Matrix(result)
    
    def transpose(self):
        """Matrix transpose."""
        result = [[self.data[j][i] for j in range(self.rows)] 
                  for i in range(self.cols)]
        return Matrix(result)
    
    def __repr__(self):
        return '\n'.join([str(row) for row in self.data])

# Examples
A = Matrix([[1, 2], [3, 4]])
B = Matrix([[5, 6], [7, 8]])

print("Matrix A:")
print(A)
print("\nMatrix B:")
print(B)
print("\nA + B:")
print(A + B)
print("\n2 * A:")
print(A * 2)
print("\nA * B:")
print(A * B)
print("\nTranspose of A:")
print(A.transpose())
```

## Applications in Computer Science

### 1. Computer Graphics
- Transformations (rotation, scaling, translation)
- 3D rendering
- Animation

### 2. Machine Learning
- Neural networks (weights as matrices)
- Principal Component Analysis (PCA)
- Recommendation systems

### 3. Computer Vision
- Image processing (convolution)
- Feature detection
- Object recognition

### 4. Natural Language Processing
- Word embeddings
- Document similarity
- Topic modeling

## Key Concepts to Master

- [ ] Vector operations (addition, dot product, cross product)
- [ ] Matrix operations (multiplication, transpose, inverse)
- [ ] Linear transformations
- [ ] Eigenvalues and eigenvectors
- [ ] Determinants
- [ ] Systems of linear equations
- [ ] Vector spaces and subspaces
- [ ] Orthogonality

## Recommended Resources
- [3Blue1Brown - Essence of Linear Algebra](https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab)
- [MIT OCW 18.06 - Linear Algebra](https://ocw.mit.edu/courses/mathematics/18-06-linear-algebra-spring-2010/)
- [Khan Academy - Linear Algebra](https://www.khanacademy.org/math/linear-algebra)
