#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 HİSSE ANALİZ TELEGRAM BOTU - Basit ve Çalışır Versiyon
BIST 100 ve Dünya Borsaları için

KOMUTLAR:
/start - Ana menü
/analiz HISSE - Tam analiz (örn: /analiz THYAO)
/sinyal HISSE - İşlem sinyali
/rapor - Günlük piyasa raporu
/tara - Piyasa taraması
/potansiyel - %5+ potansiyel hisseler
/bist - BIST 100 taraması
/dunya - Dünya borsaları
/haber HISSE - Haber analizi
/temel HISSE - Temel analiz
/yardim - Yardım
"""
import logging
import os
import sys
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, CallbackContext, CallbackQueryHandler
)

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Config import
import config

# Modüller
import stock_scanner
from technical_analysis import TechnicalAnalyzer
from advanced_indicators import AdvancedIndicators
from news_analyzer import NewsAnalyzer, FundamentalAnalyzer
from learning_system import LearningSystem
from prediction_model import PredictionModel

# Global değişkenler
scanner_results = None
analiz_ediliyor = False
current_period = "3mo"  # Varsayılan periyot
periyot_ismi = "3 AYLIK"  # Varsayılan periyot adı

# Modül örnekleri
news_analyzer = NewsAnalyzer()
fundamental_analyzer = FundamentalAnalyzer()
advanced_indicators = AdvancedIndicators()
learning_system = LearningSystem()
prediction_model = PredictionModel()


# ============================================
# YARDIMCI FONKSİYONLAR
# ============================================

def create_menu_keyboard():
    """Ana menü butonları"""
    keyboard = [
        [InlineKeyboardButton("📊 ANALİZ YAP", callback_data="menu_analiz")],
        [InlineKeyboardButton("🎯 SİNYAL AL", callback_data="menu_sinyal")],
        [InlineKeyboardButton("📈 GÜNLÜK RAPOR", callback_data="cmd_rapor")],
        [InlineKeyboardButton("🔍 HİSSE TARAMA", callback_data="cmd_tara")],
        [InlineKeyboardButton("⚡ %5+ POTANSİYEL", callback_data="cmd_potansiyel")],
        [InlineKeyboardButton("🇹🇷 BIST 100", callback_data="cmd_bist")],
        [InlineKeyboardButton("🌍 DÜNYA", callback_data="cmd_dunya")],
        [InlineKeyboardButton("📰 HABERLER", callback_data="menu_haber")],
        [InlineKeyboardButton("🏢 TEMEL ANALİZ", callback_data="menu_temel")],
        [InlineKeyboardButton("📅 PERİYOT SEÇ", callback_data="menu_periyot")],
        [InlineKeyboardButton("📚 YARDIM", callback_data="cmd_yardim")],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_periyot_keyboard():
    """Analiz periyodu seçimi"""
    keyboard = [
        [InlineKeyboardButton("📊 1 GÜN (1D)", callback_data="periyot_1d")],
        [InlineKeyboardButton("📊 1 HAFTA (1W)", callback_data="periyot_1w")],
        [InlineKeyboardButton("📊 1 AY (1M)", callback_data="periyot_1mo")],
        [InlineKeyboardButton("📊 3 AY (3M)", callback_data="periyot_3mo")],
        [InlineKeyboardButton("📊 6 AY (6M)", callback_data="periyot_6mo")],
        [InlineKeyboardButton("📊 1 YIL (1Y)", callback_data="periyot_1y")],
        [InlineKeyboardButton("◀️ ANA MENÜ", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def create_hisse_listesi_keyboard(analiz_tipi="analiz"):
    """Hisse listesi butonları"""
    keyboard = []
    bist_hisseleri = [
        "THYAO", "EREGL", "ASELS", "GARAN", "SAHOL",
        "KCHOL", "TUPRS", "ISCTR", "YKBNK", "HALKB",
        "AKBNK", "BIMAS", "SISE", "KOZAL", "TOASO"
    ]
    for hisse in bist_hisseleri:
        keyboard.append([InlineKeyboardButton(
            f"🇹🇷 {hisse}",
            callback_data=f"{analiz_tipi}_{hisse}"
        )])

    world_hisseleri = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA"]
    for hisse in world_hisseleri:
        keyboard.append([InlineKeyboardButton(
            f"🌍 {hisse}",
            callback_data=f"{analiz_tipi}_{hisse}"
        )])

    keyboard.append([InlineKeyboardButton("◀️ ANA MENÜ", callback_data="back_menu")])
    return InlineKeyboardMarkup(keyboard)


def create_analiz_sonrasi_keyboard(hisse):
    """Analiz sonrası butonlar"""
    keyboard = [
        [InlineKeyboardButton(f"📊 {hisse} YENİDEN ANALİZ", callback_data=f"analiz_{hisse}")],
        [InlineKeyboardButton(f"🎯 {hisse} SİNYAL", callback_data=f"sinyal_{hisse}")],
        [InlineKeyboardButton(f"📰 {hisse} HABER", callback_data=f"haber_{hisse}")],
        [InlineKeyboardButton(f"🏢 {hisse} TEMEL", callback_data=f"temel_{hisse}")],
        [InlineKeyboardButton("◀️ ANA MENÜ", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================
# KOMUT HANDLERLARI
# ============================================

async def start_command(update: Update, context: CallbackContext):
    """Başlangıç komutu"""
    text = """
