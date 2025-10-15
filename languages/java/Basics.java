/**
 * Java Basics - Hello World and Common Patterns
 * 
 * This file demonstrates fundamental Java concepts.
 * 
 * To compile: javac Basics.java
 * To run: java Basics
 */

import java.util.*;
import java.util.stream.*;

public class Basics {
    
    // 1. Main method - entry point
    public static void main(String[] args) {
        System.out.println("Hello, World!");
        
        // 2. Variables and data types
        String name = "Learning Lab";
        int year = 2025;
        boolean isActive = true;
        double pi = 3.14159;
        
        // 3. String formatting
        System.out.println("Welcome to " + name + "!");
        System.out.printf("The value of pi is approximately %.2f%n", pi);
        
        // 4. Arrays and loops
        String[] languages = {"Java", "Python", "JavaScript", "Go", "Rust"};
        System.out.println("\nProgramming Languages:");
        for (String lang : languages) {
            System.out.println("  - " + lang);
        }
        
        // 5. Method calls
        System.out.println("\n" + greet("Java Learner"));
        
        // 6. Fibonacci
        List<Integer> fibSequence = fibonacci(10);
        System.out.println("\nFirst 10 Fibonacci numbers: " + fibSequence);
        
        // 7. Collections and Streams
        List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);
        List<Integer> squares = numbers.stream()
            .map(x -> x * x)
            .collect(Collectors.toList());
        System.out.println("\nSquares: " + squares);
        
        List<Integer> evens = numbers.stream()
            .filter(x -> x % 2 == 0)
            .collect(Collectors.toList());
        System.out.println("Even numbers: " + evens);
        
        int sum = numbers.stream()
            .reduce(0, Integer::sum);
        System.out.println("Sum: " + sum);
        
        // 8. HashMap
        Map<String, Object> person = new HashMap<>();
        person.put("name", "John Doe");
        person.put("age", 30);
        person.put("skills", Arrays.asList("Java", "Python", "SQL"));
        
        System.out.println("\nPerson: " + person.get("name") + 
            ", Skills: " + person.get("skills"));
        
        // 9. Calculator class
        Calculator calc = new Calculator();
        System.out.println("\n" + "=".repeat(50));
        System.out.println("Java Basics Examples");
        System.out.println("=".repeat(50));
        
        System.out.println("\nCalculator: 10 + 5 = " + calc.add(10, 5));
        System.out.println("Calculator: 10 - 5 = " + calc.subtract(10, 5));
        System.out.println("Calculator: 10 * 5 = " + calc.multiply(10, 5));
        System.out.println("Calculator: 10 / 5 = " + calc.divide(10, 5));
        
        // 10. Exception handling
        System.out.println("\nSafe division: 10 / 2 = " + safeDivide(10, 2));
        System.out.println("Safe division: 10 / 0 = " + safeDivide(10, 0));
    }
    
    // Method to greet
    public static String greet(String name) {
        return "Hello, " + name + "!";
    }
    
    // Fibonacci method
    public static List<Integer> fibonacci(int n) {
        if (n <= 0) return new ArrayList<>();
        if (n == 1) return Arrays.asList(0);
        
        List<Integer> fib = new ArrayList<>();
        fib.add(0);
        fib.add(1);
        
        for (int i = 2; i < n; i++) {
            fib.add(fib.get(i-1) + fib.get(i-2));
        }
        
        return fib;
    }
    
    // Safe division with exception handling
    public static Double safeDivide(int a, int b) {
        try {
            if (b == 0) {
                throw new ArithmeticException("Cannot divide by zero");
            }
            return (double) a / b;
        } catch (ArithmeticException e) {
            System.out.println("Error: " + e.getMessage());
            return null;
        }
    }
}

// Calculator class
class Calculator {
    public int add(int a, int b) {
        return a + b;
    }
    
    public int subtract(int a, int b) {
        return a - b;
    }
    
    public int multiply(int a, int b) {
        return a * b;
    }
    
    public double divide(int a, int b) {
        if (b == 0) {
            throw new ArithmeticException("Cannot divide by zero");
        }
        return (double) a / b;
    }
}
