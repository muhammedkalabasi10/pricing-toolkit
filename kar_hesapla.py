print("=== Kâr Hesaplama Programı ===")

# 1️⃣ Verileri al
alis_fiyati = float(input("Alış fiyatını girin (₺): "))
satis_fiyati = float(input("Satış fiyatını girin (₺): "))
komisyon_orani = float(input("Komisyon oranını girin (%): "))

# 2️⃣ Komisyona %20 KDV ekle
kdvli_komisyon_orani = komisyon_orani * 1.20
komisyon_tutari = satis_fiyati * (kdvli_komisyon_orani / 100)

# 3️⃣ Kargo masrafı (300₺ ve üzeri için)
if satis_fiyati >= 300:
    kargo = 85
else:
    kargo = 0

# 4️⃣ Alış fiyatına KDV ekleme isteği
kdv_ekle = input("Alış fiyatına KDV eklemek ister misiniz? (E/H): ").strip().lower()
if kdv_ekle == "e":
    kdv_orani = float(input("KDV oranını girin (%): "))
    alis_fiyati += alis_fiyati * (kdv_orani / 100)
    print(f"KDV sonrası alış fiyatı: {alis_fiyati:.2f} ₺")
else:
    print("KDV eklenmedi.")

# 5️⃣ Kâr hesapla
kar = satis_fiyati - komisyon_tutari - alis_fiyati - kargo

# 6️⃣ Sonuçları yazdır
print("\n--- Kâr Hesaplama Sonucu ---")
print(f"Alış fiyatı (KDV dahil): {alis_fiyati:.2f} ₺")
print(f"Satış fiyatı: {satis_fiyati:.2f} ₺")
print(f"KDV dahil komisyon oranı: %{kdvli_komisyon_orani:.2f}")
print(f"Komisyon tutarı: {komisyon_tutari:.2f} ₺")
print(f"Kargo: {kargo:.2f} ₺")
print(f"\n💰 Net Kâr: {kar:.2f} ₺")

# Kâr durumu belirt
if kar > 0:
    print("Durum: Kâr ediyorsunuz ✅")
elif kar < 0:
    print("Durum: Zarar ediyorsunuz ❌")
else:
    print("Durum: Başabaş (ne kâr ne zarar) ⚖️")
