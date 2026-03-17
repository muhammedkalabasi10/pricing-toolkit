#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Lingerium ürün sayfasından verileri çekip Trendyol Excel şablonuna yazar.

Komut satırı kullanımı:
  python fill_lingerium_excel_spyder.py \
      --url "https://lingerium.com/espuar-450-saten-pijama-takimi?Renk=Bordo&Beden=L" \
      --template "pijama-takimi.xlsx" \
      --output "pijama-takimi_doldurulmus.xlsx"

Spyder / IDLE / doğrudan çalıştırma:
- Hiç parametre verilmezse program kullanıcıdan giriş ister.
- URL veya yerel HTML dosya yolu seçilebilir.
- Çıktı dosyası sorulmaz; belirtilmezse çalışılan klasöre kaydedilir.
"""

import argparse
import re
import sys
import unicodedata
from copy import copy
from pathlib import Path

import openpyxl
import requests
from bs4 import BeautifulSoup


DEFAULT_OUTPUT = "pijama-takimi_doldurulmus.xlsx"
DEFAULT_SHEET = "Ürünlerinizi Burada Listeleyin"


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalize_tr(text: str) -> str:
    mapping = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    text = (text or "").translate(mapping)
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def slugify(text: str) -> str:
    text = normalize_tr(text).lower()
    return re.sub(r"[^a-z0-9]+", "", text)


def parse_price(text: str):
    text = clean_text(str(text or ""))
    text = (
        text.replace("₺", "")
        .replace("TL", "")
        .replace("TRY", "")
        .replace("Türk Lirası", "")
        .strip()
    )
    text = re.sub(r"[^\d,\.]", "", text)
    if not text:
        return None

    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            # 1.530,00 -> 1530.00
            text = text.replace(".", "").replace(",", ".")
        else:
            # 1,530.00 -> 1530.00
            text = text.replace(",", "")
    elif "," in text:
        left, right = text.rsplit(",", 1)
        if len(right) == 2:
            text = left.replace(".", "").replace(",", "") + "." + right
        else:
            text = text.replace(",", "")
    elif "." in text:
        left, right = text.rsplit(".", 1)
        if len(right) != 2:
            text = text.replace(".", "")

    try:
        return float(text)
    except ValueError:
        return None


def color_abbr(color: str) -> str:
    norm = re.sub(r"[^A-Z0-9]", "", normalize_tr(color).upper())
    return norm[:3]


def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text


def detect_product_name(soup: BeautifulSoup) -> str:
    for tag_name in ["h1", "h2"]:
        tag = soup.find(tag_name)
        if tag:
            txt = clean_text(tag.get_text(" ", strip=True))
            if txt and "Yorumlar" not in txt:
                return txt

    text = soup.get_text("\n")
    match = re.search(r"ESPUAR\s+(.+?)\s+Ürün Kodu:", text, re.S)
    if match:
        return clean_text(match.group(1))
    return ""


def detect_brand(soup: BeautifulSoup, product_name: str) -> str:
    brand_box = soup.select_one(".brand-name")
    if brand_box:
        txt = clean_text(brand_box.get_text(" ", strip=True))
        if txt:
            return txt.title()

    if product_name:
        return clean_text(product_name.split()[0].title())
    return ""


def detect_product_code(soup: BeautifulSoup) -> str:
    box = soup.select_one(".categories-detail")
    if box:
        text = clean_text(box.get_text(" ", strip=True))
        match = re.search(r"Ürün Kodu:\s*(.+)", text)
        if match:
            return clean_text(match.group(1))

    text = soup.get_text("\n")
    match = re.search(r"Ürün Kodu:\s*([^\n]+)", text)
    return clean_text(match.group(1)) if match else ""


def detect_price(soup: BeautifulSoup):
    selectors = [
        ".product-detail-page-detail-price-box .sell-price",
        ".product-detail-page-detail-box .sell-price",
        ".price-main .sell-price",
        ".sell-price",
        "[data-price]",
        "[content][itemprop='price']",
    ]

    for selector in selectors:
        for tag in soup.select(selector):
            candidates = [
                tag.get("data-price"),
                tag.get("content"),
                clean_text(tag.get_text(" ", strip=True)),
            ]
            for candidate in candidates:
                price = parse_price(candidate)
                if price is not None and price > 0:
                    return price

    html = str(soup)

    regexes = [
        r'"price"\s*:\s*"([\d\.,]+)"',
        r'"price"\s*:\s*([\d\.,]+)',
        r'"salePrice"\s*:\s*"([\d\.,]+)"',
        r'₺\s*([\d\.,]+)',
    ]
    for pattern in regexes:
        match = re.search(pattern, html, re.I)
        if match:
            price = parse_price(match.group(1))
            if price is not None and price > 0:
                return price

    return None


def detect_variants(soup: BeautifulSoup) -> dict:
    variants = {}
    for section in soup.select("div.mb-4"):
        label = section.select_one(".variant-type.choce-variant-type")
        if not label:
            continue
        name = clean_text(label.get_text(" ", strip=True))
        values = [clean_text(v.get_text(" ", strip=True)) for v in section.select(".variant-name")]
        values = [v for v in values if v]
        if values:
            variants[name] = values
    return variants


def detect_images(soup: BeautifulSoup):
    slider = soup.select_one("div.image-slider.product-detail-page-slider.relative")
    images = []
    if slider:
        for img in slider.find_all("img"):
            src = img.get("src") or ""
            if src.startswith("http") and src not in images:
                images.append(src)
    return images[:8]


def detect_breadcrumb_category(soup: BeautifulSoup) -> str:
    crumbs = [clean_text(a.get_text(" ", strip=True)) for a in soup.select(".breadcrumbs .breadcrumb-item a")]
    return crumbs[-1] if crumbs else ""


def extract_page_description(soup: BeautifulSoup) -> str:
    text = soup.get_text("\n")
    match = re.search(r"Ürün\s+Açıklaması\s+(.+?)\s+Yorumlar", text, re.S)
    return clean_text(match.group(1)) if match else ""


def detect_model_number(product_name: str, product_code: str) -> str:
    match = re.search(r"(\d{2,5})\s*$", product_name or "")
    if match:
        return match.group(1)

    match = re.search(r"(\d{2,5})", product_code or "")
    return match.group(1) if match else ""


def build_description(product: dict) -> str:
    colors = ", ".join(product["colors"])
    sizes = ", ".join(product["sizes"])
    return (
        f'{product["product_name"]}, ev giyiminde şıklık ve rahatlığı bir arada sunan '
        f'saten dokulu bir pijama takımıdır. Biye detayları, önden düğmeli üst tasarımı '
        f've uzun kollu yapısıyla hem zarif bir görünüm hem de konforlu bir kullanım sağlar. '
        f'Yumuşak tuşesi sayesinde dinlenme, uyku ve ev içi kullanım için uygundur. '
        f'Ürün {colors} renk seçenekleri ve {sizes} beden alternatifleriyle sunulmaktadır. '
        f'Günlük homewear kullanımı için ideal, sade ve şık bir alt-üst takım tercihidir.'
    )


def parse_product(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    product_name = detect_product_name(soup)
    brand = detect_brand(soup, product_name)
    product_code = detect_product_code(soup)
    price = detect_price(soup)
    variants = detect_variants(soup)

    colors = variants.get("Renk", [])
    sizes = variants.get("Beden", [])
    model_number = detect_model_number(product_name, product_code)
    model_code = f"{slugify(brand)}{model_number}" if model_number else slugify(brand)

    product = {
        "brand": brand,
        "product_name": product_name,
        "product_code": product_code,
        "price": price,
        "colors": colors,
        "sizes": sizes,
        "category_name": detect_breadcrumb_category(soup),
        "images": detect_images(soup),
        "page_description": extract_page_description(soup),
        "model_number": model_number,
        "model_code": model_code,
    }
    product["generated_description"] = build_description(product)
    return product


def copy_row_style(ws, source_row: int, target_row: int, max_col: int):
    ws.row_dimensions[target_row].height = ws.row_dimensions[source_row].height
    for col in range(1, max_col + 1):
        src = ws.cell(source_row, col)
        tgt = ws.cell(target_row, col)
        if src.has_style:
            tgt._style = copy(src._style)
        tgt.font = copy(src.font)
        tgt.fill = copy(src.fill)
        tgt.border = copy(src.border)
        tgt.alignment = copy(src.alignment)
        tgt.protection = copy(src.protection)
        tgt.number_format = src.number_format


def get_selected_color(product_code: str) -> str:
    parts = clean_text(product_code).split()
    return parts[1] if len(parts) >= 2 else ""


def build_variant_rows(product: dict):
    colors = product["colors"]
    sizes = product["sizes"]

    rows = []
    for color in colors:
        for size in sizes:
            rows.append({"color": color, "size": size})
    return rows


def write_excel(template_path: str, output_path: str, product: dict):
    wb = openpyxl.load_workbook(template_path)
    ws = wb[DEFAULT_SHEET]

    headers = {ws.cell(1, c).value: c for c in range(1, ws.max_column + 1)}
    template_category = ws["D2"].value

    variant_rows = build_variant_rows(product)

    for row_idx, variant in enumerate(variant_rows, start=2):
        if row_idx > 2:
            copy_row_style(ws, 2, row_idx, ws.max_column)

        color = variant["color"]
        size = variant["size"]
        abbr = color_abbr(color)
        model_code = product["model_code"]

        barcode = f"{model_code.upper()}-{abbr}-{size.upper()}"
        stock_code = f"STK-{model_code.upper()}-{abbr}-{size.upper()}"

        values = {
            "Barkod": barcode,
            "Model Kodu": model_code,
            "Marka": product["brand"],
            "Kategori": template_category,
            "Para Birimi": "TRY",
            "Ürün Adı": product["product_name"],
            "Ürün Açıklaması": product["generated_description"],
            "Piyasa Satış Fiyatı (KDV Dahil)": product["price"] + 500,
            "Trendyol'da Satılacak Fiyat (KDV Dahil)": product["price"],
            "Ürün Stok Adedi": 20,
            "Stok Kodu": stock_code,
            "KDV Oranı": 10,
            "Beden": size,
            "Alt-Üst Takım": "Gömlek-Pantolon",
            "Kol Boyu": "Uzun",
            "Ürün Detayı": "Biye",
            "Ek Özellik": "Saten",
            "Ürün Tipi": "Düz",
            "Kumaş Tipi": "Saten",
            "Paket İçeriği": "2'li",
            "Boy": "Uzun",
            "Kol Tipi": "Uzun Kol",
            "Materyal": "Dokuma",
            "Yaka Tipi": "Gömlek Yaka",
            "Ortam": "Homewear",
            "Kapama Şekli": "Full Düğme Kapama",
            "Cinsiyet": "Kadın / Kız",
            "Kalıp": "Regular",
            "Desen": "Düz",
            "Sezon": "Tüm Sezonlar",
            "Parça Sayısı": "2 Parça",
            "Bel": "Normal Bel",
            "Persona": "Cool & Comfort",
            "Siluet": "Basic",
            "Yaş Grubu": "Yetişkin",
            "Renk": color,
            "Menşei": "TR",
            "Paça Tipi": "Düz Paça",
            "Web Color": color,
            "Koleksiyon": "Basic",
            "Paça Boyu": "Uzun",
        }

        for idx, img_url in enumerate(product["images"], start=1):
            values[f"Görsel {idx}"] = img_url

        for header, value in values.items():
            col_idx = headers.get(header)
            if col_idx:
                ws.cell(row_idx, col_idx).value = value

        ws.cell(row_idx, headers["Piyasa Satış Fiyatı (KDV Dahil)"]).number_format = "#,##0.00"
        ws.cell(row_idx, headers["Trendyol'da Satılacak Fiyat (KDV Dahil)"]).number_format = "#,##0.00"

    wb.save(output_path)
    return len(variant_rows)


def ask_nonempty(prompt_text: str) -> str:
    while True:
        value = input(prompt_text).strip()
        if value:
            return value
        print("Bu alan boş bırakılamaz.")


def ask_yes_no(prompt_text: str, default: bool = False) -> bool:
    suffix = " [E/h]: " if default else " [e/H]: "
    raw = input(prompt_text + suffix).strip().lower()
    if not raw:
        return default
    return raw in {"e", "evet", "y", "yes"}


def collect_interactive_inputs():
    print("\nLingerium ürün aktarma programı")
    print("-" * 40)
    use_url = ask_yes_no("Ürünü internet adresinden mi çekmek istiyorsunuz?", default=True)

    url = None
    html_path = None
    if use_url:
        url = ask_nonempty("Ürün URL'sini girin: ")
    else:
        html_path = ask_nonempty("HTML dosya yolunu girin: ")

    template = ask_nonempty("Excel şablon yolunu girin: ")

    return {
        "url": url,
        "html": html_path,
        "template": template,
    }


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="Ürün URL'si")
    parser.add_argument("--html", help="Yerel HTML dosyası")
    parser.add_argument("--template", help="Excel şablon yolu")
    parser.add_argument("--output", help="Çıktı Excel yolu")
    return parser.parse_args()


def validate_inputs(args_dict: dict):
    if not args_dict.get("url") and not args_dict.get("html"):
        raise ValueError("URL veya HTML dosya yolu vermelisiniz.")
    if not args_dict.get("template"):
        raise ValueError("Excel şablon yolu zorunludur.")


def ensure_price(product: dict):
    if product.get("price") is not None:
        return

    print("\nUyarı: Ürün fiyatı sayfadan otomatik okunamadı.")
    while True:
        raw = input("Lütfen satış fiyatını girin (örn: 1530 veya 1530,00): ").strip()
        price = parse_price(raw)
        if price is not None and price > 0:
            product["price"] = price
            return
        print("Geçerli bir fiyat girin.")


def main():
    cli_args = parse_args()

    has_cli_values = any([
        cli_args.url,
        cli_args.html,
        cli_args.template,
        cli_args.output,
    ])

    if has_cli_values:
        args_dict = {
            "url": cli_args.url,
            "html": cli_args.html,
            "template": cli_args.template,
            "output": cli_args.output,
        }
    else:
        args_dict = collect_interactive_inputs()

    validate_inputs(args_dict)

    html = Path(args_dict["html"]).read_text(encoding="utf-8") if args_dict.get("html") else fetch_html(args_dict["url"])
    product = parse_product(html)
    ensure_price(product)

    output_path = args_dict.get("output") or str((Path.cwd() / DEFAULT_OUTPUT).resolve())

    written = write_excel(
        template_path=args_dict["template"],
        output_path=output_path,
        product=product,
    )

    print("\nİşlem tamamlandı")
    print("Ürün adı:", product["product_name"])
    print("Marka:", product["brand"])
    print("Model kodu:", product["model_code"])
    print("Renkler:", ", ".join(product["colors"]))
    print("Bedenler:", ", ".join(product["sizes"]))
    print("Yazılan varyant sayısı:", written)
    print("Çıktı dosyası:", output_path)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("\nHata oluştu:", exc)
        if sys.stdin.isatty():
            input("Çıkmak için Enter'a basın...")
        raise
