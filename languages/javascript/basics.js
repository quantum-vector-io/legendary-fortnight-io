/**
 * JavaScript Basics - Hello World and Common Patterns
 * 
 * This file demonstrates fundamental JavaScript concepts.
 */

// 1. Console logging
console.log("Hello, World!");

// 2. Variables and data types
const name = "Learning Lab";
let year = 2025;
const isActive = true;
const pi = 3.14159;

// 3. Template literals
console.log(`Welcome to ${name}!`);
console.log(`The value of pi is approximately ${pi.toFixed(2)}`);

// 4. Arrays and iteration
const languages = ["JavaScript", "Python", "Java", "Go", "Rust"];
console.log("\nProgramming Languages:");
languages.forEach(lang => console.log(`  - ${lang}`));

// 5. Functions
function greet(name) {
  return `Hello, ${name}!`;
}

// Arrow function
const fibonacci = (n) => {
  if (n <= 0) return [];
  if (n === 1) return [0];
  
  const fib = [0, 1];
  for (let i = 2; i < n; i++) {
    fib.push(fib[i-1] + fib[i-2]);
  }
  return fib;
};

// 6. Array methods
const numbers = [1, 2, 3, 4, 5];
const squares = numbers.map(x => x ** 2);
const evens = numbers.filter(x => x % 2 === 0);
const sum = numbers.reduce((acc, x) => acc + x, 0);

console.log(`\nSquares: ${squares}`);
console.log(`Even numbers: ${evens}`);
console.log(`Sum: ${sum}`);

// 7. Objects and destructuring
const person = {
  name: "John Doe",
  age: 30,
  skills: ["JavaScript", "Python", "SQL"]
};

const { name: personName, skills } = person;
console.log(`\nPerson: ${personName}, Skills: ${skills.join(", ")}`);

// 8. Error handling
function safeDivide(a, b) {
  try {
    if (b === 0) {
      throw new Error("Cannot divide by zero");
    }
    return a / b;
  } catch (error) {
    console.error(`Error: ${error.message}`);
    return null;
  }
}

// 9. Classes
class Calculator {
  add(a, b) {
    return a + b;
  }
  
  subtract(a, b) {
    return a - b;
  }
  
  multiply(a, b) {
    return a * b;
  }
  
  divide(a, b) {
    if (b === 0) {
      throw new Error("Cannot divide by zero");
    }
    return a / b;
  }
}

// 10. Promises and async/await
async function fetchData(url) {
  try {
    // Simulated API call
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({ data: "Sample data from " + url });
      }, 1000);
    });
  } catch (error) {
    console.error("Error fetching data:", error);
  }
}

// Main execution
(async function main() {
  console.log("\n" + "=".repeat(50));
  console.log("JavaScript Basics Examples");
  console.log("=".repeat(50));
  
  // Test greeting
  console.log(`\n${greet("JavaScript Learner")}`);
  
  // Test Fibonacci
  const fibSequence = fibonacci(10);
  console.log(`\nFirst 10 Fibonacci numbers: ${fibSequence}`);
  
  // Test calculator
  const calc = new Calculator();
  console.log(`\nCalculator: 10 + 5 = ${calc.add(10, 5)}`);
  console.log(`Calculator: 10 - 5 = ${calc.subtract(10, 5)}`);
  console.log(`Calculator: 10 * 5 = ${calc.multiply(10, 5)}`);
  console.log(`Calculator: 10 / 5 = ${calc.divide(10, 5)}`);
  
  // Test safe divide
  console.log(`\nSafe division: 10 / 2 = ${safeDivide(10, 2)}`);
  console.log(`Safe division: 10 / 0 = ${safeDivide(10, 0)}`);
  
  // Test async function
  console.log("\nFetching data...");
  const result = await fetchData("https://api.example.com");
  console.log(result);
})();

// Export for use in other files (CommonJS)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { greet, fibonacci, Calculator, safeDivide };
}
