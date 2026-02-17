# Django Microservices API Architecture

## Services
- **API Gateway (Nginx)**: routes requests to internal services (`/users/*`, `/orders/*`).
- **users-service (Django + DRF)**: owns user profile lifecycle.
- **orders-service (Django + DRF)**: owns order creation/read model.
- **PostgreSQL**: relational persistence (service-owned schemas recommended in production).
- **Redis**: cache + Celery result backend.
- **RabbitMQ / AWS SQS**: async queue for background jobs and eventual consistency events.

## Cross-cutting concerns
- JWT auth at gateway + internal token verification.
- OpenTelemetry tracing in every service.
- Centralized logs to CloudWatch.
- Contract-first API (OpenAPI).

## Recommended production topology (AWS)
1. Source control + CI/CD (GitHub Actions).
2. Build images and push to ECR.
3. Deploy to EKS by Helm.
4. ALB Ingress Controller exposes gateway service.
5. RDS PostgreSQL (Multi-AZ) + ElastiCache Redis.
6. SQS queues for events and retries.

## Queue pattern
- `order.created` event emitted by orders-service.
- users-service consumes asynchronously (e.g. for user statistics/notifications).
- Dead-letter queues for poison messages.