🏛️ *HOŞGELDİNİZ!*

Ben sizin **Hisse Analiz Botunuzum**.

📊 *YETENEKLERİM:*

🔹 BIST 100 + Dünya Borsaları
🔹 Teknik Analiz (RSI, MACD, Bollinger, Fibonacci...)
🔹 İşlem Sinyalleri
🔹 Haber ve Duygu Analizi
🔹 Temel Analiz

⚠️ *UYARI:* Yatırım tavsiyesi DEĞİLDİR!

Kullanmak için aşağıdaki butonları kullanın veya komut yazın.
    """
    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=create_menu_keyboard()
    )


async def yardim_command(update: Update, context: CallbackContext):
    """Yardım komutu"""
    text = """
📚 *KOMUT LİSTESİ*

━━━━━━━━━━━━━━━━━━━━━━━━

📝 *Temel Komutlar:*

/start - Botu başlat
/yardim - Bu yardım menüsü

📊 *Analiz Komutları:*

/analiz HISSE - Tam analiz
  Örnek: `/analiz THYAO`

/sinyal HISSE - İşlem sinyali
  Örnek: `/sinyal AAPL`

/haber HISSE - Haber analizi
  Örnek: `/haber TSLA`

/temel HISSE - Temel analiz
  Örnek: `/temel GARAN`

📈 *Tarama Komutları:*

/rapor - Günlük piyasa raporu
/tara - Piyasa taraması
/potansiyel - %5+ potansiyel
/bist - BIST 100 taraması
/dunya - Dünya borsaları

━━━━━━━━━━━━━━━━━━━━━━━━

💡 *Hızlı Kullanım:*
Sadece hisse kodunu yazın!
Örnek: `THYAO` veya `AAPL`

