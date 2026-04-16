# CompArch Hall of Fame - Proje Notları

## Proje
Bilgisayar mimarisi konferanslarının (HPCA, MICRO, ISCA, ASPLOS) Hall of Fame verilerini birleştiren ve IEEE Micro Top Picks'in ilk kez tam derlemesini yapan web sayfası.

## URL
- GitHub: https://github.com/prof-oguzergin/CompArch-HallOfFame
- Canlı: https://prof-oguzergin.github.io/CompArch-HallOfFame/

## Veri Kaynakları
| Venue | Kaynak | Durum |
|-------|--------|-------|
| HPCA | IEEE TCCA resmi sayfası + HPCA 2026 DBLP | 2026'ya kadar güncel |
| MICRO | ACM SIGMICRO resmi sayfası | Resmi sayfadan alındı |
| ISCA | UW-Madison resmi sayfası | Resmi sayfadan alındı |
| ASPLOS | Princeton HoF + DBLP | 2026'ya kadar güncel, eksik isimler ekleniyor |
| Top Picks | IEEE Micro PDF'lerden elle | 2003-2024 tam (22 yıl, 261 TP) |

## Önemli Kurallar
1. **HoF eşiği**: 8+ makale (tüm venue'lar için)
2. **Cross-venue veri**: DBLP'den çekildi, ≤7 olanlar güvenilir. 8+ geliyorsa ya isim karışıklığı ya da yeni HoF girişi
3. **DBLP API güvenilirliği**: `author:Name:` ile sorgu yaygın isimlerde yanlış sonuç veriyor. PID ile sorgu (XML endpoint) daha güvenilir
4. **Keynote/invited talk**: Sayılmaz! DBLP bunları ayırt etmiyor, elle kontrol lazım
5. **İsim normalizasyonu**: JS'teki `norm()` fonksiyonu farklı yazılışları birleştiriyor
6. **Kontrol grubu**: Yale N. Patt (HPCA 7, ASPLOS 6), Wen-Mei W. Hwu (HPCA 2), Mateo Valero (ASPLOS 1)

## DBLP Rate Limiting
- 3-5 saniye arayla sorgula
- Çok fazla sorgu IP ban'a yol açar (30-60dk)
- Türkçe karakterli isimler (ğ, ı, ç) API'de hata verebilir

## Dosya Yapısı
- `index.html` - Ana sayfa (tek sayfa uygulama)
- `data.js` - Tüm veriler (HoF, crossvenue, affiliations, Top Picks)
- `fetch_asplos.py` - ASPLOS verisi DBLP'den çekme
- `fetch_cross_venue.py` - Cross-venue verisi çekme
- `fetch_toppicks.py` - Top Picks verisi çekme (IEEE Micro, güvenilir değil)
- `find_new_hpca.py` - Yeni HPCA HoF üyelerini bulma
- `create_toppicks_xlsx.py` - Top Picks Excel oluşturma

## Yapılacaklar
### Tamamlananlar
- [x] **PID'leri tamamla**: 235/235 tamamlandı
- [x] **Affiliation denetimi**: Tüm sekmelerde (HPCA/MICRO/ISCA/ASPLOS/Top Picks) gösteriliyor
- [x] **HPCA/ASPLOS boş sütunları doldur**: Crossvenue yapısıyla çözüldü
- [x] **Yeni HoF girişleri**: MICRO/ISCA 2025 + HPCA/ASPLOS 2026 verileri eklendi
- [x] **Top Picks HM yazarları**: 130 HM girişi tamamlandı
- [x] **Kurum filtreleme**: Dropdown ile çalışıyor

### Devam Eden / Bekleyen
- [ ] **DBLP bağlantıları**: 90 eski stil PID (`x/Name`) hâlâ var, sayısal formata (`XX/YYYY`) geçirilmeli
- [ ] **ASPLOS şüpheliler**: Benjamin C. Lee (7), Tao Li (9?), Ang Li (12?), Chao Li (15?) - PID ile doğrula
- [ ] **Excel güncelle**: 22 yıla genişlet

## KRİTİK KURALLAR — VERİ DOĞRULUĞU
1. **ASLA tahmin etme!** Veri eklerken/güncellerken mutlaka DBLP XML'den doğrula. Yıl/sayı tahmin edilmez.
2. **Venue eşleşmesinde STRICT MATCH kullan!** DBLP key'lerinde `conf/isca/` ile `conf/iscas/` FARKLI konferanslar:
   - `conf/isca/` = ISCA (International Symposium on Computer Architecture) ✓
   - `conf/iscas/` = ISCAS (International Symposium on Circuits and Systems) ✗
   - Python'da: `re.search(r'conf/isca/', key)` kullan, `'conf/isca' in key` KULLANMA!
   - Aynı şekilde: `conf/hpca/` vs `conf/hpcasia/` (HPCAsia farklı konferans)
   - `conf/micro/` vs `conf/micropro/` gibi durumlar olabilir
3. **Aşağıdakiler bildiri sayısına DAHİL EDİLMEMELİ:**
   - Keynote / invited talk (genelde 1 sayfa veya sayfa numarası tek rakam, ör: pp:1, pp:322)
   - Program chair / general chair proceedings editörlüğü
   - Tutorial
   - Panel
   - Retrospective (ör: ISCA 1998 25th Anniversary reprints)
   - Workshop bildirisi (ör: "ISCA Workshops" ≠ ISCA). DİKKAT: DBLP bazen workshop bildirilerini ana konferans key'i altında kaydediyor (ör: conf/isca/GrotKM10 aslında ISCA Workshops 2010). Resmi HoF kaynağıyla çapraz kontrol şart!
   - DBLP hepsini `inproceedings` olarak kaydediyor, ayırt etmek için sayfa sayısına ve başlığa bak
   - Tam bildiriler genelde 10+ sayfa, keynote/editörlük 1-3 sayfa
4. **DBLP sayılarını körü körüne güncelleme!** Resmi HoF kaynaklarıyla (IEEE TCCA, SIGMICRO, UW-Madison, Princeton) karşılaştır. DBLP'de fazla çıkıyorsa keynote/editörlük karışmış olabilir, eksik çıkıyorsa eski yıllar DBLP'de olmayabilir. DİKKAT: Resmi HoF kaynakları da hatalı olabilir — isim karışıklığı (ör: Yuan Xie HKUST vs Yuan Xie Alibaba) nedeniyle farklı kişilerin bildirilerini birleştirebilirler. DBLP PID'li sorgu daha güvenilir çünkü disambiguated.
5. **audit.json** dosyasında her araştırmacının doğrulama tarihi tutulur. Doğrulanmamış kişilerin sayıları güvenilmez olabilir.

## Öğrenilen Dersler
- DBLP `author:Name:` sorgusu yaygın isimlerde GÜVENİLMEZ. PID ile XML sorgusu kullan.
- PID format: disambiguated isimler `-1`, `-2` suffix alıyor (ör: `61/7672-1`)
- Eski stil PID'ler (`x/IsimSoyisim`) çoğu bozuk, sayısal PID (`XX/YYYY`) daha güvenilir
- Resmi HoF'ta yoksa o venue'da max 7 olabilir (≤7 kuralı)
- Kontrol grubu: Patt (HPCA 7, ASPLOS 6), Hwu (HPCA 2), Valero (ASPLOS 1)
- ISCAS/ISCA karışması: `in` operatörü alt-string eşleşmesi yapar, `re.search` ile `/` dahil eşleştir
