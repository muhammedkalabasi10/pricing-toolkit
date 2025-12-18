import json
import pandas as pd

# 1. JSON dosyasını oku (liste halinde)
with open("data.json", "r", encoding="utf-8") as f:
    data_list = json.load(f)  # <-- ARTIK BİR LİSTE

rows = []

# 2. Her data objesini dolaş
for data in data_list:
    page = data.get("page")  # istersek Excel'e de yazabiliriz

    for item in data["searchApplicableCampaignOfferVmList"]:
        urun = item["includedSkus"][0]

        for pc in item["priceCommissionRangesV2"]:
            rows.append({
                "Sayfa": page,
                "Urun": urun,
                "Alis_Birim_Fiyati": "",
                "Adet": "",
                "Iskonto_Orani": "",
                "Satis_Fiyati": pc["price"],
                "Komisyon_Orani": pc["commission"],
                "Kargo": 85,
                "Alis_KDV_Orani": 10,
                "Komisyon_KDV_Orani": 20
            })

# 3. DataFrame oluştur
df = pd.DataFrame(rows)

# 4. Excel'e yaz
df.to_excel("veri.xlsx", index=False)

print("Tüm data objeleri işlendi, veri.xlsx oluşturuldu.")
