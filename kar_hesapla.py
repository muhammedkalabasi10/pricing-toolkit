print("=== Kâr Hesaplama Programı (KDV'li & KDV'siz) ===")

# Girdiler (eval geri eklendi)
alis_fiyati = float(eval(
    input("Alış fiyatını girin (₺): "),
    {"__builtins__": None},
    {}
))
satis_fiyati = float(input("Satış fiyatını girin (₺): "))
komisyon_orani = float(input("Komisyon oranını girin (%): "))

# Komisyona %20 KDV ekle
kdvli_komisyon_orani = komisyon_orani * 1.20
komisyon_tutari = satis_fiyati * (kdvli_komisyon_orani / 100)

# Kargo masrafı
kargo = 85

# Alış KDV oranı (%10)
alis_kdv_orani = 10

# Senaryo 1: Alış KDV'siz
alis_kdvsiz = alis_fiyati
kar_kdvsiz = satis_fiyati - komisyon_tutari - alis_kdvsiz - kargo

# Senaryo 2: Alış KDV'li (%10 eklenmiş)
alis_kdvli = alis_fiyati * (1 + alis_kdv_orani / 100)
kar_kdvli = satis_fiyati - komisyon_tutari - alis_kdvli - kargo

def durum(kar: float) -> str:
    if kar > 0:
        return "Kâr ✅"
    elif kar < 0:
        return "Zarar ❌"
    return "Başabaş ⚖️"

# Sonuçlar
print("\n--- Komisyon & Sabit Giderler ---")
print(f"Satış fiyatı: {satis_fiyati:.2f} ₺")
print(f"KDV dahil komisyon oranı: %{kdvli_komisyon_orani:.2f}")
print(f"Komisyon tutarı: {komisyon_tutari:.2f} ₺")
print(f"Kargo: {kargo:.2f} ₺")

print("\n--- Senaryo Karşılaştırması ---")
print(f"Alış (KDV'siz): {alis_kdvsiz:.2f} ₺  -> 💰 Net Kâr: {kar_kdvsiz:.2f} ₺  | Durum: {durum(kar_kdvsiz)}")
print(f"Alış (KDV'li  %10): {alis_kdvli:.2f} ₺  -> 💰 Net Kâr: {kar_kdvli:.2f} ₺  | Durum: {durum(kar_kdvli)}")
