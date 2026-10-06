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
- İkinci tarama (`micro2026_missed_check.py`): DBLP bir kişiyi birden çok PID'e bölebiliyor (her biri 8'in altında, toplam 8 ve üstü); takma ad, ters yazılmış ad ve sanayi oturumu da tarandı. Xinyu Chen (HKUST(GZ)) böyle bulundu: 96/3374-1 ve 96/3374, 3 + 5 = 8 (`apply_micro2026_secondpass.py`). Yeni girenlerde hata olasılığı daha yüksek, ikinci tarama her konferans güncellemesinde koşulmalı.
- 23 yeni MICRO üyesi (149); 11'i siteye ilk kez girdi (kurum, DBLP PID, öteki konferans sayıları ve Scholar bilgisiyle). Kurum değişiklikleri doğrulandı: Giray Yağlıkçı CISPA (Eki 2025), Mohammad Alian Cornell (Tem 2024), Juan Gómez-Luna NVIDIA (2023).
- ASPLOS 2026 programındaki 168 makalenin hepsi DBLP'de: 152'si 2026 ciltlerinde, 16'sı ASPLOS'25 bildiri kitabının 3. cildinde (2026'da sunuldu, kayıtta 2025 yılı altında; bildiri kitabının yılı esas alınıyor).

## ASPLOS yeniden denetimi (6 Eki 2026)
- Güncel DBLP çekimi `dblp_pull_asplos_fresh.py` → `dblp_sparql/asplos_20261006.json`. 30 Eylül'den beri tek değişiklik bir 2026 kaydında Ziyi Zhang'ın PID'i. Ad takma adları PID ile gruplanınca sitedeki 271 kişinin ASPLOS sayısı (üyelerde yıl yıl) DBLP ile birebir.
- `asplos2026_check.py`: ASPLOS 2026 programının 168 makalesi (152'si ASPLOS'26 ciltleri, 16'sı ASPLOS'25 3. cilt) DBLP kayıtlarıyla eşleşti; her araştırmacının bu makaleleri programdaki kurumla tek tek denetlendi. Programdaki araştırmacılardan DBLP kaydında eksik olan yok ("Nan Sung Kim" yazım hatasını DBLP doğru kişiye bağlamış).
- `asplos_split_check.py`: bütün yıllar için bölünmüş kimlik taraması (gevşek ad eşleşmesi, takma ad, ters ad sırası; dört konferanstaki ortak yazar örtüşmesiyle puan). Sitede olmayıp birleşince 8'e ulaşan kimse yok.
- **Bulunan iki DBLP hatası** (`apply_asplos_splits.py`, ayrıca `apply_dblp_verified.py` EXTRA_PUBL): Scott A. Mahlke'nin ASPLOS 2026 SNIP makalesi yeni açılmış 429/0057'de (11 → 12); Quan Chen'in (SJTU) ASPLOS'25 3. cilt Voyager makalesi uzaktan algılamacı başka bir Quan Chen'de, 40/3858-1 (12 → 13). İkisi de 30 Eylül doğrulamasında gözden kaçmıştı.
- Ayrı kişi çıkanlar: Yu Feng 30/4550-1 (UCSB, PL), Ang Li 33/2805 (UW-Madison 2013) ve 33/2805-11 (Princeton 2020), Jaeyong Lee (SNU, Jihong Kim'in grubu, Jae W. Lee değil), Rakesh Kumar 98/4371-3 (NTNU), Mingyu Gao 61/7672-6, Ravishankar K. Iyer (UIUC). Yu Feng (SJTU) 7'de, Ang Li (PNNL) 7'de kalıyor.
- Xu Liu sınırda (8): SpecProto'da kurumu Google ama eski NC State öğrencisi Qidong Zhao da Google'da ve DeepContext'te ortak yazar, aynı kişi.
- Yıl kuralı: ASPLOS'25 3. cildin 16 makalesi 2026'da sunuldu, sitede 2025 sütununda (bildiri kitabının yılı, kabul tablosuyla aynı kural).
- Kurumlar 2026 programından güncellendi: Kaşıkçı UW, Fletcher UC Berkeley, Suh Cornell / NVIDIA, Xu Liu Google.
- ISCA, MICRO ve HPCA için de yapıldı, aşağıda.

## ISCA, MICRO, HPCA yeniden denetimi (6 Eki 2026)
- `dblp_pull_fresh.py isca micro hpca` → `dblp_sparql/<v>_20261006.json`; `venue_split_check.py <v>` (ASPLOS betiğinin genel hâli: site-DBLP karşılaştırması, bölünmüş kimlik, ortak yazarsız yeni makale, yeni üye adayı). Ayrıca 30 Eylül'ün 60 değişikliğinden her düşüşte o yılın aynı soyadlı yazarları tarandı.
- Bulunan ve düzeltilen beş makale (`apply_other_venue_splits.py`, EXTRA_PUBL'da kayıtlı):
  - Rajiv Gupta MICRO 1993 (HP Labs ile): DBLP bir radyoloğun profiline (181/2697) yazmış, ACM yazar profili UC Riverside'daki Rajiv Gupta. 30 Eylül sayımı bu yüzden 15'i 14'e düşürmüştü, 15'e döndü.
  - Michael C. Huang ISCA 2025 DS-TPU (87/6759'da; program "Michael Huang (Rochester)") 9 → 10.
  - Guangyu Sun HPCA 2026 In-Switch (30 Eylül'de 29/6473'teydi, DBLP sonradan düzeltti; program PKU) 12 → 13.
  - Jie Zhang HPCA 2026 TENET-v2 (84/6889-177; HPCA 2026 sitesi makaleyi AutoGNN ile aynı researchr profiline bağlıyor: CHASE Lab, PKU) 11 → 12.
  - Ang Li HPCA 2026 kuantum LDPC (33/2805; program PNNL) çapraz sayı 4 → 5.
- Düşüşlerin geri kalanı doğru çıktı: Jun Yang MICRO 2020 CATCAM Southeast Üniversitesi'nden başka bir Jun Yang; Mengjia Yan'ın düşen makalesi Mingyu Yan'ındı; David Brooks'un ASPLOS'taki beş makalesi Brooks Davis'indi (CHERI); ISCA'da Ang Li'nin düşen 2026 makalesi (DICE) UW'deki başka bir Ang Li'nin.
- Ortak yazarsız yeni makaleler ISCA 2026 ve HPCA 2025-26 programlarındaki kurumlarla tek tek doğrulandı (Kang Chen µShare Tsinghua, Yufei Ding Yonsei ile ortak çalışma UCSD, Prashant Nair d-Matrix ve UBC, Onur Mutlu COSM ETH vb.); başka kişiye ait çıkan yok.
- Sonuç: ISCA ve HPCA'da site DBLP ile birebir (yalnız belgeli KEEP istisnaları), MICRO'da farklar yalnızca programdan eklenen MICRO 2026 makaleleri. Yeni üye adayı yok (MICRO'da "Yuan Chou" adlı üç PID toplamda 8 ediyor ama UBC'deki Yuan-Hsi Chou ile Sun'daki Yuan C. Chou ayrı kişiler).
- `recompute_crossvenue.py` artık EXTRA_PUBL'ı da okuyor. DBLP MICRO 2026'yı dizinleyene kadar `--apply` ile koşma, programdan gelen MICRO 2026 sayıları silinir.

## Google Scholar yenilemesi (6 Eki 2026, YARIM)
- `refresh_gs.py` 84 profili okudu (8-14 sn arayla), sonra HTTP 429. 30 dk ve 3 x 45 dk beklemeden sonra da 429: Scholar bu adresten otomatik okumayı kapattı. Engeli aşmaya çalışma (tarayıcıya geçmek, kimlik ya da adres değiştirmek yok); beklenir.
- **Sürdürmek için sırayla:** `python refresh_gs.py` (gs_refresh_20261006.json'dan sürer, 15-25 sn, 429'da 45 dk bekler) → `python refresh_gs.py --ids X-HEAfgAAAAJ --as "Amir Roth"` → ilk 84 içindeki yaygın adlıları başlıklarıyla yeniden oku (`--ids`: Yu Feng, Ang Li, Anoop Gupta, Antonio González, Arvind, Benjamin C. Lee, Chao Li, Christopher J. Hughes, Daehoon Kim, David Brooks, Donghyuk Lee) → `python verify_gs.py` (tam ad, en çok atıflı başlıklar DBLP'de mi, kurum) → `python apply_gs_refresh.py --apply` → Combined notuna "Google Scholar, <tarih>" ekle, güncelleme notu, önizleme, yayın. Tabloyu yarı yeni yarı eski rakamla yayına alma, sıralama karışır.
- **Yanlış profiller (Nisan'dan beri):** Lipovski = "Jack Kramer", Papachristou = Christos Papachristos (robotik), Amir Roth = Aaron Roth (33.400 atıf gösteriyordu). Üçü veriden kaldırıldı ve yayında. Amir Roth'un kendi profili X-HEAfgAAAAJ (artık US DOE), tam yenilemeyle girecek. Soyadı denetimi Aaron Roth'u yakalamamıştı; `verify_gs.py` ön adı da istiyor.
- **Yeni profiller (doğrulandı):** Minesh Patel om-NSbgAAAAJ (Rutgers), André Seznec BHupl5EAAAAJ (INRIA/IRISA).
- **Profili yok ya da kullanılamaz:** Sohi, Albonesi, Dubois (aramada çıkan profiller başkalarının), Barroso (profil kaldırılmış, 404), Davidson, Rau, Pleszkun, Schlansker, Lipovski, Papachristou. Amro Awad jDmd7AoAAAAJ bir kez 404 verdi, arama motorunda duruyor; yeniden dene.

## Top Picks (6 Eki 2026)
- **Ad birleştirme:** Top Picks sıralaması yazarı yazıldığı dizgeyle sayıyordu; aynı kişinin iki yazımı iki satıra bölünüyordu (Dean Tullsen 1 + Dean M. Tullsen 2 gibi). Ad ve soyada göre 21 çift bulundu, 20'si aynı kişi; ILLIXR'deki "Jae Lee" (UIUC öğrencisi) Jae W. Lee değil, ayrı kaldı. `apply_tp_name_merge.py` verideki yazımları birleştirdi (HoF listelerindeki yazım, yoksa uzun biçim). Ayrıca `buildTopPicksAuthors` artık `hmNormName` kullanıyor, `buildCombined` Top Picks ve mansiyon sayılarını üzerine yazmak yerine topluyor. Yeni Top Picks eklerken aynı taramayı koş.
- **Bekleyen yıl (2025 konferansları):** seçim Nisan 2026'da açıklandı (129 başvuru, 12 Top Pick, 11 mansiyon; SAFARI duyurusu). Sayı IEEE Micro Cilt 46 Sayı 5'te (Eylül-Ekim 2026) çıkacak; 6 Ekim'de Xplore'da güncel sayı hâlâ 4. sayı (Hot Chips), DBLP'de 1-4. sayılar var. Erken erişimde 11 Top Pick: ColumnDisturb, H-Houdini, GateBleed, Necro-reaper, xUI, Bringing Distributed Ordering to Heterogeneous Memory Consistency, LLM.265, Accounting for Workload Churn in Design Space Exploration, XOR Cache, MLPerf Power, Fast and Accurate CPU Performance Modeling with Compositional Analytical-ML Fusion. 12. makale ve mansiyon listesi editör girişinde (Guest Editors' Introduction) çıkacak, başka yerde tam listesi yok.
- **11'i geçici olarak eklendi (6 Eki 2026, Oğuz'un onayıyla):** `apply_tp2025_provisional.py`, kaynak `dblp_sparql/tp2025_records.json` (konferans sürümünün DBLP başlığı, sıralı yazarları, DOI'si ve Semantic Scholar atıf sayısı). Dergi başlığı farklı olan üçü: Distributed Ordering = CORD (ISCA 2025), Workload Churn = Neoscope (ISCA 2025), CPU Performance Modeling = Concorde (ISCA 2025). Yazar adı: sitede olan kişi için HoF yazımı, değilse Top Picks listesindeki yazım. Sekme notu ve HM notu 2025'in geçici olduğunu söylüyor. Sayı çıkınca: 12. makaleyi ve 11 mansiyonu ekle, notları "complete for 2003-2025" yap, `apply_tp_name_merge.py`'deki ad taramasını yeniden koş.

## Kabul oranları, ASPLOS sayım kuralı (6 Eki 2026)
- **Kural:** ASPLOS 2023'ten beri yılda iki ya da üç başvuru dönemiyle çalışıyor; major revision alan makale bir sonraki yılın toplantısında sunulabiliyor. Tabloda "kabul" o yılın başvurularından kabul edilen bütün makaleler (sonradan kabul edilen revizyonlar dahil), sunulduğu toplantı değil. HoF'taki yıl kovaları da aynı kuralla (bildiri kitabının yılı) sayılıyor, ikisi tutarlı.
- **2023:** 151 / 598. Ciltler: 1. cilt (DBLP'de 2022 yılında) 9, 2. cilt 65, 3. cilt 54 (+2 keynote), toplantıda 128; 4. cilt 23 (7 Şub 2024'te yayımlandı, ASPLOS'24'te sunuldu). Program başkanlarının SIGARCH özeti (Enright Jerger ve Swift, 16 May 2023): 600 başvuru, 151 kabul (128 + 23), %25. Dönem dökümü 90/270/238 = 598 (csconferences, Dan Tsafrir'den). Yürütme kurulu yazısı (Eki 2024) 597 diyor.
- **2024:** 194 / 922 (%21,0). 3. cilt mesajı (ACM DL 10.1145/3620666): 922 başvuru, konferansa kadar 170 kabul (%18,4), sonbaharın 33 revizyonu 4. ciltte ve ASPLOS'25'te. 4. cilt (10.1145/3622781, 10 Nis 2025) 24 makale. Programdaki 193 = 170 + ASPLOS'23'ün 23 revizyonu; csconfstats ve OpenAccept bu 193'ü, csconferences 170'i yazıyor, ikisi de bu kurala uymuyor.
- **2025:** 176 / 912 (%19,3). 1. cilt (10.1145/3669940): bahar + yaz 586 başvuru, 74 kabul (72'si bu ciltte). 2. cilt (10.1145/3676641): 88 = 40 yaz revizyonu + 46 sonbahar doğrudan kabul + 2 ertelenmiş. 3. cilt (10.1145/3676642, 6 Ağu 2025): 16 sonbahar revizyonu + 2 keynote + ASPLOS/EuroSys yarışma özeti (sayılmaz), "toplamda %19". csconfstats 177 yarışma özetini sayıyor, OpenAccept 160 yalnız 1. ve 2. cilt. 912 csconfstats ve OpenAccept'te aynı.
- **2026:** 152 / 1048 (%14,5). İki dönem (bahar 208 başvuru, 20 kabul, 19 revizyon; yaz). ACM DL kabul tablosu 208/20 ve 840/132. Sonbahar dönemi yok. Programdaki 168 = 152 + ASPLOS'25 3. cildin 16 makalesi.
- **2017:** 56 / 320. Program başkanının mesajı 320 başvuru ve 53 kabul diyor, ama program (22 + 34 makalelik iki kısa sunum oturumu) ve bildiri kitabında 56 tam makale var; sysconf (Frachtenberg) 320/56. 321 (csconferences) dayanaksız.
- **2020:** 86 / 486 doğru (program başkanları: 486 başvuru, 66 kabul + 20 koşullu kabul). csconferences 476 yazıyor.
- **Kaynak erişimi:** ACM DL sayfaları curl ve WebFetch'e 403 veriyor, yerleşik tarayıcıda açılıyor; cilt sayfasındaki özet program başkanlarının mesajı. Kesin son tablolar ön sayfa PDF'inde (`/action/showFmPdf?doi=...`), o bağlantı dosya indirmesi başlatıyor, izin almadan açma.

## Tasarım (5 Eki 2026)
- Aydınlık ve karanlık tema: renkler `:root[data-theme=...]` değişkenlerinde; başlıktaki düğme geçiş yapar, seçim localStorage'da, ilk açılış sistem ayarına uyar, bağlantıda `?theme=light|dark` zorlar. Sabit renk yazma; yeni öğe değişken kullansın (grafik `renderAccChart` içinde değişkenleri okur, tema değişince yeniden çizilir).
- Yazı tipleri: metin ve tablolar Inter (tabular rakamlar), başlık Source Serif 4 (Google Fonts).
- Isı haritası renkleri her tema için ayrı (`--isca-1..5` ve mürekkep `-i` değişkenleri); aydınlık temada 5+ en koyu, karanlıkta en parlak, ikisinde de en doygun basamak. Kabul oranı tabloları nötr gri ölçeği (`--hm-*`) kullanır.
- Sekmeler renksiz, konferans rengi yalnız verinin içinde (nokta, sayı, ısı haritası). Sıra rozetleri `.rk1..3`, emoji yok. Sayfa metninde uzun tire yok.
