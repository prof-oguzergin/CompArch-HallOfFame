# CompArch Hall of Fame - Proje Notları

## Proje
Bilgisayar mimarisi konferanslarının (HPCA, MICRO, ISCA, ASPLOS) Hall of Fame verilerini birleştiren ve IEEE Micro Top Picks'in ilk kez tam derlemesini yapan web sayfası.

## URL
- GitHub: https://github.com/prof-oguzergin/CompArch-HallOfFame
- Canlı: https://prof-oguzergin.github.io/CompArch-HallOfFame/

## Veri Kaynakları
| Venue | Kaynak | Durum |
|-------|--------|-------|
| HPCA | IEEE TCCA resmi sayfası + DBLP | 2026'ya kadar, DBLP PID ile doğrulandı (30 Eyl 2026) |
| MICRO | ACM SIGMICRO resmi sayfası + DBLP | 2025'e kadar, DBLP PID ile doğrulandı (30 Eyl 2026) |
| ISCA | UW-Madison resmi sayfası + DBLP | 2026'ya kadar, DBLP PID ile doğrulandı (30 Eyl 2026) |
| ASPLOS | Princeton HoF + DBLP | 2026'ya kadar, DBLP PID ile doğrulandı (30 Eyl 2026) |
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

## Yeni HoF Üyesi Ekleme Prosedürü (HER ZAMAN uygula)
Bir kişi herhangi bir venue'da 8+ eşiğini geçip listeye girince, SADECE o venue'yu eklemekle yetinme. Tam profil oluştur:
1. **DBLP PID'sinden TÜM venue sayılarını çek** (hpca/micro/isca/asplos), STRICT match (`conf/isca/` ≠ `conf/iscas/`), keynote/editöryel hariç. PID ile sorgula (isim-string değil).
   - 8+ olan venue(ler): `isca`/`hpca`/... array'ine tam entry (yıl dağılımı + `total`).
   - <8 olan diğer venue'lar: `crossvenue` kaydına ekle (ör. `"X": {hpca:5,micro:2,asplos:2}`).
2. **Google Scholar'dan atıf/h-index çek** → `gs` bölümüne `{gs:"ID",h:..,i10:..,c:..,b:[100+,200+,400+,800+,1000+]}`. Yöntem: `fetch_gs_stojkovic.py` (tek kişi) veya `fetch_gs_all.py` (toplu). Scholar ID'yi WebSearch ile bul.
3. **affiliation ekle**: `affiliations` bölümüne `{inst:"...",pid:"..."}`.
Aksi halde site o kişiyi eksik gösterir (h-index/atıf/cross-venue boş kalır). Örnek: Jovan Stojkovic (20 Haz 2026) bu prosedürle tamamlandı.

## ⚠️ Konferans programı çekme: WebFetch DEĞİL, ham HTML
Konferans program sayfalarını (ISCA/MICRO vb. kabul listesi) WebFetch ile çekme: WebFetch içeriği ~50KB'a TRUNCATE ediyor, yazar listelerini sessizce kırpıyor. 20 Haz 2026'da ISCA 2026 programını WebFetch ile çektim, ~19 yazar (Nika Mansouri-Ghiasi dahil) eksik geldi; hem yeni giren kaçtı hem mevcut üyelerin 2026 sayıları yanlış oldu. DOĞRU yöntem: `curl -sL -H "User-Agent: Mozilla/5.0" URL -o sayfa.html` (ham HTML, ISCA için ~224KB) → `<div class="paper-title">` + `<div class="paper-authors">` bloklarını parse et. Yazar ayırırken affiliation içindeki virgüle dikkat (split `') , '` deseni). Sayım için isim eşleştirmesi otomatik scriptlerle (nickname/initial-tolerant) GÜVENİLMEZ; değişen/şüpheli isimleri ham HTML'de makale+affiliation bazlı ELLE doğrula (ör. "Rakesh Kumar (NTNU)" ≠ bizim UIUC Rakesh Kumar; "A. Giray" = "Abdullah Giray").

## Yapılacaklar
### Tamamlananlar
- [x] **PID'leri tamamla**: 235/235 tamamlandı
- [x] **Affiliation denetimi**: Tüm sekmelerde (HPCA/MICRO/ISCA/ASPLOS/Top Picks) gösteriliyor
- [x] **HPCA/ASPLOS boş sütunları doldur**: Crossvenue yapısıyla çözüldü
- [x] **Yeni HoF girişleri**: MICRO/ISCA 2025 + HPCA/ASPLOS 2026 verileri eklendi
- [x] **Top Picks HM yazarları**: 130 HM girişi tamamlandı
- [x] **Kurum filtreleme**: Dropdown ile çalışıyor

