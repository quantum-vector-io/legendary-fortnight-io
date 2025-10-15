# Go Learning Path

## Getting Started

### Setup
```bash
# Check Go version
go version

# Download and install Go
# https://go.dev/dl/

# Set up workspace (Go modules - recommended)
go mod init myproject

# Install dependencies
go get github.com/gorilla/mux  # Example: web router
```

## Topics to Cover

### Basics
- [ ] Variables and constants
- [ ] Data types
- [ ] Control flow (if, for, switch)
- [ ] Functions
- [ ] Arrays and slices
- [ ] Maps
- [ ] Pointers

### Intermediate
- [ ] Structs and methods
- [ ] Interfaces
- [ ] Error handling
- [ ] Goroutines (concurrency)
- [ ] Channels
- [ ] Defer, panic, recover
- [ ] Packages and modules

### Advanced
- [ ] Context package
- [ ] Sync package (mutexes, wait groups)
- [ ] Testing and benchmarks
- [ ] Generics (Go 1.18+)
- [ ] Build tags
- [ ] Reflection
- [ ] CGO

## Project Ideas
1. CLI tool (file processor, task manager)
2. REST API server
3. Concurrent web scraper
4. Microservice
5. Chat server with goroutines
6. Database-backed application
7. Container orchestration tool

## Useful Libraries
- **Web**: Gin, Echo, Gorilla Mux, Fiber
- **Database**: GORM, sqlx, pgx
- **Testing**: testify, gomock
- **CLI**: Cobra, urfave/cli
- **Logging**: zap, logrus
- **HTTP**: net/http (standard library)

## Running Go Programs
```bash
# Run directly
go run main.go

# Build executable
go build -o myapp main.go

# Run executable
./myapp

# Format code
go fmt ./...

# Run tests
go test ./...

# Install dependencies
go mod tidy
```

## Resources
- [Go by Example](https://gobyexample.com/)
- [Effective Go](https://go.dev/doc/effective_go)
- [Go Documentation](https://go.dev/doc/)
- [A Tour of Go](https://go.dev/tour/)
