# Memocan Desktop Companion

Memocan, düşük kaynak tüketimli bir masaüstü çalışma arkadaşıdır. Sürüklenebilir
avatar; aktif bilgisayar kullanımını, molaları ve su kayıtlarını yerel SQLite
veritabanında tutar.

## Ön demo

- Windows aktivite/boşta kalma takibi
- 25 dakika sonunda mola hatırlatması
- Su kaydı ve 7 günlük özet
- Robot, kedi, baykuş ve ördek avatarları
- OpenAI uyumlu Ollama Cloud, OpenRouter veya DeepSeek bağlantısı
- İsteğe bağlı TTS ve mikrofon desteği

## Kurulum ve çalıştırma

PowerShell'de:

```powershell
cd D:\mt_proje\memocan_app
.\setup.ps1
.\.venv\Scripts\python.exe main.py
```

PowerShell betik çalıştırmayı engellerse:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

Uygulama `.env` dosyasını otomatik yükler. Sağlayıcı örneği:

```dotenv
MEMOCAN_PROVIDER=ollama_cloud
MEMOCAN_MODEL=gemma4:31b-cloud
OLLAMA_API_KEY=...
```

`MEMOCAN_PROVIDER` için `openrouter` veya `deepseek` de kullanılabilir. İlgili
anahtarlar sırasıyla `OPENROUTER_API_KEY` ve `DEEPSEEK_API_KEY` olur. `.env`
Git tarafından yok sayılır; örnek yapı `.env.example` dosyasındadır.

## Erişilebilir kullanım

- `Ctrl+Alt+M`: ekran okuyucuyla gezilebilen yerel Memocan menüsü
- `Ctrl+Alt+V`: ses kapalıysa açar ve sesli konuşmayı başlatır; dinleme sürerken
  tekrar basılırsa sesi kapatır
- `Hey Memo` veya `Hey Memocan`: sesli konuşmayı başlatır
- Avatar tıklaması erişilebilir menüyü, sağ tık ayarları açar

Yazılı sohbet bulunmaz. `Su içtim`, `rapor` ve genel sohbet sesle kullanılabilir.
Sesli yanıtlar kapalıyken süre hatırlatmaları sistem bip sesiyle verilir. Ayarlardan
Türkçe/İngilizce, sürekli uyandırma dinlemesi ve oturum açılışında başlatma seçilebilir.

## Dağıtım

Son kullanıcı için önerilen biçim, Python gerektirmeyen işletim sistemi paketidir.
Windows paketi:

```powershell
.\build.ps1
.\dist\Memocan.exe
```

Windows'ta tek tık yerel kurulum için:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Bu işlem uygulamayı `%LOCALAPPDATA%\Memocan` altına kurar, masaüstü ve Başlat
menüsü kısayollarını oluşturur ve kullanıcı oturum açtığında otomatik başlatır.
Türkçe seçiliyken Windows'un Microsoft Tolga sesi, İngilizce seçiliyken İngilizce
SAPI sesi kullanılır.

macOS ve Linux kendi işletim sistemleri üzerinde `./build.sh` ile paketlenir.
`.github/workflows/build.yml`, üç işletim sistemi için ayrı paket üretir; PyInstaller
çapraz derleyici olmadığı için her hedef kendi runner'ında oluşturulur. Paketlenmiş
uygulamada `.env`, çalıştırılabilir dosyayla aynı klasöre konur.

İstatistikler `%APPDATA%\Memocan\stats.sqlite3`, kullanıcı ayarları ise
`%APPDATA%\Memocan\config.json` altında yerel olarak saklanır.
