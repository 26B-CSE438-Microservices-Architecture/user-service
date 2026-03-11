

# 1. Authentication Service

## POST /api/v1/auth/login

### Request

```json
{
  "email": "sametbilgin@gmail.com",
  "password": "123456"
}
```

### Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR...",
  "expires_in": 3600,
  "user": {
    "id": "user_123",
    "name": "Samet",
    "surname": "Bilgin",
    "email": "sametbilgin@gmail.com",
    "phone_number": "+905551234567"
  }
}
```

---

## POST /api/v1/auth/register

### Request

```json
{
  "name": "Samet",
  "surname": "Bilgin",
  "email": "sametbilgin@gmail.com",
  "phone_number": "+905551234567",
  "password": "123456"
}
```

### Response

```json
{
  "message": "User registered successfully",
  "user_id": "user_123"
}
```

---

## POST /api/v1/auth/refresh-token

### Request

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR..."
}
```

### Response

```json
{
  "access_token": "new_access_token_here",
  "expires_in": 3600
}
```

---

## POST /api/v1/auth/logout

### Request

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR..."
}
```

### Response

```json
{
  "message": "Logged out successfully"
}
```

---

# 2. User Service

## GET /api/v1/users/me

### Response

```json
{
  "id": "user_123",
  "name": "Samet",
  "surname": "Bilgin",
  "email": "sametbilgin@gmail.com",
  "phone_number": "+905551234567",
  "loyalty_points": 420,
  "notification_preferences": {
    "push_enabled": true,
    "sms_enabled": false,
    "email_enabled": true
  }
}
```

---

## POST /api/v1/users/me/device

### Request

```json
{
  "device_token": "fcm_device_token_123",
  "platform": "ios"
}
```

### Response

```json
{
  "message": "Device registered successfully"
}
```

---

## GET /api/v1/users/me/addresses

### Response

```json
[
  {
    "id": "addr_1",
    "address_title": "Ev",
    "city": "Antalya",
    "district": "Kepez",
    "neighborhood": "Kültür Mah",
    "street": "3818 Sokak",
    "building_no": "8",
    "floor": "3",
    "apartment_no": "6",
    "address_description": "Kapı zili çalışmıyor",
    "phone": "05555555555",
    "location": {
      "lat": 36.884804,
      "lng": 30.704044
    },
    "masked_phone": "555*****55",
    "shows_map_preview": true,
    "is_current": true
  }
]
```

---

## POST /api/v1/users/me/addresses

### Request

```json
{
  "address_title": "İş",
  "city": "Antalya",
  "district": "Muratpaşa",
  "neighborhood": "Lara",
  "street": "2050 Sokak",
  "building_no": "10",
  "floor": "5",
  "apartment_no": "12",
  "address_description": "Güvenliğe bırakabilirsiniz",
  "phone": "05555555555",
  "location": {
    "lat": 36.884804,
    "lng": 30.704044
  }
}
```

### Response

```json
{
  "id": "addr_2",
  "address_title": "İş",
  "city": "Antalya",
  "district": "Muratpaşa",
  "neighborhood": "Lara",
  "street": "2050 Sokak",
  "building_no": "10",
  "floor": "5",
  "apartment_no": "12",
  "address_description": "Güvenliğe bırakabilirsiniz",
  "phone": "05555555555",
  "location": {
    "lat": 36.884804,
    "lng": 30.704044
  }
}
```

---

## PUT /api/v1/users/me/addresses/{id}

### Request

```json
{
  "address_title": "Ofis",
  "street": "2055 Sokak",
  "location": {
    "lat": 36.884810,
    "lng": 30.704050
  }
}
```

### Response

```json
{
  "id": "addr_2",
  "address_title": "Ofis",
  "city": "Antalya",
  "district": "Muratpaşa",
  "neighborhood": "Lara",
  "street": "2055 Sokak",
  "building_no": "10",
  "floor": "5",
  "apartment_no": "12",
  "address_description": "Güvenliğe bırakabilirsiniz",
  "phone": "05555555555",
  "location": {
    "lat": 36.884810,
    "lng": 30.704050
  }
}
```

---

## DELETE /api/v1/users/me/addresses/{id}

### Response

```json
{
  "message": "Address deleted"
}
```

---

## GET /api/v1/users/me/favorites?page=1&limit=20

### Response

```json
{
  "page": 1,
  "limit": 20,
  "total": 15,
  "data": [
    {
      "vendor_id": "vendor_101",
      "name": "Burger Point",
      "image_url": "https://cdn.app.com/burger.jpg"
    }
  ]
}
```

---

## POST /api/v1/users/me/favorites/{vendor_id}

### Response

```json
{
  "message": "Vendor added to favorites"
}
```

---

## DELETE /api/v1/users/me/favorites/{vendor_id}

### Response

```json
{
  "message": "Vendor removed from favorites"
}
```

---

