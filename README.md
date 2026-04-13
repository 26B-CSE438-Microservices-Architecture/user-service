# User Service

User Service, FastAPI tabanlı bir kullanıcı mikroservisidir. Kullanıcı profili, adres, cihaz ve favori satıcı verilerini yönetir.

## Base URL ve Dokümantasyon

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Health: `GET /actuator/health`
- Admin Panel (SQLAdmin): `http://localhost:8000/admin`

## Kimlik ve Header Bilgisi

Public kullanıcı endpointlerinde servis JWT doğrulamaz; gateway'den gelen header'ı kullanır:

- `X-User-Id: <uuid>` (zorunlu, `/register` hariç)

`X-User-Id` geçersiz formatta ise `400 Invalid X-User-Id header` döner.

---

## Endpoint Detayları

## 1) Public Endpoints (`/api/v1/users`)

### `POST /api/v1/users/register`

Yeni kullanıcı kaydı.

Request body:

```json
{
  "name": "Ali",
  "surname": "Veli",
  "email": "ali@example.com",
  "phone": "+905551112233",
  "password": "StrongPass123!",
  "role": "CUSTOMER"
}
```

Response `201 Created`:

```json
{
  "id": "f2f1a57d-9e12-47d3-83fe-0db3b0f7f8d9",
  "name": "Ali",
  "surname": "Veli",
  "email": "ali@example.com",
  "phone": "+905551112233",
  "role": "CUSTOMER",
  "created_at": "2026-03-14T12:34:56.000000Z"
}
```

Hata:

- `409 Conflict`: `Email or phone already exists`
- `400 Bad Request`: `Invalid role`

---

### `GET /api/v1/users/me`

Mevcut kullanıcı profilini ve adres listesini döner.

Headers:

- `X-User-Id: <uuid>`

Response `200 OK`:

```json
{
  "id": "user_f2f1a57d-9e12-47d3-83fe-0db3b0f7f8d9",
  "name": "Ali",
  "surname": "Veli",
  "email": "ali@example.com",
  "phone_number": "+905551112233",
  "role": "CUSTOMER",
  "is_active": true,
  "addresses": [
    {
      "id": "addr_57f1dd6f-b90b-462b-9d64-e9a67b69cc74",
      "address_title": "Ev",
      "city": "Antalya",
      "district": "Muratpaşa",
      "neighborhood": "Yıldız",
      "street": "Atatürk Cad.",
      "building_no": "12",
      "floor": "3",
      "apartment_no": "8",
      "address_description": "Kapı ziline basınız",
      "phone": "+905551112233",
      "location": {
        "lat": 36.8969,
        "lng": 30.7133
      },
      "masked_phone": "905******33",
      "shows_map_preview": true,
      "is_current": true
    }
  ]
}
```

Hata:

- `404 Not Found`: `User not found`

---

### `PUT /api/v1/users/me`

Kullanıcı profil güncellemesi (`name`, `surname`, `phone`).

Headers:

- `X-User-Id: <uuid>`

Request body (en az bir alan):

```json
{
  "name": "Ali",
  "surname": "Veli",
  "phone": "+905559998877"
}
```

Response `200 OK`: `GET /me` ile aynı response formatı.

Hata:

- `400 Bad Request`: `At least one field (name, surname, or phone) must be provided`
- `409 Conflict`: `Phone already exists`
- `404 Not Found`: `User not found`

---

### `POST /api/v1/users/me/change-password`

Giriş yapmış kullanıcının şifresini değiştirir.

Headers:

- `X-User-Id: <uuid>`

Request body:

```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass456!"
}
```

Response `200 OK`:

```json
{
  "message": "Password changed successfully"
}
```

Hata:

- `400 Bad Request`: `Current password is incorrect`
- `400 Bad Request`: `New password must be different from current password`
- `404 Not Found`: `User not found`

---

### `POST /api/v1/users/forgot-password/request`

Şifre sıfırlama talebi oluşturur ve kullanıcıya e-posta ile reset link gönderir.

Request body:

```json
{
  "email": "ali@example.com"
}
```

Response `200 OK`:

