// Go Basics - Hello World and Common Patterns
//
// This file demonstrates fundamental Go concepts.
//
// To run: go run basics.go

package main

import (
	"fmt"
	"strings"
)

func main() {
	// 1. Basic printing
	fmt.Println("Hello, World!")

	// 2. Variables and data types
	name := "Learning Lab"
	year := 2025
	isActive := true
	pi := 3.14159

	// 3. String formatting
	fmt.Printf("Welcome to %s!\n", name)
	fmt.Printf("The value of pi is approximately %.2f\n", pi)

	// 4. Slices and loops
	languages := []string{"Go", "Python", "JavaScript", "Java", "Rust"}
	fmt.Println("\nProgramming Languages:")
	for _, lang := range languages {
		fmt.Printf("  - %s\n", lang)
	}

	// 5. Functions
	fmt.Printf("\n%s\n", greet("Go Learner"))

	// 6. Fibonacci
	fibSequence := fibonacci(10)
	fmt.Printf("\nFirst 10 Fibonacci numbers: %v\n", fibSequence)

	// 7. Slices operations
	numbers := []int{1, 2, 3, 4, 5}

	var squares []int
	for _, n := range numbers {
		squares = append(squares, n*n)
	}
	fmt.Printf("\nSquares: %v\n", squares)

	var evens []int
	for _, n := range numbers {
		if n%2 == 0 {
			evens = append(evens, n)
		}
	}
	fmt.Printf("Even numbers: %v\n", evens)

	sum := 0
	for _, n := range numbers {
		sum += n
	}
	fmt.Printf("Sum: %d\n", sum)

	// 8. Maps
	person := map[string]interface{}{
		"name":   "John Doe",
		"age":    30,
		"skills": []string{"Go", "Python", "SQL"},
	}

	skills := person["skills"].([]string)
	fmt.Printf("\nPerson: %s, Skills: %s\n", person["name"], strings.Join(skills, ", "))

	// 9. Structs and methods
	calc := Calculator{}

	fmt.Println("\n" + strings.Repeat("=", 50))
	fmt.Println("Go Basics Examples")
	fmt.Println(strings.Repeat("=", 50))

	fmt.Printf("\nCalculator: 10 + 5 = %d\n", calc.Add(10, 5))
	fmt.Printf("Calculator: 10 - 5 = %d\n", calc.Subtract(10, 5))
	fmt.Printf("Calculator: 10 * 5 = %d\n", calc.Multiply(10, 5))

	// 10. Error handling
	if result, err := calc.Divide(10, 5); err != nil {
		fmt.Printf("Error: %v\n", err)
	} else {
		fmt.Printf("Calculator: 10 / 5 = %.1f\n", result)
	}

	fmt.Printf("\nSafe division: 10 / 2 = ")
	if result, err := safeDivide(10, 2); err != nil {
		fmt.Println(err)
	} else {
		fmt.Printf("%.1f\n", result)
	}

	fmt.Printf("Safe division: 10 / 0 = ")
	if result, err := safeDivide(10, 0); err != nil {
		fmt.Println(err)
	} else {
		fmt.Printf("%.1f\n", result)
	}

	// Unused variables to avoid compile errors
	_ = year
	_ = isActive
}

// greet returns a greeting message
func greet(name string) string {
	return fmt.Sprintf("Hello, %s!", name)
}

// fibonacci generates Fibonacci sequence up to n terms
func fibonacci(n int) []int {
	if n <= 0 {
		return []int{}
	}
	if n == 1 {
		return []int{0}
	}

	fib := []int{0, 1}
	for i := 2; i < n; i++ {
		fib = append(fib, fib[i-1]+fib[i-2])
	}

	return fib
}

// safeDivide performs division with error handling
func safeDivide(a, b int) (float64, error) {
	if b == 0 {
		return 0, fmt.Errorf("cannot divide by zero")
	}
	return float64(a) / float64(b), nil
}

// Calculator is a simple calculator struct
type Calculator struct{}

// Add returns the sum of two integers
func (c Calculator) Add(a, b int) int {
	return a + b
}

// Subtract returns the difference of two integers
func (c Calculator) Subtract(a, b int) int {
	return a - b
}

// Multiply returns the product of two integers
func (c Calculator) Multiply(a, b int) int {
	return a * b
}

// Divide returns the quotient of two integers
func (c Calculator) Divide(a, b int) (float64, error) {
	if b == 0 {
		return 0, fmt.Errorf("cannot divide by zero")
	}
	return float64(a) / float64(b), nil
}