### Devam Eden / Bekleyen
- [x] **DBLP bağlantıları**: affiliations PID'leri akıştaki kanonik PID'e çevrildi (30 Eyl 2026, 40 kayıt; bir kısmı başka kişiyi gösteriyordu). `m/OnurMutlu` gibi eski biçimli PID'ler DBLP'de kanonikse kalır.
- [x] **ASPLOS şüpheliler**: dört konferansın tamamı PID ile yeniden sayıldı (30 Eyl 2026)
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

## DBLP PID doğrulaması (30 Eyl 2026)
Dört liste makale makale DBLP'ye karşı yeniden sayıldı. Hat, sırayla:
1. `dblp_sparql_pull.py`: dört akışı (`streams/conf/<venue>`) SPARQL ile çeker, `dblp_sparql/<venue>.json`.
2. `dblp_verify.py`: kayıtları sınıflandırır (`classify`), HoF ile PID bazında karşılaştırır, `dblp_sparql/compare.json`.
3. `apply_dblp_verified.py`: açık kararlarla (PID, EXTRA_PUBL, KEEP, ADD) data.js'i günceller; `--apply` olmadan kuru koşu.
4. `recompute_crossvenue.py`: crossvenue'yu PID kimliğiyle baştan hesaplar; `--apply`. Yeniden koşunca "0 crossvenue entries change" çıkmalı.
Kanıt dökümü: `dblp_sparql/changes_evidence.txt`. Kişi başı not: `audit.json`.