```json
{
  "message": "If the email exists, a reset link has been sent"
}
```

Hata:

- `503 Service Unavailable`: `Failed to send reset email`

---

### `POST /api/v1/users/forgot-password/confirm`

Reset linkteki token ile yeni şifreyi kaydeder.

Request body:

```json
{
  "token": "reset_token_from_email_link",
  "new_password": "NewPass456!"
}
```

Response `200 OK`:

```json
{
  "message": "Password reset successfully"
}
```

Hata:

- `400 Bad Request`: `Invalid or expired token`
- `400 Bad Request`: `New password must be different from current password`
- `404 Not Found`: `User not found`

---

### `GET /api/v1/users/me/addresses`

Kullanıcının silinmemiş (`deleted_at is null`) adreslerini listeler.

Headers:

- `X-User-Id: <uuid>`

Query: yok.

Response `200 OK`:

```json
[
  {
    "id": "addr_57f1dd6f-b90b-462b-9d64-e9a67b69cc74",
    "address_title": "Ev",
    "city": "Antalya",
    "district": "Muratpaşa",
    "neighborhood": "Yıldız",
    "street": "Atatürk Cad.",
    "building_no": "12",
    "floor": "3",
    "apartment_no": "8",
    "address_description": "Kapı ziline basınız",
    "phone": "+905551112233",
    "location": {
      "lat": 36.8969,
      "lng": 30.7133
    },
    "masked_phone": "905******33",
    "shows_map_preview": true,
    "is_current": true
  }
]
```

---

### `POST /api/v1/users/me/addresses`

Yeni adres ekler.

Headers:

- `X-User-Id: <uuid>`

Request body:

```json
{
  "address_title": "Ev",
  "city": "Antalya",
  "district": "Muratpaşa",
  "neighborhood": "Yıldız",
  "street": "Atatürk Cad.",
  "building_no": "12",
  "floor": "3",
  "apartment_no": "8",
  "address_description": "Kapı ziline basınız",
  "phone": "+905551112233",
  "location": {
    "lat": 36.8969,
    "lng": 30.7133
  }
}
```

Response `201 Created`:

```json
{
  "id": "addr_57f1dd6f-b90b-462b-9d64-e9a67b69cc74",
  "address_title": "Ev",
  "city": "Antalya",
  "district": "Muratpaşa",
  "neighborhood": "Yıldız",
  "street": "Atatürk Cad.",
  "building_no": "12",
  "floor": "3",
  "apartment_no": "8",
  "address_description": "Kapı ziline basınız",
  "phone": "+905551112233",
  "location": {
    "lat": 36.8969,
    "lng": 30.7133
  }
}
```

---

### `PUT /api/v1/users/me/addresses/{address_id}`

Adresi günceller (partial update). `address_id` hem `addr_<uuid>` hem düz `uuid` kabul eder.

Headers:

- `X-User-Id: <uuid>`

Path param:

- `address_id` (string)

Request body (örnek):

```json
{
  "address_title": "Ofis",
  "district": "Kepez",
  "location": {
    "lat": 36.90,
    "lng": 30.70
  }
}
```

Response `200 OK`: `POST /me/addresses` response formatı ile aynı.

Hata:

- `400 Bad Request`: `Invalid address id`
- `404 Not Found`: `Address not found`

---

### `DELETE /api/v1/users/me/addresses/{address_id}`

Adresi soft delete yapar (`deleted_at` set edilir, `is_current=false` yapılır).

Headers:

- `X-User-Id: <uuid>`

Path param:

- `address_id` (string)

Request body: yok.

Response `200 OK`:

```json
{
  "message": "Address deleted"
}
```

Hata:

- `400 Bad Request`: `Invalid address id`
- `404 Not Found`: `Address not found`

---

### `PATCH /api/v1/users/me/addresses/{address_id}/current`

Kullanıcının aktif adresini değiştirir; önce tüm adresleri `is_current=false`, sonra hedef adresi `true` yapar.

Headers:

- `X-User-Id: <uuid>`

Path param:

- `address_id` (string)

Request body: yok.

Response `200 OK`:

