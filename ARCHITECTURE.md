# Memocan mimarisi ve yol haritası

## Mevcut MVP

`main.py` uygulamayı başlatır. `app.py` avatar penceresi, aktivite zamanlayıcısı,
sohbet ve ayar panelini yönetir. `storage.py` günlük aktif süre, uzakta kalma
süresi ve su sayısını SQLite'a yazar. `llm.py` OpenAI uyumlu Ollama Cloud
endpointine bağlanır. `voice.py` pyttsx3 TTS ve SpeechRecognition STT için
opsiyonel adaptördür.

## Güvenlik ve mahremiyet

İstatistikler varsayılan olarak yalnızca yerel makinede tutulur. Mikrofon dinleme
varsayılan olarak kapalıdır. LLM anahtarı uygulama klasörüne değil işletim sistemi
kullanıcı ayar dizinine yazılır; üretim sürümünde Windows Credential Manager veya
keyring kullanılmalıdır.

## Sonraki aşamalar

1. Windows başlangıç kaydı ve sistem tepsisi (tray) menüsü.
2. Gerçek PNG/SVG avatar animasyonları ve konuşma durumları.
3. Wake-word için sürekli Google STT yerine yerel düşük güç motoru.
4. Ayarlar ve haftalık rapor için daha zengin grafik arayüzü.
5. Kullanıcı izniyle Supabase senkronizasyonu; anonimleştirilmiş istatistikler.
6. Sağlık önerilerinde kişisel tıbbi tavsiye vermeyen, güvenli metin şablonları.