━━━━━━━━━━━━━━━━━━━━━━━━
    """
    await update.message.reply_text(text, parse_mode='Markdown')


async def analiz_command(update: Update, context: CallbackContext):
    """Analiz komutu"""
    global analiz_ediliyor

    if not context.args:
        await update.message.reply_text(
            "📊 *Analiz*\n\nKullanım: `/analiz THYAO`\n\nVeya aşağıdan hisse seçin:",
            parse_mode='Markdown',
            reply_markup=create_hisse_listesi_keyboard("analiz")
        )
        return

    hisse = context.args[0].upper().strip()
    await hisse_analiz_et(update, context, hisse)


async def sinyal_command(update: Update, context: CallbackContext):
    """Sinyal komutu"""
    if not context.args:
        await update.message.reply_text(
            "🎯 *Sinyal*\n\nKullanım: `/sinyal THYAO`\n\nVeya aşağıdan hisse seçin:",
            parse_mode='Markdown',
            reply_markup=create_hisse_listesi_keyboard("sinyal")
        )
        return

    hisse = context.args[0].upper().strip()
    await hisse_sinyal_et(update, context, hisse)


async def haber_command(update: Update, context: CallbackContext):
    """Haber komutu"""
    if not context.args:
        await update.message.reply_text(
            "📰 *Haber Analizi*\n\nKullanım: `/haber THYAO`\n\nVeya aşağıdan hisse seçin:",
            parse_mode='Markdown',
            reply_markup=create_hisse_listesi_keyboard("haber")
        )
        return

    hisse = context.args[0].upper().strip()
    await hisse_haber_analiz_et(update, context, hisse)


async def temel_command(update: Update, context: CallbackContext):
    """Temel analiz komutu"""
    if not context.args:
        await update.message.reply_text(
            "🏢 *Temel Analiz*\n\nKullanım: `/temel THYAO`\n\nVeya aşağıdan hisse seçin:",
            parse_mode='Markdown',
            reply_markup=create_hisse_listesi_keyboard("temel")
        )
        return

    hisse = context.args[0].upper().strip()
    await hisse_temel_analiz_et(update, context, hisse)


async def rapor_command(update: Update, context: CallbackContext):
    """Günlük rapor komutu"""
    await update.message.reply_text("📊 *Günlük rapor hazırlanıyor...*", parse_mode='Markdown')

    try:
        scanner = stock_scanner.StockScanner()
        scanner.scan_bist_100(limit=15)
        scanner.filter_high_potential()

        if scanner.high_potential_stocks:
            report = scanner.format_daily_report()
        else:
            report = "❌ Bugün için yeterli potansiyel hisse bulunamadı."

        await update.message.reply_text(report, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Rapor hatası: {e}")
        await update.message.reply_text(f"❌ Hata: {str(e)}")


async def tara_command(update: Update, context: CallbackContext):
    """Piyasa tarama komutu"""
    await update.message.reply_text("🔍 *Piyasa taranıyor...*", parse_mode='Markdown')

    try:
        scanner = stock_scanner.StockScanner()
        scanner.scan_bist_100(limit=20)
        scanner.scan_world_markets()
        scanner.filter_high_potential()

        report = scanner.format_daily_report()
        await update.message.reply_text(report, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Tarama hatası: {e}")
        await update.message.reply_text(f"❌ Hata: {str(e)}")


async def potansiyel_command(update: Update, context: CallbackContext):
    """Yüksek potansiyel komutu"""
    await update.message.reply_text("⚡ *%5+ potansiyel hisseler aranıyor...*", parse_mode='Markdown')

    try:
        scanner = stock_scanner.StockScanner()
        scanner.scan_bist_100(limit=30)
        scanner.filter_high_potential(min_percent=5)

        if scanner.high_potential_stocks:
            report = scanner.format_daily_report(top_stocks=scanner.high_potential_stocks[:10])
        else:
            report = "❌ %5 üzeri potansiyel hisse bulunamadı."

        await update.message.reply_text(report, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Potansiyel hatası: {e}")
        await update.message.reply_text(f"❌ Hata: {str(e)}")


async def bist_command(update: Update, context: CallbackContext):
    """BIST komutu"""
    await update.message.reply_text("🇹🇷 *BIST 100 taranıyor...*", parse_mode='Markdown')

    try:
        scanner = stock_scanner.StockScanner()
        scanner.scan_bist_100(limit=25)
        scanner.filter_high_potential()

        report = scanner.format_daily_report()
        await update.message.reply_text(report, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"BIST hatası: {e}")
        await update.message.reply_text(f"❌ Hata: {str(e)}")


async def dunya_command(update: Update, context: CallbackContext):
    """Dünya komutu"""
    await update.message.reply_text("🌍 *Dünya borsaları taranıyor...*", parse_mode='Markdown')

    try:
        scanner = stock_scanner.StockScanner()
        scanner.scan_world_markets()
        scanner.filter_high_potential()

        report = scanner.format_daily_report()
        await update.message.reply_text(report, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Dünya hatası: {e}")
        await update.message.reply_text(f"❌ Hata: {str(e)}")


# ============================================
# ANALIZ FONKSIYONLARI
# ============================================

async def hisse_analiz_et(update_or_query, context, hisse):
    """Hisse analizi yap"""
    global analiz_ediliyor, current_period, periyot_ismi

    if analiz_ediliyor:
        text = "⏳ Analiz yapılıyor, lütfen bekleyin..."
        if hasattr(update_or_query, 'message'):
            await update_or_query.message.reply_text(text)
        else:
            await update_or_query.callback_query.answer(text, show_alert=True)
        return

    analiz_ediliyor = True

    # Mesaj gönder - İLERLEME
    msg_text = f"📊 *{hisse}* analiz ediliyor...\n\n⏳ Veriler alınıyor... [%0]"
    if hasattr(update_or_query, 'message'):
        msg = await update_or_query.message.reply_text(msg_text, parse_mode='Markdown')
    else:
        await update_or_query.callback_query.answer()
        msg = await update_or_query.callback_query.edit_message_text(msg_text, parse_mode='Markdown')

    try:
        # BIST kontrolü
        symbol = hisse
        if hisse in [s.replace('.IS', '') for s in config.BIST_100_STOCKS]:
            if not hisse.endswith('.IS'):
                symbol = f"{hisse}.IS"

        # İLERLEME 1: Veri çekme
        await msg.edit_text(f"📊 *{hisse}* analiz ediliyor...\n\n⏳ Veriler çekiliyor... [%%20]", parse_mode='Markdown')

        # Teknik analiz - periyot kullan
        analyzer = TechnicalAnalyzer(symbol, period=current_period)
        tech_data = analyzer.calculate_all()

        await msg.edit_text(f"📊 *{hisse}* analiz ediliyor...\n\n⏳ Teknik analiz yapılıyor... [%%40]", parse_mode='Markdown')

        if not tech_data:
            await msg.edit_text(f"❌ {hisse} için veri bulunamadı.")
            analiz_ediliyor = False
            return

        # İLERLEME 2: İleri göstergeler
        await msg.edit_text(f"📊 *{hisse}* analiz ediliyor...\n\n⏳ İleri göstergeler hesaplanıyor... [%%60]", parse_mode='Markdown')

        analyzer2 = TechnicalAnalyzer(symbol, period=current_period)
        if analyzer2.fetch_data():
            adv = advanced_indicators.calculate_all_advanced(analyzer2.data)
        else:
            adv = {}

        # İLERLEME 3: Haber ve temel analiz
        await msg.edit_text(f"📊 *{hisse}* analiz ediliyor...\n\n⏳ Haber analizi yapılıyor... [%%80]", parse_mode='Markdown')

        news_data = news_analyzer.analyze_news_for_stock(symbol)
        sentiment = news_data.get('avg_sentiment', 0)
        fund_data = fundamental_analyzer.analyze_fundamentals(symbol)

        # İLERLEME 4: Sinyal hesaplama
        await msg.edit_text(f"📊 *{hisse}* analiz ediliyor...\n\n⏳ Sinyal hesaplanıyor... [%%90]", parse_mode='Markdown')

        signal = prediction_model.generate_trade_signal(symbol, tech_data, fund_data, sentiment)

        # İLERLEME 5: Tamamlandı
        await msg.edit_text(f"✅ *{hisse}* analiz tamamlandı! [%%100]\n\nRapor hazırlanıyor...", parse_mode='Markdown')

        # Rapor oluştur
        report = f"""📊 *{hisse} - DETAYLI ANALIZ*