```json
{
  "message": "Current address updated"
}
```

Hata:

- `400 Bad Request`: `Invalid address id`
- `404 Not Found`: `Address not found`

---

### `GET /api/v1/users/me/favorites`

Kullanıcının favori satıcılarını sayfalı olarak listeler.

Headers:

- `X-User-Id: <uuid>`

Query params:

- `page` (opsiyonel, default: `1`, min: `1`)
- `size` (opsiyonel, default: `20`, min: `1`, max: `100`)

Response `200 OK`:

```json
{
  "items": [
    {
      "vendor_id": "vendor_101",
      "created_at": "2026-04-13T10:00:00Z"
    }
  ],
  "page": 1,
  "size": 20,
  "total": 15
}
```

Hata:

- `404 Not Found`: `User not found`

---

### `POST /api/v1/users/me/favorites/{vendor_id}`

Kullanıcının favori satıcılarına ekler (aynı kayıt varsa idempotent davranır).

Headers:

- `X-User-Id: <uuid>`

Path param:

- `vendor_id` (string)

Request body: yok.

Response `200 OK`:

```json
{
  "message": "Vendor added to favorites"
}
```

Hata:

- `400 Bad Request`: `Invalid vendor_id`
- `404 Not Found`: `User not found`

---

### `DELETE /api/v1/users/me/favorites/{vendor_id}`

Favori satıcıdan çıkarır (kayıt yoksa yine başarılı döner).

Headers:

- `X-User-Id: <uuid>`

Path param:

- `vendor_id` (string)

Request body: yok.

Response `200 OK`:

```json
{
  "message": "Vendor removed from favorites"
}
```

Hata:

- `400 Bad Request`: `Invalid vendor_id`
- `404 Not Found`: `User not found`

---

## 2) Internal Endpoints (`/internal/v1/users`)

### `GET /internal/v1/users/{user_id}`

Kullanıcıyı ID ile döner.

Path param:

- `user_id` (UUID)

Response `200 OK`:

```json
{
  "id": "f2f1a57d-9e12-47d3-83fe-0db3b0f7f8d9",
  "name": "Ali",
  "surname": "Veli",
  "email": "ali@example.com",
  "phone": "+905551112233",
  "role": "CUSTOMER",
  "active": true
}
```

Hata:

- `404 Not Found`: `User not found`

---

### `POST /internal/v1/users/lookup`

Toplu kullanıcı sorgusu.

Request body:

```json
{
  "userIds": [
    "f2f1a57d-9e12-47d3-83fe-0db3b0f7f8d9",
    "7e3978a1-330d-46ea-bcf7-2283f42d6f59"
  ]
}
```

Response `200 OK`:

```json
{
  "users": [
    {
      "id": "f2f1a57d-9e12-47d3-83fe-0db3b0f7f8d9",
      "name": "Ali",
      "surname": "Veli",
      "role": "CUSTOMER",
      "active": true
    },
    {
      "id": "7e3978a1-330d-46ea-bcf7-2283f42d6f59",
      "name": "Ayşe",
      "surname": "Yılmaz",
      "role": "COURIER",
      "active": true
    }
  ]
}
```

Not: `userIds` boş verilirse `{ "users": [] }` döner.

---

### `GET /internal/v1/users/by-email?email={email}`

Email ile kullanıcı sorgusu (auth servisinin credential kontrolünde kullanımı için).

Query param:

- `email` (string, zorunlu)

Örnek istek:

```http
GET /internal/v1/users/by-email?email=ali@example.com
```

Response `200 OK`:

```json
{
  "id": "f2f1a57d-9e12-47d3-83fe-0db3b0f7f8d9",
  "email": "ali@example.com",
  "hashedPassword": "$2b$12$abcd...",
  "role": "CUSTOMER",
  "active": true
}
```

Hata:

- `404 Not Found`: `User not found`

---

## 3) Health Endpoint

### `GET /actuator/health`

Request body/query: yok.

Response `200 OK`:

```json
{
  "status": "UP"
}
```

---

## Veritabanı Şeması (Tablo Formatı)

### `users`

