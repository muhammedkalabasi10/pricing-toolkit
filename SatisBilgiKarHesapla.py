import pandas as pd
import numpy as np


# =======================
# 1) DOSYA YOLLARI
# =======================
SATIS_PATH = "Satisbilgisi.xlsx"
PRODUCTS_PATH = "products.xlsx"
SATIS_SHEET = "Listelerim"          # SatisBilgisi sheet adı
OUT_PATH = "kar_hesaplama_sonuclari.xlsx"

SHIPPING = 85.0                     # kargo
KDV_ORANI = 0.10                    # %10


# =======================
# 2) YARDIMCI FONKSİYONLAR
# =======================
def normalize_key(x) -> str:
    """Eşleştirme anahtarını temizler (12345.0 -> 12345 gibi)."""
    if pd.isna(x):
        return ""
    s = str(x).strip()
    if s.endswith(".0"):
        s = s[:-2]
    return s.strip()

def parse_percent_to_rate(x) -> float:
    """
    '18%' -> 0.18
    '3,63%' -> 0.0363
    18 -> 0.18
    0.18 -> 0.18
    """
    if pd.isna(x):
        return 0.0

    if isinstance(x, (int, float, np.integer, np.floating)):
        v = float(x)
        return v / 100.0 if v > 1 else v

    s = str(x).strip()
    if not s:
        return 0.0
    s = s.replace("%", "").replace(" ", "").replace(",", ".")
    try:
        v = float(s)
        return v / 100.0 if v > 1 else v
    except Exception:
        return 0.0


# =======================
# 3) VERİYİ OKU
# =======================
satis = pd.read_excel(SATIS_PATH, sheet_name=SATIS_SHEET)
products = pd.read_excel(PRODUCTS_PATH)

# Satis/Fiyat kolonu bazı dosyalarda "Satis" bazı dosyalarda "Fiyat" olabiliyor
sales_col = "Satis" if "Satis" in satis.columns else "Fiyat"
if sales_col not in satis.columns:
    raise ValueError("SatisBilgisi içinde 'Satis' veya 'Fiyat' kolonu bulunamadı.")

# Numeric dönüşümler
satis[sales_col] = pd.to_numeric(satis[sales_col], errors="coerce")
if "İndirimli Fiyat" in satis.columns:
    satis["İndirimli Fiyat"] = pd.to_numeric(satis["İndirimli Fiyat"], errors="coerce")

products["Alış Fiyatı (İskontolu %10)"] = pd.to_numeric(
    products["Alış Fiyatı (İskontolu %10)"], errors="coerce"
)

# Key alanlarını temizle
satis["_key"] = satis["Satıcı Stok Kodu"].apply(normalize_key)
products["_key"] = products["HB Ürün Id"].apply(normalize_key)

# Aynı Ürün Id birden fazla ise merge sırasında satır çoğalmasın diye tekilleştir
products_dedup = products.drop_duplicates(subset=["_key"], keep="first")

# =======================
# 4) MERGE
# =======================
df = satis.merge(
    products_dedup,
    on="_key",
    how="left",
    suffixes=("_SatisBilgisi", "_Products")
)

# =======================
# 5) HESAPLAMALAR
# =======================
df["Komisyon_Rate"] = df["Komisyon Oranı"].apply(parse_percent_to_rate)

df["Alış_İsk10"] = df["Alış Fiyatı (İskontolu %10)"]
df["Alış_İsk10_KDV"] = df["Alış_İsk10"] * (1 + KDV_ORANI)

# --- Satış/Fiyat üzerinden ---
df["Brut_Satis_Fiyat"] = df[sales_col]
df["Net_Satis_Fiyat"] = df["Brut_Satis_Fiyat"] * (1 - df["Komisyon_Rate"])
df["KDVli_Kar_Fiyat"] = df["Net_Satis_Fiyat"] - df["Alış_İsk10_KDV"] - SHIPPING
df["KDVsiz_Kar_Fiyat"] = df["Net_Satis_Fiyat"] - df["Alış_İsk10"] - SHIPPING

# --- İndirimli Fiyat üzerinden (varsa) ---
if "İndirimli Fiyat" in df.columns:
    df["Brut_Satis_Indirimli"] = df["İndirimli Fiyat"]
    df["Net_Satis_Indirimli"] = df["Brut_Satis_Indirimli"] * (1 - df["Komisyon_Rate"])
    df["KDVli_Kar_Indirimli"] = df["Net_Satis_Indirimli"] - df["Alış_İsk10_KDV"] - SHIPPING
    df["KDVsiz_Kar_Indirimli"] = df["Net_Satis_Indirimli"] - df["Alış_İsk10"] - SHIPPING

# =======================
# 6) SONUÇ TABLOSU
# =======================
base_cols = [
    "Satıcı Stok Kodu", "Komisyon Oranı", sales_col, "İndirimli Fiyat",
    "HB Ürün Id", "Alış Fiyatı (İskontolu %10)",
    "Komisyon_Rate", "Alış_İsk10", "Alış_İsk10_KDV",
    "Net_Satis_Fiyat", "KDVli_Kar_Fiyat", "KDVsiz_Kar_Fiyat",
    "Net_Satis_Indirimli", "KDVli_Kar_Indirimli", "KDVsiz_Kar_Indirimli",
]
result_cols = [c for c in base_cols if c in df.columns]
result = df[result_cols].copy()

summary = pd.DataFrame({
    "Toplam Satır": [len(result)],
    "Eşleşen Ürün": [result["HB Ürün Id"].notna().sum() if "HB Ürün Id" in result.columns else np.nan],
    "Eşleşmeyen": [result["HB Ürün Id"].isna().sum() if "HB Ürün Id" in result.columns else np.nan],
    "Ortalama KDV'li Kâr (Fiyat)": [result["KDVli_Kar_Fiyat"].mean(skipna=True) if "KDVli_Kar_Fiyat" in result.columns else np.nan],
    "Ortalama KDV'siz Kâr (Fiyat)": [result["KDVsiz_Kar_Fiyat"].mean(skipna=True) if "KDVsiz_Kar_Fiyat" in result.columns else np.nan],
    "Ortalama KDV'li Kâr (İndirimli)": [result["KDVli_Kar_Indirimli"].mean(skipna=True) if "KDVli_Kar_Indirimli" in result.columns else np.nan],
    "Ortalama KDV'siz Kâr (İndirimli)": [result["KDVsiz_Kar_Indirimli"].mean(skipna=True) if "KDVsiz_Kar_Indirimli" in result.columns else np.nan],
})

# =======================
# 7) EXCEL'E YAZ + ÖNİZLEME
# =======================
with pd.ExcelWriter(OUT_PATH, engine="openpyxl") as writer:
    result.to_excel(writer, index=False, sheet_name="Sonuclar")
    summary.to_excel(writer, index=False, sheet_name="Ozet")

print("Bitti! Dosya:", OUT_PATH)
print(result.head(10))
