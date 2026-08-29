# Enterprise Architecture Guidelines (Engineering Department)

## 1. Microservice Communication Protocols
All internal microservices in the engineering ecosystem must communicate asynchronously using Kafka events for telemetry and gRPC over HTTP/2 for synchronous RPCs. Direct synchronous REST communication between internal services is deprecated.

## 2. Payment Service Resilience Standards
The payment processing service enforces strict fault-tolerance standards:
- **Maximum Retry Limit**: 3 retry attempts before falling back to dead-letter queue (DLQ).
- **Backoff Strategy**: Exponential backoff with a multiplier of 2.0 and initial delay of 500ms.
- **Circuit Breaker**: Trips after 5 consecutive 5xx errors within a 10-second rolling window.

## 3. Database Scaling & Partitioning
Engineering teams must partition time-series databases by month. Read replicas must be scaled out when CPU utilization exceeds 70% for more than 15 consecutive minutes.
