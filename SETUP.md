# 🤖 Stock Telegram Bot - Kurulum Talimatları

## 📦 Bu Dosyaları İndirin
Dosyalar: `stock-telegram-bot/` klasöründe

## 🚀 Render.com'a Kurulum (ÜCRETSİZ)

### Adım 1: GitHub'a Yükleyin
1. https://github.com/new adresinde **New repository** oluşturun
2. İsim: `stock-telegram-bot`
3. **Create repository** tıklayın

### Adım 2: Dosyaları Yükleyin
1. Oluşturduğunuz repo'ya gidin
2. **Add file** > **Upload files** tıklayın
3. Tüm dosyaları sürükleyip bırakın
4. **Commit changes** tıklayın

### Adım 3: Render.com'a Bağlayın
1. https://render.com adresinde hesap açın (GitHub ile giriş yapın)
2. **New** > **Background Worker** tıklayın
3. Ayarlar:
   - **Name**: `stock-telegram-bot`
   - **Region**: Frankfurt
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`

4. **Environment Variables** ekleyin:
   - Key: `TELEGRAM_BOT_TOKEN`
   - Value: `8745144801:AAGyQbL7loQKVaR8amZ5IxWLzfmqb6cfEiI`

5. **Create Worker** tıklayın

### Adım 4: Tamam!
- ~1-2 dakika sonra bot çalışmaya başlar
- Render dashboard'dan log'ları kontrol edebilirsiniz

---

## 📱 Telegram'da Kullanım
Bot: **@tradehaluk_bot**

Komutlar:
- `/start` - Ana menü
- `/rapor` - Günlük rapor
- `/potansiyel` - %5+ hisseler
- `/analiz THYAO` - Tek hisse analizi

---

## ✅ Özellikler
- BIST 100 hisse analizi
- SPOT işlem sinyalleri
- %5+ potansiyel tarama
- Periyot seçimi (1D, 1W, 1M, 3M, 6M, 1Y)
- İlerleme takibi
- 7/24 çalışma (Render.com'da)

---

## 🔧 Sorun Giderme
Bot çalışmazsa:
1. Render dashboard > Logs kontrol edin
2. Environment Variables'ı kontrol edin
3. Build log'larını inceleyin
