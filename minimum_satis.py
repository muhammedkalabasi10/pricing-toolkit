while True:
    print("\n=== Zararsız Satış Fiyatı Hesaplama ===")

    # Kullanıcıdan verileri al
    alis_fiyati = float(input("Alış fiyatını girin (₺): "))
    komisyon_orani = float(input("Komisyon oranını girin (%): "))

    # KDV ekleme tercihi
    kdv_ekle = input("Alış fiyatına KDV eklemek ister misiniz? (E/H): ").strip().lower()

    if kdv_ekle == "e":
        kdv_orani = float(input("KDV oranını girin (%): "))
        alis_fiyati += alis_fiyati * (kdv_orani / 100)
        print(f"KDV dahil alış fiyatı: {alis_fiyati:.2f} ₺")
    else:
        print("KDV eklenmedi.")

    # Kargo bedelini belirle
    if alis_fiyati >= 300:
        kargo = 85
    else:
        kargo = 0

    # Komisyona %20 KDV ekle
    kdvli_komisyon = komisyon_orani * 1.20

    # Zararsız satış fiyatını hesapla
    zararsiz_satis = (alis_fiyati + kargo) / (1 - (kdvli_komisyon / 100))

    # Sonuçları yazdır
    print("\n--- Zararsız Satış Fiyatı Sonucu ---")
    print(f"Alış fiyatı (KDV dahil): {alis_fiyati:.2f} ₺")
    print(f"Kargo: {kargo:.2f} ₺")
    print(f"KDV dahil komisyon oranı: %{kdvli_komisyon:.2f}")
    print(f"Zararsız (minimum) satış fiyatı: {zararsiz_satis:.2f} ₺")

    # Tekrar sormak için kullanıcıya seçenek sun
    devam = input("\nYeni bir hesaplama yapmak ister misiniz? (E/H): ").strip().lower()
    if devam != "e":
        print("Çıkış yapılıyor... 👋")
        break
