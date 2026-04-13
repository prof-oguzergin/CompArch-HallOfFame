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
- [ ] ASPLOS HoF'u tamamla (Rajiv Gupta, Benjamin C. Lee, Tao Li, Ang Li kontrol et)
- [ ] Diğer venue'lar için de yeni HoF girişlerini bul (MICRO 2025, ISCA 2025)
- [ ] Affiliations listesini tamamla (şu an ~90 kişi, toplam ~240)
- [ ] Top Picks Honorable Mention yazarlarını web'den bul
- [ ] Excel dosyasını 22 yıla genişlet
- [ ] Kurumları da sayfada göster (filtreleme?)
