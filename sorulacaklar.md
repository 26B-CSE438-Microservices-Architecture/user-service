# Favorites Endpointleri İçin Sorular

## Bağlam
`README2` içinde aşağıdaki endpointler isteniyor:
- `GET /api/v1/users/me/favorites?page=1&limit=20`
- `POST /api/v1/users/me/favorites/{vendor_id}`
- `DELETE /api/v1/users/me/favorites/{vendor_id}`

Bu endpointlerin User Service kapsamında olup olmadığı ve veri sınırlarının nasıl çizileceği net değil.

## Hocaya Sorulacak Net Sorular

1. `favorites` User Service sorumluluğunda mı?
- Beklenti: User Service sadece `user_id - vendor_id` ilişkisini mi tutsun, yoksa bu feature tamamen başka serviste mi olsun?

2. `GET /favorites` response’undaki `name` ve `image_url` alanlarının kaynağı ne olmalı?
- Seçenek A: User Service bu alanları kendi DB’sinde de saklar.
- Seçenek B: User Service sadece `vendor_id` döner, `name/image_url` Gateway veya BFF katmanında Vendor/Restaurant servisinden tamamlanır.

3. `vendor_id` formatı ve doğrulama kuralı nedir?
- Örn: `vendor_101` gibi string mi, UUID mi?
- Endpoint `POST /favorites/{vendor_id}` çağrısında vendor varlık doğrulaması zorunlu mu?

4. Pagination sözleşmesi kesin mi?
- `page` ve `limit` için default değerler nedir?
- Max `limit` değeri var mı?

5. Aynı vendor tekrar favoriye eklenirse beklenen davranış nedir?
- `200` idempotent başarı mı?
- `409 conflict` mi?

6. Favoriden silmede bulunamayan kayıt için beklenen status nedir?
- `200` ve "zaten yoktu" yaklaşımı mı?
- `404` mi?

7. Soft delete mi hard delete mi isteniyor?
- Favori ilişkisi fiziksel olarak silinsin mi, yoksa işaretlenip saklansın mı?

8. Vendor silinirse veya pasif olursa favoriler nasıl yönetilecek?
- Otomatik temizleme gerekli mi?
- Event tabanlı senkronizasyon bekleniyor mu?

9. Yetkilendirme modeli net mi?
- Bu endpointlerde sadece `X-User-Id` header yeterli mi?
- `X-User-Role` veya ek kontrol gerekiyor mu?

10. Kontrat önceliği hangisi?
- `README2` mi nihai kaynak?
- Yoksa takımın ana `README.md` kapsamı mı esas alınmalı?

## Önerilen Teknik Yaklaşım (Onay Gelirse)
- User Service içinde `favorites` tablosu: `id`, `user_id`, `vendor_id`, `created_at`.
- Unique constraint: `(user_id, vendor_id)`.
- User Service temel ilişkiyi yönetir.
- `name` ve `image_url` alanları mümkünse Vendor/Restaurant servisinden beslenir.