**Sayılan:** yalnız ana program makalesi. **Sayılmayan:** editörlük, keynote, panel, başkan mesajı, corrigendum, anma yazısı, workshop bildirisi, 25 Years ISCA retrospektif ve yeniden basımları, geri çekilmiş makale (DBLP'de `Withdrawn`, yazarsız: ISCA 2019 TPShare ve "3D-based video recognition"), tek sayfalık özet (HPCA'daki Best of CAL sunumları dahil; asıl makale CAL'da), 2000 sonrası 4 sayfaya kadar davetli yazı. 1992 ISCA'nın yarım sayfalık özetleri de sayılmaz, UW listesi de saymıyor.

**Tuzaklar:**
- IEEE ve DBLP sayfa aralığı yanlış olabilir: HPCA 2011'de üç tam makale "62-63" gibi 2 sayfa kayıtlı (Calvin, Shared LL TLBs, Offline symbolic analysis). Komşu makalenin başlangıç sayfasıyla doğrula; `dblp_verify.py` içinde `FORCE_MAIN`.
- Başlık kelimesi süzgeci yalnız 4 sayfaya kadar olan kayıtlara uygulanır ("Power struggles ... debate", "RemembERR ... Errata" gerçek makale).
- DBLP yazar birleştirmesi: ISCA 1981 `conf/isca/Kathail81` tek yazar "Arvind V. Kathail" diye kayıtlı, gerçekte Arvind ve Vinod Kathail (EXTRA_PUBL).
- Resmî listeler de yanılıyor: SIGMICRO Mengjia Yan'a Mingyu Yan'ın MICRO 2019 makalesini ve InvisiSpec corrigendum'unu, Alameldeen'e MICRO 2024 program başkanı mesajını, Torrellas'a MICRO 2016'da olmayan üçüncü makaleyi saymış. UW Skadron'a ISCA 2002 editörlüğünü, Qian'a geri çekilen TPShare'i saymış. TCCA HPCA 2011'deki üç makaleyi saymamış.
- Aynı adlı farklı kişiler: iki Ang Li var (PNNL/Unconventional AI olan HoF üyesi; UW'deki Princeton doktoralı olan). ISCA 2026 DICE ötekinin.
- data.js'te crossvenue düzenlemesi YALNIZ crossvenue bloğunda yapılır; adlar affiliations ve gs bloklarında da geçiyor (30 Eyl'de ilk denemede affiliations bozuldu, yedekten dönüldü).
- Bir kişinin tek listesi 8'in altına düşerse siteden tümüyle çıkar (crossvenue yalnız üyelere eklenir): 30 Eyl'de Kai Li, Mendel Rosenblum ve Alaa Alameldeen böyle çıktı.


## Site düzeni (5 Eki 2026)
- **Sıralama:** standart yarışma sıralaması (1, 1, 1, 4); berabere olanlar aynı sırayı ve madalyayı alır, numarada "=" imi var. Sıra her zaman bütün listeden hesaplanır (`ranker()`), arama ve kurum süzgeci kişinin gerçek sırasını değiştirmez. Combined'da # sütunu hangi sütuna göre sıralanırsa sıralansın Total sırasını gösterir.
- **Isı haritası renkleri (5 Eki 2026'da yenilendi):** her konferansta 5+ basamağı konferansın kendi canlı rengi (gerekirse biraz açılmış), alt basamaklar o rengin zemine karıştırılmış tonları; sayı arttıkça renk hem açılıyor hem doyuyor. İlk sürümde açıklık 0,82'ye çıkınca mavi, mor ve pembede doygunluk düşüyor, 5+ grimsi görünüyordu (Oğuz fark etti). Ölçütler: 1. basamak zemine karşı en az 2:1, hücre yazısı saf beyaz ya da siyahla en az 4,5:1 (#f1f5f9/#0f172a orta tonlarda yetmiyor), komşu basamaklar OKLab ΔE en az 0,05 (doygunluk artarken ΔL 0,06 mavi/mor/pembede sağlanamıyor; hücredeki sayı değeri zaten veriyor). Arama betikleri oturum geçici klasöründeydi; değiştirilecekse aynı ölçütlerle yeniden hesaplanmalı.
- **Masaüstü ısı haritası:** konferans sekmeleri son yıllardan açılır (`pinRight`), okur sola kaydırınca konumu korunur. Sıra, ad ve Total sabit (`fixSticky()`; sol kaydırmaları sütun genişliğinden ölçülür). Yıl başlığı tablonun kendi kaydırma kutusunda sabit kalır. Telefonda (768 px altı) yıl sütunları gizli, sabit sütunlar kapalı.
- **Tarihler veriden gelir:** "Data as of" = `updates` içinde `site:true` işareti taşımayan ilk girdinin tarihi; alt bilgideki "Last updated" = ilk girdinin tarihi; kutulardaki bitiş yılı = o listedeki en son yıl. Yalnız görünümü değiştiren bir güncelleme notuna `site:true` eklenir.
- **Paylaşım kartı:** `og-card.png` (1200x630) `python make_og_card.py` ile data.js'ten üretilir; alttaki şerit üyelerin yıllara göre makale yoğunluğu. Kartta kişi sayısı yok, eskimez; yine de büyük bir veri güncellemesinden sonra yeniden üretilebilir. Meta etiketleri şimdilik github.io adresini gösteriyor; comparch.oguzergin.net DNS kaydı Wix'e girilince `og:url`, `og:image` ve `twitter:image` yeni adrese çevrilmeli.

## MICRO 2026 geçici güncellemesi (5 Eki 2026)
Program sayfasından (https://www.microarch.org/micro59/program/) eklendi, DBLP MICRO 2026'yı dizinleyince doğrulama hattı (`dblp_sparql_pull.py` → `dblp_verify.py` → `apply_dblp_verified.py` → `recompute_crossvenue.py`) yeniden koşulup geçici sayılar DBLP'ninkilerle değiştirilmeli.
- Hat: ham HTML curl ile (`micro59_prog_raw.html`), oturumlar `micro59_sessions.json`, eşleştirme `micro2026_match.py`, uygulama `apply_micro2026.py` (bütün kararlar dosyada açık yazılı).
- Sayılmayanlar: açılış konuşmaları, keynote, PhD Jobs, SRC oturumu. **Sanayi oturumu (Industry Track, MICRO'da ilk kez) şimdilik sayılmadı**; DBLP bunları ana bildiri kitabına koyarsa Jangwoo Kim +1 olur.
- Ad eşleştirme tuzakları: tireli soyadı ("Juan Gómez Luna" ↔ "Juan Gomez-Luna"), kısa ad ("Ron Dreslinski"), uzun ad ("Abdullah Giray Yaglikci" ↔ "A. Giray Yağlıkçı"). Ad anahtarı eşleşmeyenler için soyadı + ilk harf taraması yapıldı.
- Aynı adlı farklı kişiler: "Rakesh Kumar (NTNU)", "Ang Li (UW)" CacheFlex (öteki Ang Li; BITE ise bizim Ang Li), "Jie Zhang (Southeast Univ.)", DBLP'de 39/449-46 "Jian Wang" (1987-1994 yazarı). Yazar listesindeki kurum, bağlantı sayfalarında ortak yazarlar karşılaştırılarak ayrıldı.
- Ayrıştırma: kurum adının içinde ";" olabiliyor (ICT CAS), yazar grupları parantez dışındaki ";" ile bölünür.
- 22 yeni MICRO üyesi; 10'u siteye ilk kez girdi (kurum, DBLP PID, öteki konferans sayıları ve Scholar bilgisiyle). Kurum değişiklikleri doğrulandı: Giray Yağlıkçı CISPA (Eki 2025), Mohammad Alian Cornell (Tem 2024), Juan Gómez-Luna NVIDIA (2023).
