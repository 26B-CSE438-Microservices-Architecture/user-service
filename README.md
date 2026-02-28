# User Service

> **CSE 438 – Microservice Architecture | Spring 2026**
> Term Project: Trendyol Go Clone — User Team

---

## Overview

The User Service is the single source of truth for **user profile and account data** across the Trendyol Go platform. It owns the `User` bounded context — managing user registration, profile information, roles, and delivery addresses.

> **Note:** Authentication (login, JWT issuance, token validation) is **not** the responsibility of this service. That concern belongs to the **Gateway/Auth Service**. This service exposes user data; the Gateway/Auth service controls access to it.

---

## Responsibilities

- User registration (creating accounts)
- Storing and managing user profile data (name, email, phone)
- Role assignment: `CUSTOMER`, `RESTAURANT_OWNER`, `COURIER`, `ADMIN`
- Delivery address book management per user
- Providing user data to other services via internal API
- Publishing user lifecycle domain events

---

## Requirements

### Functional Requirements

| # | Requirement |
|---|-------------|
| FR-01 | A new user can register with name, email, phone number, password, and role |
| FR-02 | Passwords are stored securely (hashed — handled by this service before persistence) |
| FR-03 | Users can view their own profile |
| FR-04 | Users can update their profile fields (name, phone) |
| FR-05 | Users can add, list, and delete delivery addresses |
| FR-06 | Admins can list, deactivate, or delete any user account |
| FR-07 | Other services can fetch a user's basic info by user ID via an internal endpoint |
| FR-08 | The service publishes domain events when a user is created, updated, or deactivated |
| FR-09 | Email and phone number must be unique across all users |
| FR-10 | A user's role determines what actions they can perform across the platform |

### Non-Functional Requirements

| # | Requirement |
|---|-------------|
| NFR-01 | Passwords must be hashed with bcrypt (cost factor ≥ 12) before storage |
| NFR-02 | Service must be independently deployable and horizontally scalable |
| NFR-03 | PII fields (email, phone) should be encrypted at rest |
| NFR-04 | Structured JSON logging with trace/correlation IDs on every log line |
| NFR-05 | Health check endpoints for Kubernetes liveness and readiness probes |
| NFR-06 | Internal user lookup must respond in < 50 ms (p99) |
| NFR-07 | All communication with other services follows shared API style and auth conventions |

---

## API Interfaces

> Public base path: `/api/v1/users`
> Internal base path: `/internal/v1/users`
> All request/response bodies are `application/json`
> Public endpoints expect the Gateway/Auth service to forward a verified `X-User-Id` and `X-User-Role` header — this service does **not** validate JWTs directly.

---

### Public Endpoints

#### `POST /api/v1/users/register`
Register a new user. This is the only unauthenticated public endpoint on this service.

**Request Body:**
```json
{
  "name": "Ali Veli",
  "email": "ali@example.com",
  "phone": "+905551234567",
  "password": "SecurePass123!",
  "role": "CUSTOMER"
}
```

**Response `201 Created`:**
```json
{
  "id": "uuid",
  "name": "Ali Veli",
  "email": "ali@example.com",
  "phone": "+905551234567",
  "role": "CUSTOMER",
  "createdAt": "2026-03-01T10:00:00Z"
}
```

**Error cases:** `409 Conflict` if email or phone already exists.

---

#### `GET /api/v1/users/me`
Get the authenticated user's own profile.
Headers: `X-User-Id: uuid`, `X-User-Role: CUSTOMER` (injected by Gateway)

**Response `200 OK`:**
```json
{
  "id": "uuid",
  "name": "Ali Veli",
  "email": "ali@example.com",
  "phone": "+905551234567",
  "role": "CUSTOMER",
  "active": true,
  "addresses": [
    {
      "id": "uuid",
      "label": "Home",
      "street": "Atatürk Cad. No:5",
      "city": "Antalya",
      "postalCode": "07100",
      "lat": 36.8969,
      "lng": 30.7133
    }
  ],
  "createdAt": "2026-03-01T10:00:00Z"
}
```

---

#### `PUT /api/v1/users/me`
Update the authenticated user's own profile (name, phone only — email changes require a separate flow).

**Request Body (partial update):**
```json
{
  "name": "Ali Veli Updated",
  "phone": "+905559876543"
}
```

**Response `200 OK`:** *(updated user object)*

---

#### `POST /api/v1/users/me/addresses`
Add a new delivery address to the authenticated user's address book.

**Request Body:**
```json
{
  "label": "Home",
  "street": "Atatürk Cad. No:5",
  "city": "Antalya",
  "postalCode": "07100",
  "lat": 36.8969,
  "lng": 30.7133
}
```

**Response `201 Created`:**
```json
{
  "id": "uuid",
  "label": "Home",
  "street": "Atatürk Cad. No:5",
  "city": "Antalya",
  "postalCode": "07100",
  "lat": 36.8969,
  "lng": 30.7133
}
```

---

#### `GET /api/v1/users/me/addresses`
List all saved addresses of the authenticated user.

**Response `200 OK`:** *(array of address objects)*