| Kolon | Tip | Constraint / Not |
| --- | --- | --- |
| `id` | `UUID` | PK |
| `name` | `VARCHAR(255)` | NOT NULL |
| `surname` | `VARCHAR(255)` | NOT NULL |
| `email` | `VARCHAR(255)` | NOT NULL, UNIQUE, INDEX |
| `phone` | `VARCHAR(20)` | NOT NULL, UNIQUE, INDEX |
| `hashed_password` | `VARCHAR(255)` | NOT NULL |
| `role` | `ENUM(user_role)` | NOT NULL (`CUSTOMER`, `RESTAURANT_OWNER`, `COURIER`, `ADMIN`) |
| `is_active` | `BOOLEAN` | default `true` |
| `created_at` | `TIMESTAMPTZ` | default now |
| `updated_at` | `TIMESTAMPTZ` | default now, on update now |
| `deleted_at` | `TIMESTAMPTZ` | nullable |

### `addresses`

| Kolon | Tip | Constraint / Not |
| --- | --- | --- |
| `id` | `UUID` | PK |
| `user_id` | `UUID` | FK -> `users.id`, ON DELETE CASCADE, INDEX |
| `address_title` | `VARCHAR(100)` | NOT NULL |
| `street` | `VARCHAR(255)` | NOT NULL |
| `city` | `VARCHAR(100)` | NOT NULL |
| `district` | `VARCHAR(100)` | NOT NULL |
| `neighborhood` | `VARCHAR(120)` | NOT NULL |
| `building_no` | `VARCHAR(20)` | NOT NULL |
| `floor` | `VARCHAR(20)` | NOT NULL |
| `apartment_no` | `VARCHAR(20)` | NOT NULL |
| `address_description` | `VARCHAR(255)` | nullable |
| `phone` | `VARCHAR(20)` | NOT NULL |
| `is_current` | `BOOLEAN` | default `false` |
| `lat` | `FLOAT` | nullable |
| `lng` | `FLOAT` | nullable |
| `created_at` | `TIMESTAMPTZ` | default now |
| `deleted_at` | `TIMESTAMPTZ` | nullable (soft delete) |

### `user_favorites`

| Kolon | Tip | Constraint / Not |
| --- | --- | --- |
| `id` | `UUID` | PK |
| `user_id` | `UUID` | FK -> `users.id`, ON DELETE CASCADE, INDEX |
| `vendor_id` | `VARCHAR(100)` | NOT NULL |
| `created_at` | `TIMESTAMPTZ` | default now |

Ek unique constraint:

- `uq_user_vendor_favorite` -> (`user_id`, `vendor_id`)

### `password_reset_tokens`

| Kolon | Tip | Constraint / Not |
| --- | --- | --- |
| `id` | `UUID` | PK |
| `user_id` | `UUID` | FK -> `users.id`, ON DELETE CASCADE, INDEX |
| `token_hash` | `VARCHAR(64)` | NOT NULL, UNIQUE, INDEX (SHA-256 hash) |
| `expires_at` | `TIMESTAMPTZ` | NOT NULL |
| `used_at` | `TIMESTAMPTZ` | nullable |
| `created_at` | `TIMESTAMPTZ` | default now |

---

## Kurulum ve Çalıştırma

### Docker

```bash
docker compose up -d
```

`docker-compose.yml` içinde servis başlangıcında migration otomatik çalışır:

```bash
alembic upgrade head
```

### Lokal

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Ortam Değişkenleri

| Değişken | Default |
| --- | --- |
| `APP_NAME` | `user-service` |
| `APP_PORT` | `8000` |
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@user-db:5432/userdb` |
| `RESET_PASSWORD_URL_BASE` | `http://localhost:3000/reset-password` |
| `RESET_PASSWORD_TOKEN_TTL_MINUTES` | `30` |
| `SMTP_HOST` | `` |
| `SMTP_PORT` | `587` |
| `SMTP_USERNAME` | `` |
| `SMTP_PASSWORD` | `` |
| `SMTP_USE_TLS` | `true` |
| `SMTP_FROM_EMAIL` | `no-reply@example.com` |
