#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Excel'den toplu kâr hesaplama (Alış: Birim x Adet - İskonto) + (Alış KDV'li & KDV'siz senaryo)

Beklenen kolonlar (en az):
- Alis_Birim_Fiyati   (birim alış)
- Adet                (varsayılan 1)
- Iskonto_Orani       (yüzde, varsayılan 0)
- Satis_Fiyati        (toplam satış)
- Komisyon_Orani      (yüzde)

Opsiyonel kolonlar:
- Kargo (varsayılan 85)
- Alis_KDV_Orani (varsayılan 10)
- Komisyon_KDV_Orani (komisyona eklenecek KDV; varsayılan 20)
- Urun (isim/etiket)

Not:
- Bu sürüm eval KULLANMAZ. Hücreye "(155*(9/10))*3" gibi ifade yazarsanız sayıya çevrilmez (NaN olur).
  Böyle bir hesabı Excel formülüyle yapıp (değer olarak) kaydetmeniz gerekir.
"""

import argparse
import re
import numpy as np
import pandas as pd

def normalize_col(s: str) -> str:
    s = str(s).strip().lower()
    tr_map = str.maketrans({"ç":"c","ğ":"g","ı":"i","ö":"o","ş":"s","ü":"u"})
    s = s.translate(tr_map)
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s

def to_number(x):
    """Eval yok: Sayı/parasal string -> float. Uygun değilse NaN."""
    if pd.isna(x) or x == "":
        return np.nan
    if isinstance(x, (int, float, np.number)):
        try:
            return float(x)
        except Exception:
            return np.nan

    s = str(x).strip()
    s = s.replace("₺", "").replace("TL", "").replace("tl", "").replace(" ", "")
    # 1234,56 -> 1234.56
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    s = s.replace("%", "")

    # Sadece sayısal formatları kabul et (aritmetik ifade vb. olmasın)
    if not re.fullmatch(r"[-+]?\d+(\.\d+)?", s):
        return np.nan
    try:
        return float(s)
    except Exception:
        return np.nan

def pick_column(df, candidates):
    norm = {normalize_col(c): c for c in df.columns}
    for cand in candidates:
        key = normalize_col(cand)
        if key in norm:
            return norm[key]
    return None

def main():
    input_file = "veri.xlsx"          # Giriş dosyası
    sheet_name = None                 # İlk sayfa
    output_file = "kar_tablosu.xlsx"  # Çıkış dosyası

    sheet_name = 0
    df = pd.read_excel(input_file, sheet_name=sheet_name)

    col_urun = pick_column(df, ["Urun", "Ürün", "Product", "Adi", "Ad", "Name"])
    col_alis_birim = pick_column(df, ["Alis_Birim_Fiyati", "AlisBirimFiyati", "Alis_Birim", "Birim_Alis", "CostUnit"])
    col_adet = pick_column(df, ["Adet", "Qty", "Quantity", "Miktar"])
    col_iskonto = pick_column(df, ["Iskonto_Orani", "Iskonto", "Discount", "Indirim_Orani", "Indirim"])
    col_satis = pick_column(df, ["Satis_Fiyati", "Satis", "SatisFiyati", "Sale", "Toplam_Satis"])
    col_kom = pick_column(df, ["Komisyon_Orani", "Komisyon", "KomisyonOrani", "Commission", "KomOran"])
    col_kargo = pick_column(df, ["Kargo", "Kargo_Masrafi", "Shipping"])
    col_alis_kdv = pick_column(df, ["Alis_KDV_Orani", "AlisKDVOrani", "KDV_Orani", "KDV"])
    col_kom_kdv = pick_column(df, ["Komisyon_KDV_Orani", "KomisyonKDVOrani", "KomKDV", "KDVKomisyon"])

    missing = [name for name, col in [
        ("Alis_Birim_Fiyati", col_alis_birim),
        ("Satis_Fiyati", col_satis),
        ("Komisyon_Orani", col_kom),
    ] if col is None]
    if missing:
        raise SystemExit(f"Eksik zorunlu kolon(lar): {', '.join(missing)}")

    # Sayısallaştır
    df["_alis_birim"] = df[col_alis_birim].map(to_number)
    df["_satis"] = df[col_satis].map(to_number)
    df["_komisyon"] = df[col_kom].map(to_number)

    if col_adet:
        df["_adet"] = df[col_adet].map(to_number).fillna(1.0)
    else:
        df["_adet"] = 1.0

    if col_iskonto:
        df["_iskonto"] = df[col_iskonto].map(to_number).fillna(0.0)
    else:
        df["_iskonto"] = 0.0

    if col_kargo:
        df["_kargo"] = df[col_kargo].map(to_number).fillna(85.0)
    else:
        df["_kargo"] = 85.0

    if col_alis_kdv:
        df["_alis_kdv"] = df[col_alis_kdv].map(to_number).fillna(10.0)
    else:
        df["_alis_kdv"] = 10.0

    if col_kom_kdv:
        df["_kom_kdv"] = df[col_kom_kdv].map(to_number).fillna(20.0)
    else:
        df["_kom_kdv"] = 20.0

    # Alış toplam (kdv hariç): birim x adet, iskonto düş
    df["Alis_Toplam_KDV_siz"] = df["_alis_birim"] * df["_adet"] * (1 - df["_iskonto"] / 100.0)

    # Alış toplam (kdv dahil)
    df["Alis_Toplam_KDV_li"] = df["Alis_Toplam_KDV_siz"] * (1 + df["_alis_kdv"] / 100.0)

    # Komisyon (komisyona KDV eklenmiş oran)
    df["KDV_dahil_komisyon_orani"] = df["_komisyon"] * (1 + df["_kom_kdv"] / 100.0)
    df["Komisyon_tutari"] = df["_satis"] * (df["KDV_dahil_komisyon_orani"] / 100.0)

    # Kârlar
    df["Net_Kar_Alis_KDV_siz"] = df["_satis"] - df["Komisyon_tutari"] - df["Alis_Toplam_KDV_siz"] - df["_kargo"]
    df["Net_Kar_Alis_KDV_li"] = df["_satis"] - df["Komisyon_tutari"] - df["Alis_Toplam_KDV_li"] - df["_kargo"]

    def durum_series(s):
        return np.select([s > 0, s < 0], ["Kâr ✅", "Zarar ❌"], default="Başabaş ⚖️")

    df["Durum_KDV_siz"] = durum_series(df["Net_Kar_Alis_KDV_siz"])
    df["Durum_KDV_li"] = durum_series(df["Net_Kar_Alis_KDV_li"])
    df["KDV_eklenince_fark"] = df["Net_Kar_Alis_KDV_siz"] - df["Net_Kar_Alis_KDV_li"]

    out_cols = []
    if col_urun:
        out_cols.append(col_urun)

    out_cols += [
        col_alis_birim,
        (col_adet or "_adet"),
        (col_iskonto or "_iskonto"),
        col_satis,
        col_kom,
        "KDV_dahil_komisyon_orani",
        "Komisyon_tutari",
        "_kargo",
        "_alis_kdv",
        "_kom_kdv",
        "Alis_Toplam_KDV_siz",
        "Alis_Toplam_KDV_li",
        "Net_Kar_Alis_KDV_siz",
        "Durum_KDV_siz",
        "Net_Kar_Alis_KDV_li",
        "Durum_KDV_li",
        "KDV_eklenince_fark",
    ]

    rename_map = {
        "_kargo": "Kargo",
        "_alis_kdv": "Alis_KDV_Orani",
        "_kom_kdv": "Komisyon_KDV_Orani",
        "_adet": "Adet",
        "_iskonto": "Iskonto_Orani",
    }

    out_df = df[out_cols].rename(columns=rename_map)
    out_df.to_excel(output_file, index=False)
    print(f"✅ Kâr tablosu oluşturuldu: {output_file}")

if __name__ == "__main__":
    main()
