### Favorites Composition Plan (User Service + Gateway/BFF + Restaurant Service)

#### Summary
`favorites` ownership User Service’te kalacak (`user_id` ↔ `vendor_id`).  
Mobile’ın beklediği `name` ve `image_url` alanları **Gateway/BFF** katmanında, Restaurant Service’ten alınan verilerle compose edilecek.

Seçilen kararlar:
- Compose katmanı: **Gateway/BFF**
- Vendor detay API’si: **Restaurant bulk lookup**

#### Implementation Changes
1. **User Service (bu repo)**
- Yeni endpoint: `GET /api/v1/users/me/favorites?page=1&limit=20`
- Response (User Service iç sözleşmesi):
  - `page`, `limit`, `total`
  - `data: [{ "vendor_id": "vendor_101" }]`
- `POST /me/favorites/{vendor_id}` ve `DELETE /me/favorites/{vendor_id}` mevcut hali korunur.
- Pagination kuralları:
  - default: `page=1`, `limit=20`
  - validation: `page >= 1`, `1 <= limit <= 100`
- Sıralama: `created_at DESC` (en son favorilenen üstte).

2. **Gateway/BFF (arkadaş ekibine net task)**
- Mobile contract’ını burada üret:
  - `GET /api/v1/users/me/favorites?page&limit`
  - User Service’ten `vendor_id` listesi al.
  - Restaurant Service bulk lookup çağır.
  - Merge edip mobile şu formatı dön:
    - `data: [{ vendor_id, name, image_url }]`
- Merge kuralı:
  - Restaurant’tan dönmeyen `vendor_id` için item response’tan düşürülsün.
  - `total` User Service total’ı kalsın (source-of-truth favorites ilişkisi).

3. **Restaurant Service (arkadaş ekibine net task)**
- Internal endpoint sağlamalı:
  - `POST /internal/v1/vendors/lookup`
- Request:
  ```json
  { "vendorIds": ["vendor_101", "vendor_202"] }
  ```
- Response:
  ```json
  {
    "vendors": [
      { "vendor_id": "vendor_101", "name": "Burger Point", "image_url": "https://..." }
    ]
  }
  ```
- Kurallar:
  - Sadece aktif/görünebilir vendor’ları döndür.
  - Bulunamayan ID’leri response’a koyma.
  - `vendor_id` unique olmalı.

#### Cross-Service Data Expectations (paylaşılacak net liste)
1. **User Service -> Gateway/BFF**
- Beklenen alanlar: `vendor_id`, `created_at` (opsiyonel), pagination metadata (`page`, `limit`, `total`).

2. **Gateway/BFF -> Restaurant Service**
- Giden: `vendorIds[]`.
- Dönen zorunlu alanlar: `vendor_id`, `name`, `image_url`.
- Opsiyonel gelecekte: `is_open`, `rating`, `delivery_eta`.

3. **Gateway/BFF -> Mobile**
- Tek response:
  - `page`, `limit`, `total`, `data[{vendor_id,name,image_url}]`.

#### Test Plan
1. User Service unit/integration
- `GET favorites` boş liste.
- Pagination doğru (`page/limit/total`).
- Aynı vendor iki kez POST idempotent.
- DELETE idempotent.

2. Gateway composition tests
- Restaurant tüm vendor’ları döndürüyor: tam merge.
- Restaurant kısmi dönüyor: eksikler düşüyor.
- Restaurant timeout/hata: degrade davranışı (HTTP 502 veya fallback policy, ekipte netleştirilecek ama tek policy seçilip sabitlenecek).

3. Contract tests
- User Service <-> Gateway response şeması.
- Gateway <-> Restaurant bulk lookup şeması.

#### Assumptions / Defaults
- `vendor_id` formatı string (`vendor_101` gibi) ve tüm servislerde aynı.
- Favorites source-of-truth User Service.
- Vendor detay source-of-truth Restaurant Service.
- User Service vendor adı/görseli snapshot olarak tutmayacak (şimdilik).
