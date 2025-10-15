# Java Learning Path

## Getting Started

### Setup
```bash
# Check Java version
java --version

# Check compiler version
javac --version

# Download and install Java Development Kit (JDK)
# Latest version: https://www.oracle.com/java/technologies/downloads/

# Set JAVA_HOME environment variable (if needed)
# On Linux/macOS:
export JAVA_HOME=/path/to/jdk
# On Windows:
# set JAVA_HOME=C:\Program Files\Java\jdk-XX
```

### Build Tools
```bash
# Maven
mvn --version
# Download: https://maven.apache.org/

# Gradle
gradle --version
# Download: https://gradle.org/
```

## Topics to Cover

### Basics
- [ ] Variables and data types
- [ ] Control flow (if/else, switch, loops)
- [ ] Methods
- [ ] Arrays
- [ ] Strings
- [ ] Input/Output

### Object-Oriented Programming
- [ ] Classes and objects
- [ ] Inheritance
- [ ] Polymorphism
- [ ] Abstraction
- [ ] Encapsulation
- [ ] Interfaces
- [ ] Abstract classes

### Intermediate
- [ ] Collections (List, Set, Map)
- [ ] Generics
- [ ] Exception handling
- [ ] File I/O
- [ ] Serialization
- [ ] Multithreading
- [ ] Lambda expressions

### Advanced
- [ ] Streams API
- [ ] Functional programming
- [ ] Design patterns
- [ ] JDBC (database connectivity)
- [ ] JUnit testing
- [ ] Spring Framework
- [ ] JavaFX (GUI)

## Project Ideas
1. Banking system
2. Student management system
3. Library management system
4. REST API with Spring Boot
5. Android app (with Android SDK)
6. Multithreaded chat server
7. E-commerce backend

## Useful Libraries
- **Collections**: ArrayList, HashMap, TreeSet
- **Web**: Spring Boot, Spring MVC, Servlet API
- **Testing**: JUnit, Mockito, TestNG
- **Database**: JDBC, Hibernate, JPA
- **Utilities**: Apache Commons, Guava
- **Logging**: Log4j, SLF4J

## Compilation and Execution
```bash
# Compile a Java file
javac HelloWorld.java

# Run the compiled class
java HelloWorld

# Compile with dependencies
javac -cp "lib/*" MyProgram.java

# Run with dependencies
java -cp ".:lib/*" MyProgram
```

## Resources
- [Oracle Java Tutorials](https://docs.oracle.com/javase/tutorial/)
- [Java Documentation](https://docs.oracle.com/en/java/)
- [Baeldung](https://www.baeldung.com/) - Java tutorials
- [Effective Java](https://www.oreilly.com/library/view/effective-java/9780134686097/) - Best practices book
