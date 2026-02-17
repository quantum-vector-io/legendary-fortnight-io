"""Infrastructure layer: concrete adapter implementations for domain ports.

This layer contains all framework, cloud, and database dependencies. Each
sub-package implements one or more domain port interfaces. The application
layer never imports from this package directly; the dependency injection
container (src.config.container) wires adapters to ports at startup.
"""
