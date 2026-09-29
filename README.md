# Memocan — masaüstü çalışma arkadaşın

Windows için erişilebilir masaüstü asistanı: su takibi, günlük/haftalık bilgisayar kullanım metrikleri, mola hatırlatıcısı ve isteğe bağlı sesli AI sohbeti.

## Hızlı kurulum — Python gerekmez

1. [Son sürümden](https://github.com/mustan79/memocan_app/releases/latest) **Memocan-Windows.zip** dosyasını indir.
2. ZIP'i bir klasöre çıkar.
3. **Install-Memocan.bat** dosyasını çift tıkla. Uygulama kullanıcı hesabına kurulur; masaüstü/Başlat menüsü kısayolları oluşturulur.
4. Kurmadan denemek için **Memocan.exe** dosyasını aç.

Paket dijital olarak imzalanmamıştır; Windows yayıncıyı doğrulayamayabilir. Yalnız bu deponun Releases sayfasından indirin. `SHA256SUMS.txt` ile indirdiğiniz ZIP'in özetini karşılaştırabilirsiniz.

## Su ve metrikler

- Avatara tıkla veya **Ctrl+Alt+M**: ana menü.
- **Su içtim (+1 bardak)** / **Drink water (+1 glass)**: her basış tam bir bardak ekler. Menü açık kalır ve günlük toplam güncellenir.
- **Metrikler** / **Metrics**: ilk açılışta **bu hafta ve bugün** seçilidir.
- Hafta açılır listesinden geçmiş haftaları, tarih listesinden o haftanın gününü seç.
- Gün ve hafta için **aktif kullanım**, **bilgisayarın izlenen açık/uyanık süresi** ve **bardak sayısı** ayrı gösterilir.
- **Yenile** en yeni kayıtları getirir. Haftalar Pazartesi–Pazar arasıdır.

**Ölçüm kapsamı:** Bilgisayar süresi Memocan çalışırken tutulur; Windows uyku/hazırda bekletme süresi sayılmaz. Uygulama kapalıyken ve kurulmadan önce geçen süre geri üretilemez. Tam gün takibi için Ayarlar'dan oturum açılışında başlatmayı etkinleştirin. Aktif kullanım varsayılan olarak son 5 dakika içinde klavye/fare girdisi olmasıdır; bu, kişinin üretkenliğinin ölçümü değildir. Eski sürümlerin su/aktif kayıtları korunur; geçmiş bilgisayar açık süresi bulunmaz. Süreler 15 saniyede bir, metrik açılırken ve normal çıkışta kaydedilir; zorla kapanmada son birkaç saniye kaybolabilir.

Su, metrikler ve mola hatırlatmaları **API anahtarı, üyelik veya internet gerektirmez**. Bardak kaydı adet olarak tutulur; litreye çevrilmez.

## Ses, dil ve erişilebilirlik

- **Ctrl+Alt+V**: sesli konuşmayı başlatır; dinleme sürerken tekrar basılırsa sesi kapatır.
- İsteğe bağlı “Hey Memo” / “Hey Memocan” uyandırması.
- “2 bardak su içtim” ve “bugün kaç bardak su içtim” komutları.
- Ayarlar'dan Türkçe/İngilizce, avatar, mola süresi, mikrofon ve otomatik başlangıç.
- Menü düğmeleri ve metrik seçimleri klavyeyle kullanılabilir; yerel wxPython kontrolleri ekran okuyucu erişimi sağlar.

## İsteğe bağlı AI sohbeti

`.env.example` dosyasını `%APPDATA%\Memocan\.env` olarak kopyalayıp **kendi sağlayıcı anahtarını** ekle. Ollama Cloud, OpenRouter veya DeepSeek kullanılabilir. Örnek:

```dotenv
MEMOCAN_PROVIDER=openrouter
MEMOCAN_MODEL=openrouter/auto
OPENROUTER_API_KEY=kendi_anahtariniz
```

Sağlayıcı ücretleri sana aittir. Yerel su/rapor komutları haricindeki sohbet, seçilen sağlayıcıya gönderilir. Ses tanıma mevcut uygulamada çevrimiçi konuşma tanıma hizmeti kullanabilir; çevrimdışı yalnızca düğmeler/metrikler için garanti edilir. Mikrofon dinlemesini Ayarlar'dan kapatabilirsin.

Kişisel anahtarlar dağıtım paketine dahil edilmez. Sohbet geçmişi `%APPDATA%\Memocan\conversations.md`, istatistikler `stats.sqlite3`, ayarlar `config.json` dosyasında yerel tutulur. Bu dosyaları paylaşırken kişisel içerik içerebileceğini unutma.

## Geliştirici kurulumu

Windows, Python 3.12 ve Git:

```powershell
git clone https://github.com/mustan79/memocan_app.git
cd memocan_app
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
.\.venv\Scripts\python.exe main.py
```

Test ve Windows paketi:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
powershell -NoProfile -ExecutionPolicy Bypass -File .\build.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\package.ps1
```

Çıktı: `dist\Memocan-Windows.zip`. Paket; uygulama, tek tık kurulum dosyası, README, lisans ve boş anahtar şablonu içerir. `.env`, kullanıcı verileri, konuşmalar ve SQLite dosyaları eklenmez.

Bu sürümün dağıtım/test hedefi **Windows x64**'tür. macOS/Linux desteklenmiş dağıtım olarak sunulmaz; özellikle aktiflik takibi Windows API'lerine dayanır.

## Güncelleme ve kaldırma

Güncellemeden önce menüden Memocan'ı kapat; yeni ZIP'i çıkarıp kurulum dosyasını çalıştır. `%APPDATA%\Memocan` altındaki kayıtların korunur. Kaldırırken önce otomatik başlangıcı Ayarlar'dan kapat, uygulamadan çık, `%LOCALAPPDATA%\Memocan` klasörünü ve kısayollarını sil. Kullanım geçmişini de kaldırmak istersen `%APPDATA%\Memocan` klasörünü ayrıca sil.

## Lisans

[MIT](LICENSE). Hata bildirimi ve öneriler için [Issues](https://github.com/mustan79/memocan_app/issues).