━━━━━━━━━━━━━━━━━━━━

⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}
📅 Periyot: *{periyot_ismi}*

💰 *FIYAT BILGILERI*
  Güncel: {tech_data.get('current_price', 'N/A')}
  Değişim: %{tech_data.get('price_change', 0):+.2f}

📈 *TEKNIK GOSTERGELER*
  RSI (14): {tech_data.get('rsi', 'N/A')}
  MACD: {tech_data.get('macd', 'N/A')}
  Stokastik: {tech_data.get('stoch_k', 'N/A')}

📊 *HAREKETLI ORTALAMALAR*
  SMA 20: {tech_data.get('sma_20', 'N/A')}
  SMA 50: {tech_data.get('sma_50', 'N/A')}
  SMA 200: {tech_data.get('sma_200', 'N/A')}

🎯 *SEVIYELER*
  Direnç: {tech_data.get('resistance', 'N/A')}
  Destek: {tech_data.get('support', 'N/A')}

━━━━━━━━━━━━━━━━━━━━

🎯 *ISLEM SINYALI (SPOT)*
  Yön: *{signal['direction']}*
  Güven: %{signal['confidence'] * 100:.0f}
  Hedef: {signal['target_price']} (%{signal['target_percent']:+.2f})
  Stop-Loss: {signal['stop_loss']}
  Risk/Ödül: {signal['risk_reward']:.2f}