---

#### `DELETE /api/v1/users/me/addresses/{addressId}`
Remove a delivery address.

**Response `204 No Content`**

---

### Internal Endpoints (Service-to-Service Only)

These endpoints are **not exposed through the API Gateway**. They are only reachable within the Kubernetes cluster network by trusted services.

#### `GET /internal/v1/users/{userId}`
Fetch basic user profile by ID. Used by Order, Courier, Payment, and Notification services.

**Response `200 OK`:**
```json
{
  "id": "uuid",
  "name": "Ali Veli",
  "email": "ali@example.com",
  "phone": "+905551234567",
  "role": "CUSTOMER",
  "active": true
}
```

**Response `404 Not Found`** if user does not exist.

---

#### `POST /internal/v1/users/lookup`
Bulk fetch multiple users by a list of IDs (used by Order or Restaurant services for batch operations).

**Request Body:**
```json
{
  "userIds": ["uuid1", "uuid2", "uuid3"]
}
```

**Response `200 OK`:**
```json
{
  "users": [
    { "id": "uuid1", "name": "...", "role": "CUSTOMER", "active": true },
    { "id": "uuid2", "name": "...", "role": "COURIER", "active": true }
  ]
}
```

---

#### `GET /internal/v1/users/by-email?email={email}`
Look up a user by email address. Used by the **Gateway/Auth service** during the login flow to retrieve the user record (including hashed password) for credential verification.

**Response `200 OK`:**
```json
{
  "id": "uuid",
  "email": "ali@example.com",
  "hashedPassword": "$2b$12$...",
  "role": "CUSTOMER",
  "active": true
}
```

> ⚠️ This endpoint returns sensitive data and must only be called by the Gateway/Auth service within the cluster.

---

### Admin Endpoints

> Require `X-User-Role: ADMIN` header forwarded by the Gateway.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/admin/users` | List all users (paginated, filterable by role/status) |
| `GET` | `/api/v1/admin/users/{id}` | Get any user by ID |
| `PATCH` | `/api/v1/admin/users/{id}/deactivate` | Soft delete — marks user as deleted (`deletedAt` timestamp set, data retained) |
| `PATCH` | `/api/v1/admin/users/{id}/activate` | Re-activate a user account |

> ℹ️ **No hard delete.** User records are never physically removed from the database. This preserves referential integrity for historical Order, Payment, and Courier records that reference a `userId`. A soft-deleted user cannot log in and is excluded from all normal queries, but their data remains intact.

---

## Domain Events Published

The User Service publishes these events to the message broker (e.g., Kafka). Other services subscribe as needed.

| Event | Topic | Trigger |
|-------|-------|---------|
| `UserRegistered` | `user.registered` | New user successfully created |
| `UserUpdated` | `user.updated` | Profile fields changed |
| `UserDeactivated` | `user.deactivated` | Admin soft-deletes or deactivates an account |
| `UserReactivated` | `user.reactivated` | Admin re-activates a previously deactivated account |

**`UserRegistered` Payload Example:**
```json
{
  "eventId": "uuid",
  "eventType": "UserRegistered",
  "timestamp": "2026-03-01T10:00:00Z",
  "data": {
    "userId": "uuid",
    "name": "Ali Veli",
    "email": "ali@example.com",
    "role": "CUSTOMER"
  }
}
```

---

## Inter-Service Dependencies

| Service | Direction | Communication | Purpose |
|---------|-----------|---------------|---------|
| Gateway/Auth | Inbound | Internal HTTP (`/internal/v1/users/by-email`) | Credential lookup during login |
| Gateway/Auth | Inbound | Public HTTP (proxied) | Routes authenticated requests with user headers |
| Order Service | Inbound | Internal HTTP (`/internal/v1/users/{id}`) | Fetch customer info for orders |
| Payment Service | Inbound | Internal HTTP (`/internal/v1/users/{id}`) | Fetch billing info |
| Restaurant Service | Inbound | Internal HTTP (`/internal/v1/users/{id}`) | Fetch restaurant owner info |

---

## Tech Stack (Proposed)

| Concern | Choice |
|---------|--------|
| Language / Framework | Python 3.12 + FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2 + Alembic (migrations) |
| Messaging | Kafka (aiokafka) |
| Containerization | Docker + Kubernetes |
| API Docs | OpenAPI 3 / Swagger UI (FastAPI built-in) |

---

## Health & Observability

| Endpoint | Description |
|----------|-------------|
| `GET /actuator/health` | Liveness & readiness for K8s probes |
| `GET /actuator/metrics` | Prometheus-compatible metrics |

- Distributed tracing via OpenTelemetry; `traceId` propagated in all service-to-service calls
- All logs include `traceId`, `userId`, `requestId` fields

---

## Error Response Format

```json
{
  "timestamp": "2026-03-01T10:00:00Z",
  "status": 409,
  "error": "Conflict",
  "code": "EMAIL_ALREADY_EXISTS",
  "message": "A user with this email already exists",
  "path": "/api/v1/users/register"
}
```

---

*CSE 438 – User Team | Spring 2026*