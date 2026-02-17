"""Domain ports: abstract interfaces defining contracts for infrastructure adapters.

Each port is an Abstract Base Class (ABC) that the infrastructure layer must
implement. The application layer depends only on these abstractions, never on
concrete infrastructure classes. This enforces the Dependency Inversion Principle
and enables environment-based adapter substitution without changing business logic.
"""
