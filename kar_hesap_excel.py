#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Excel'den toplu kâr hesaplama (KDV'li & KDV'siz alış senaryoları)

Beklenen kolonlar (en az):
- Alis_Fiyati
- Satis_Fiyati
- Komisyon_Orani   (yüzde)

Opsiyonel kolonlar:
- Kargo (varsayılan 85)
- Alis_KDV_Orani (varsayılan 10)
- Komisyon_KDV_Orani (komisyona eklenecek KDV; varsayılan 20)
- Urun (isim/etiket; zorunlu değil)

Not:
- Alış fiyatı gibi hücrelere "100+10" gibi basit aritmetik ifade yazarsanız eval ile hesaplanır.
  (eval; __builtins__ kapalı şekilde kullanılır)
- Binlik ayırıcı içeren formatlar (1.234,56 gibi) yerine 1234,56 veya 1234.56 kullanın.
"""

import argparse
import re
import numpy as np
import pandas as pd

def normalize_col(s: str) -> str:
    s = str(s).strip().lower()
    # Türkçe karakterleri sadeleştir
    tr_map = str.maketrans({"ç":"c","ğ":"g","ı":"i","ö":"o","ş":"s","ü":"u"})
    s = s.translate(tr_map)
    s = re.sub(r"[^a-z0-9]+", "", s)
    return s

def safe_eval_cell(x):
    """Excel hücresindeki değeri sayıya çevirir. String ise eval (builtins kapalı) ile dener."""
    if pd.isna(x) or x == "":
        return np.nan
    if isinstance(x, (int, float, np.number)):
        try:
            return float(x)
        except Exception:
            return np.nan

    s = str(x).strip()
    # Para simgesi ve boşlukları temizle
    s = s.replace("₺", "").replace("TL", "").replace("tl", "").replace(" ", "")
    # Basit TR ondalık desteği (1234,56 -> 1234.56)
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    # Yüzde işareti varsa çıkar
    s = s.replace("%", "")

    try:
        return float(eval(s, {"__builtins__": None}, {}))
    except Exception:
        # Son çare: doğrudan float dene
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
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="Giriş Excel dosyası (örn: veri.xlsx)")
    ap.add_argument("--sheet", default=None, help="Sayfa adı (boşsa ilk sayfa)")
    ap.add_argument("--out", default="kar_tablosu.xlsx", help="Çıkış Excel dosyası")
    args = ap.parse_args()

    df = pd.read_excel(args.input, sheet_name=args.sheet)

    # Kolon eşleştirmeleri (farklı yazımlara tolerans)
    col_urun = pick_column(df, ["Urun", "Ürün", "Product", "Adi", "Ad", "Name"])
    col_alis = pick_column(df, ["Alis_Fiyati", "Alis", "AlisFiyati", "Cost", "AlisF"])
    col_satis = pick_column(df, ["Satis_Fiyati", "Satis", "SatisFiyati", "Sale", "SatisF"])
    col_kom = pick_column(df, ["Komisyon_Orani", "Komisyon", "KomisyonOrani", "Commission", "KomOran"])
    col_kargo = pick_column(df, ["Kargo", "Kargo_Masrafi", "Shipping"])
    col_alis_kdv = pick_column(df, ["Alis_KDV_Orani", "AlisKDVOrani", "KDV_Orani", "KDV"])
    col_kom_kdv = pick_column(df, ["Komisyon_KDV_Orani", "KomisyonKDVOrani", "KomKDV", "KDVKomisyon"])

    # Zorunlu kolon kontrolü
    missing = [name for name, col in [("Alis_Fiyati", col_alis), ("Satis_Fiyati", col_satis), ("Komisyon_Orani", col_kom)] if col is None]
    if missing:
        raise SystemExit(f"Eksik zorunlu kolon(lar): {', '.join(missing)}")

    # Sayısallaştır
    df["_alis"] = df[col_alis].map(safe_eval_cell)
    df["_satis"] = df[col_satis].map(safe_eval_cell)
    df["_komisyon"] = df[col_kom].map(safe_eval_cell)

    if col_kargo:
        df["_kargo"] = df[col_kargo].map(safe_eval_cell)
    else:
        df["_kargo"] = 85.0

    if col_alis_kdv:
        df["_alis_kdv"] = df[col_alis_kdv].map(safe_eval_cell).fillna(10.0)
    else:
        df["_alis_kdv"] = 10.0

    if col_kom_kdv:
        df["_kom_kdv"] = df[col_kom_kdv].map(safe_eval_cell).fillna(20.0)
    else:
        df["_kom_kdv"] = 20.0

    # Hesaplar
    df["KDV_dahil_komisyon_orani"] = df["_komisyon"] * (1 + df["_kom_kdv"] / 100.0)
    df["Komisyon_tutari"] = df["_satis"] * (df["KDV_dahil_komisyon_orani"] / 100.0)

    df["Alis_KDV_siz"] = df["_alis"]
    df["Alis_KDV_li"] = df["_alis"] * (1 + df["_alis_kdv"] / 100.0)

    df["Net_Kar_Alis_KDV_siz"] = df["_satis"] - df["Komisyon_tutari"] - df["Alis_KDV_siz"] - df["_kargo"]
    df["Net_Kar_Alis_KDV_li"] = df["_satis"] - df["Komisyon_tutari"] - df["Alis_KDV_li"] - df["_kargo"]

    def durum_series(s):
        return np.select([s > 0, s < 0], ["Kâr ✅", "Zarar ❌"], default="Başabaş ⚖️")

    df["Durum_KDV_siz"] = durum_series(df["Net_Kar_Alis_KDV_siz"])
    df["Durum_KDV_li"] = durum_series(df["Net_Kar_Alis_KDV_li"])

    df["KDV_eklenince_fark"] = df["Net_Kar_Alis_KDV_siz"] - df["Net_Kar_Alis_KDV_li"]

    # Çıkış kolonları
    out_cols = []
    if col_urun:
        out_cols.append(col_urun)

    out_cols += [
        col_alis, col_satis, col_kom,
        "KDV_dahil_komisyon_orani", "Komisyon_tutari",
        "_kargo", "_alis_kdv", "_kom_kdv",
        "Alis_KDV_siz", "Alis_KDV_li",
        "Net_Kar_Alis_KDV_siz", "Durum_KDV_siz",
        "Net_Kar_Alis_KDV_li", "Durum_KDV_li",
        "KDV_eklenince_fark"
    ]

    # Kolon adlarını daha okunur yap
    rename_map = {
        "_kargo": "Kargo",
        "_alis_kdv": "Alis_KDV_Orani",
        "_kom_kdv": "Komisyon_KDV_Orani",
    }
    out_df = df[out_cols].rename(columns=rename_map)

    out_df.to_excel(args.out, index=False)
    print(f"✅ Kâr tablosu oluşturuldu: {args.out}")

if __name__ == "__main__":
    main()
