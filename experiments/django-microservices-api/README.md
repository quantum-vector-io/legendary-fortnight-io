# Ідеальне Django API: мультисервісна архітектура (Docker + PostgreSQL + AWS + Kubernetes + Load Balancer + Queue)

Це production-oriented шаблон для запуску API-платформи на Django з двома сервісами (`users-service`, `orders-service`), локальним запуском через Docker Compose і хмарним деплоєм в AWS (EKS + ALB + RDS + SQS).

## Що входить
- Мультисервісна архітектура на Django REST Framework.
- Локальна оркестрація: Docker Compose.
- БД: PostgreSQL.
- API Gateway: Nginx.
- Черга: RabbitMQ локально / SQS в AWS.
- Kubernetes маніфести для EKS + ALB Ingress.
- Практична документація з кроками деплою.

## Структура
```text
django-microservices-api/
├── .env.example
├── architecture.md
├── docker-compose.yml
├── k8s/
│   ├── base/
│   └── aws/
├── scripts/
│   └── nginx.conf
└── services/
    ├── users_service/
    └── orders_service/
```

## 1) Локальний запуск
```bash
cd experiments/django-microservices-api
cp .env.example .env
docker compose up --build
```

Після запуску:
- Gateway: `http://localhost:8080`
- Users API health: `http://localhost:8080/users/api/v1/health/`
- Orders API health: `http://localhost:8080/orders/api/v1/health/`
- RabbitMQ UI: `http://localhost:15672` (guest/guest)

## 2) Приклади API-запитів
### Створити користувача
```bash
curl -X POST http://localhost:8080/users/api/v1/users/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo@example.com", "full_name":"Demo User"}'
```

### Створити замовлення
```bash
curl -X POST http://localhost:8080/orders/api/v1/orders/ \
  -H 'Content-Type: application/json' \
  -d '{"user_id":1, "amount":"99.90", "currency":"USD"}'
```

## 3) AWS production blueprint

### Компоненти
- **EKS** — оркестрація контейнерів.
- **ECR** — registry образів.
- **RDS PostgreSQL** — managed база даних.
- **ElastiCache Redis** — кеш/бекенд для воркерів.
- **SQS** — продакшн-черга.
- **ALB** — зовнішній load balancer.
- **CloudWatch + X-Ray/OpenTelemetry** — логування/трейсинг.

### CI/CD (рекомендовано)
1. Лінт + тести.
2. Build Docker images.
3. Push в ECR.
4. `kubectl apply` або Helm deploy в EKS.
5. Smoke tests проти ALB endpoint.

## 4) Kubernetes деплой
```bash
kubectl apply -f k8s/base/namespace.yaml
kubectl apply -f k8s/base/users-deployment.yaml
kubectl apply -f k8s/base/orders-deployment.yaml
kubectl apply -f k8s/base/gateway-deployment.yaml
kubectl apply -f k8s/aws/alb-ingress.yaml
```

## 5) Що додати для production-grade “ідеального API”
- JWT/OAuth2 (Keycloak або Cognito).
- OpenAPI/Swagger (drf-spectacular).
- Rate limiting (Nginx/Envoy + Redis).
- SAGA/outbox pattern для міжсервісних транзакцій.
- Blue/Green або Canary деплой.
- Автоматичне сканування образів (Trivy/Grype).
- Backup/restore стратегії для RDS.

## 6) Нотатки
- У прикладі сервіси використовують спільну PostgreSQL інстанцію для простоти.
- У реальному продакшені рекомендується окрема схема/БД на сервіс + event-driven інтеграція.
- RabbitMQ можна повністю замінити на SQS у production.