━━━━━━━━━━━━━━━━━━━━

⚠️ *YATIRIM TAVSIYESI DEGILDIR!*
"""

        await msg.edit_text(report, parse_mode='Markdown', reply_markup=create_analiz_sonrasi_keyboard(hisse))

    except Exception as e:
        logger.error(f"Analiz hatası ({hisse}): {e}")
        await msg.edit_text(f"❌ Analiz hatası: {str(e)}")
    finally:
        analiz_ediliyor = False


async def hisse_sinyal_et(update_or_query, context, hisse):
    """Hisse sinyali al"""
    # Mesaj gönder
    msg_text = f"🎯 *{hisse}* sinyali hesaplanıyor..."
    if hasattr(update_or_query, 'message'):
        msg = await update_or_query.message.reply_text(msg_text, parse_mode='Markdown')
    else:
        await update_or_query.callback_query.answer()
        msg = await update_or_query.callback_query.edit_message_text(msg_text, parse_mode='Markdown')

    try:
        symbol = hisse
        if hisse in [s.replace('.IS', '') for s in config.BIST_100_STOCKS]:
            symbol = f"{hisse}.IS"

        # Teknik analiz
        analyzer = TechnicalAnalyzer(symbol, period="2mo")
        tech_data = analyzer.calculate_all()

        if not tech_data:
            await msg.edit_text(f"❌ {hisse} için veri bulunamadı.")
            return

        # Haber ve temel
        news_data = news_analyzer.analyze_news_for_stock(symbol)
        fund_data = fundamental_analyzer.analyze_fundamentals(symbol)
        sentiment = news_data.get('avg_sentiment', 0)

        # Sinyal
        signal = prediction_model.generate_trade_signal(symbol, tech_data, fund_data, sentiment)

        # Renk ve emoji
        if signal['direction'] == 'AL':
            emoji, renk = "📈", "✅"
        elif signal['direction'] == 'SAT':
            emoji, renk = "📉", "❌"
        else:
            emoji, renk = "⚖️", "⚠️"

        report = f"""{emoji} *{hisse} ISLEM SINYALI*
━━━━━━━━━━━━━━━━━━━━

🎯 Yön: *{signal['direction']}*
📊 Güven: %{signal['confidence'] * 100:.0f}

💰 *FIYAT BILGILERI*
  Giriş: {signal['entry_price']:.2f}
  Hedef: {signal['target_price']:.2f} (%{signal['target_percent']:+.2f})
  Stop-Loss: {signal['stop_loss']:.2f}

⚖️ Risk/Ödül: *{signal['risk_reward']:.2f}*

━━━━━━━━━━━━━━━━━━━━

RSI: {tech_data.get('rsi', 'N/A')}
MACD: {tech_data.get('macd', 'N/A')}

