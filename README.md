# pricing-toolkit
A Python-based toolkit for flexible pricing and profitability calculations across multiple sales channels, accounting for costs, commissions, taxes, and other expenses.

# Flexible Pricing Toolkit

Çoklu satış kanalları (pazaryerleri + kendi e-ticaret siten) için ürün bazlı maliyet, komisyon, vergi ve diğer giderleri hesaba katarak **esnek fiyatlama** ve **kârlılık hesapları** yapmaya yönelik Python tabanlı araç seti.

> A Python-based toolkit for flexible pricing and profitability calculations across multiple sales channels, accounting for costs, commissions, taxes, and other expenses.

---

## Özellikler

- 📊 **Çoklu satış kanalı desteği**  
  Trendyol, Hepsiburada vb. pazaryerleri ve ileride eklenebilecek diğer platformlar (Amazon, Shopify, kendi siten, vb.) için esnek mimari.

- 📁 **Excel tabanlı veri giriş/çıkış**  
  Ürün listelerini Excel’den okuyup, hesaplanan minimum satış fiyatı, kâr ve kâr marjı gibi sonuçları tekrar Excel’e yazabilme.

- 💰 **Maliyet & fiyatlama hesapları**
  - Toplam maliyet (alış maliyeti + kargo + ek giderler)
  - Komisyon dikkate alınarak **zararsız (break-even)** fiyat hesaplama
  - Hedef kâr marjına göre minimum satış fiyatı hesaplama
  - Mevcut satış fiyatına göre kâr ve kâr marjı analizi

- 🧩 **Genişletilebilir yapı**
  - Yeni marketplace türleri ekleyebilme
  - Farklı vergi yapıları, komisyon modelleri ve platforma özel parametreler ekleme imkânı
  - Farklı ürün tipleri için ekstra alanlar ile esnetilebilir sınıf yapısı

---

## Kurulum

### 1. Depoyu klonla

```bash
git clone https://github.com/<kullanıcı_adın>/<repo_adın>.git
cd <repo_adın>