⚠️ *YATIRIM TAVSIYESI DEGILDIR!*
"""

        await msg.edit_text(report, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Sinyal hatası ({hisse}): {e}")
        await msg.edit_text(f"❌ Sinyal hatası: {str(e)}")


async def hisse_haber_analiz_et(update_or_query, context, hisse):
    """Hisse haber analizi"""
    msg_text = f"📰 *{hisse}* haberleri analiz ediliyor..."
    if hasattr(update_or_query, 'message'):
        msg = await update_or_query.message.reply_text(msg_text, parse_mode='Markdown')
    else:
        await update_or_query.callback_query.answer()
        msg = await update_or_query.callback_query.edit_message_text(msg_text, parse_mode='Markdown')

    try:
        symbol = hisse
        if hisse in [s.replace('.IS', '') for s in config.BIST_100_STOCKS]:
            symbol = f"{hisse}.IS"

        report = news_analyzer.get_news_summary(symbol)
        await msg.edit_text(report, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Haber hatası ({hisse}): {e}")
        await msg.edit_text(f"❌ Haber hatası: {str(e)}")


async def hisse_temel_analiz_et(update_or_query, context, hisse):
    """Hisse temel analizi"""
    msg_text = f"🏢 *{hisse}* temel analiz yapılıyor..."
    if hasattr(update_or_query, 'message'):
        msg = await update_or_query.message.reply_text(msg_text, parse_mode='Markdown')
    else:
        await update_or_query.callback_query.answer()
        msg = await update_or_query.callback_query.edit_message_text(msg_text, parse_mode='Markdown')

    try:
        report = fundamental_analyzer.format_fundamental_report(hisse)
        await msg.edit_text(report, parse_mode='Markdown')

    except Exception as e:
        logger.error(f"Temel analiz hatası ({hisse}): {e}")
        await msg.edit_text(f"❌ Temel analiz hatası: {str(e)}")


# ============================================
# CALLBACK HANDLER
# ============================================

async def button_callback(update: Update, context: CallbackContext):
    """Buton tıklamaları"""
    global current_period, periyot_ismi

    query = update.callback_query
    await query.answer()

    data = query.data

    # Ana menü
    if data == "back_menu":
        text = "🏛️ *ANA MENÜ*\n\nNe yapmak istersiniz?\n📅 Aktif periyot: *{}*".format(periyot_ismi)
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=create_menu_keyboard())
        return

    # Periyot seçimi
    elif data == "menu_periyot":
        text = "📅 *Analiz periyodunu seçin:*\n\nMevcut periyot: *{}*".format(periyot_ismi)
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=create_periyot_keyboard())
        return

    elif data.startswith("periyot_"):
        period_map = {
            "periyot_1d": ("1d", "1 GÜNLÜK"),
            "periyot_1w": ("1wk", "1 HAFTALIK"),
            "periyot_1mo": ("1mo", "1 AYLIK"),
            "periyot_3mo": ("3mo", "3 AYLIK"),
            "periyot_6mo": ("6mo", "6 AYLIK"),
            "periyot_1y": ("1y", "1 YILLIK"),
        }
        if data in period_map:
            current_period, periyot_ismi = period_map[data]
            await query.answer(f"✅ Periyot ayarlandı: {periyot_ismi}", show_alert=True)
            text = f"🏛️ *ANA MENÜ*\n\n📅 Aktif periyot: *{periyot_ismi}*\n\nNe yapmak istersiniz?"
            await query.edit_message_text(text, parse_mode='Markdown', reply_markup=create_menu_keyboard())
        return

    # Menü seçimleri
    elif data == "menu_analiz":
        text = "📊 *Hangi hisseyi analiz etmemi istersiniz?*"
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=create_hisse_listesi_keyboard("analiz"))
        return

    elif data == "menu_sinyal":
        text = "🎯 *Hangi hisse için sinyal almak istersiniz?*"
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=create_hisse_listesi_keyboard("sinyal"))
        return

    elif data == "menu_haber":
        text = "📰 *Hangi hisse için haber analizi?*"
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=create_hisse_listesi_keyboard("haber"))
        return

    elif data == "menu_temel":
        text = "🏢 *Hangi hisse için temel analiz?*"
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=create_hisse_listesi_keyboard("temel"))
        return

    elif data == "cmd_rapor":
        await query.edit_message_text("📊 *Günlük rapor hazırlanıyor...*\n\n⏳ Lütfen bekleyin...", parse_mode='Markdown')
        await rapor_command(update, context)
        return

    elif data == "cmd_tara":
        await query.edit_message_text("🔍 *Piyasa taranıyor...*\n\n⏳ Lütfen bekleyin...", parse_mode='Markdown')
        await tara_command(update, context)
        return

    elif data == "cmd_potansiyel":
        await query.edit_message_text("⚡ *%5+ potansiyel aranıyor...*\n\n⏳ Lütfen bekleyin...", parse_mode='Markdown')
        await potansiyel_command(update, context)
        return

    elif data == "cmd_bist":
        await query.edit_message_text("🇹🇷 *BIST 100 taranıyor...*\n\n⏳ Lütfen bekleyin...", parse_mode='Markdown')
        await bist_command(update, context)
        return

    elif data == "cmd_dunya":
        await query.edit_message_text("🌍 *Dünya borsaları taranıyor...*\n\n⏳ Lütfen bekleyin...", parse_mode='Markdown')
        await dunya_command(update, context)
        return

    elif data == "cmd_yardim":
        await yardim_command(update, context)
        return

    # Hissse analizleri
    elif data.startswith("analiz_"):
        hisse = data.replace("analiz_", "")
        await hisse_analiz_et(update, context, hisse)
        return

    elif data.startswith("sinyal_"):
        hisse = data.replace("sinyal_", "")
        await hisse_sinyal_et(update, context, hisse)
        return

    elif data.startswith("haber_"):
        hisse = data.replace("haber_", "")
        await hisse_haber_analiz_et(update, context, hisse)
        return

    elif data.startswith("temel_"):
        hisse = data.replace("temel_", "")
        await hisse_temel_analiz_et(update, context, hisse)
        return

    else:
        await query.answer(f"Bilinmeyen komut: {data}", show_alert=True)


# ============================================
# MESAJ HANDLER
# ============================================

async def mesaj_handler(update: Update, context: CallbackContext):
    """Mesaj işleyici - Direkt hisse sorgusu"""
    text = update.message.text.strip().upper()

    # Komutları atlama
    if text.startswith('/'):
        return

    # Geçerli hisse mi kontrolü
    valid_symbols = [s.replace('.IS', '') for s in config.BIST_100_STOCKS]
    for region in config.WORLD_MARKETS.values():
        valid_symbols.extend(region.get('stocks', []))

    if any(text == s for s in valid_symbols) or (len(text) <= 6 and text.isalpha()):
        await hisse_analiz_et(update, context, text)


# ============================================
# HATA HANDLER
# ============================================

async def error_handler(update: Update, context: CallbackContext):
    """Hata yönetimi"""
    logger.error(f"Hata: {context.error}")


# ============================================
# BOT BAŞLATMA
# ============================================

def main():
    """Ana fonksiyon"""
    print("=" * 50)
    print("📊 HİSSE ANALİZ BOTU BAŞLATILIYOR")
    print("=" * 50)

    bot_token = config.TELEGRAM_BOT_TOKEN
    if not bot_token or bot_token == "YOUR_BOT_TOKEN_HERE":
        print("❌ HATA: TELEGRAM_BOT_TOKEN ayarlanmamış!")
        print("   config.py dosyasına token ekleyin.")
        sys.exit(1)

    print(f"✅ Token: {bot_token[:10]}...")

    # Application oluştur
    application = Application.builder().token(bot_token).build()

    # Komutlar
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("yardim", yardim_command))
    application.add_handler(CommandHandler("help", yardim_command))
    application.add_handler(CommandHandler("analiz", analiz_command))
    application.add_handler(CommandHandler("analyze", analiz_command))
    application.add_handler(CommandHandler("sinyal", sinyal_command))
    application.add_handler(CommandHandler("signal", sinyal_command))
    application.add_handler(CommandHandler("haber", haber_command))
    application.add_handler(CommandHandler("temel", temel_command))
    application.add_handler(CommandHandler("fundamental", temel_command))
    application.add_handler(CommandHandler("rapor", rapor_command))
    application.add_handler(CommandHandler("report", rapor_command))
    application.add_handler(CommandHandler("tara", tara_command))
    application.add_handler(CommandHandler("tarama", tara_command))
    application.add_handler(CommandHandler("potansiyel", potansiyel_command))
    application.add_handler(CommandHandler("bist", bist_command))
    application.add_handler(CommandHandler("dunya", dunya_command))
    application.add_handler(CommandHandler("world", dunya_command))

    # Callback handler (BUTONLAR)
    application.add_handler(CallbackQueryHandler(button_callback))

    # Mesaj handler (direkt hisse yazma)
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        mesaj_handler
    ))

    # Hata yönetimi
    application.add_error_handler(error_handler)

    print("✅ Tüm komutlar kaydedildi!")
    print("📱 Telegram'da /start yazın")
    print("=" * 50)

    # Botu çalıştır
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
