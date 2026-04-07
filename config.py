# Hisse Analiz Botu - Konfigürasyon
import os

# Telegram Ayarları
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8745144801:AAGyQbL7loQKVaR8amZ5IxWLzfmqb6cfEiI")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "tradehaluk_bot")

# BIST 100 Hisse Listesi
BIST_100_STOCKS = [
    "THYAO.IS", "EREGL.IS", "ASELS.IS", "GARAN.IS", "AKBNK.IS",
    "ISCTR.IS", "YKBNK.IS", "SAHOL.IS", "TUPRS.IS", "BIMAS.IS",
    "KCHOL.IS", "KOZAL.IS", "Turkcell.IS", "VAKBN.IS", "HALKB.IS",
    "SISE.IS", "TAVHL.IS", "ENKAI.IS", "OTKAR.IS", "ARCLK.IS",
    "FROTO.IS", "TOASO.IS", "CCOLA.IS", "KORDS.IS", "ODAS.IS",
    "GUBRF.IS", "AGHOL.IS", "AEFES.IS", "PETKM.IS", "PKART.IS",
    "LOGO.IS", "KORDS.IS", "SILECE.IS", "MGROS.IS", "TRILOG.IS",
    "BUCIM.IS", "ULKER.IS", "COCOC.IS", "SASA.IS", "KARSN.IS",
    "ALARK.IS", "VESTL.IS", "KNFRT.IS", "BRKSN.IS", "ZOREN.IS",
    "IZOCAM.IS", "DOAS.IS", "HEKTS.IS", "BAGFS.IS", "KATMR.IS",
    "PGSUS.IS", "KCHOL.IS", "TTKOM.IS", "TELCO.IS", "GYDNY.IS",
    "TMSN.IS", "CLEBI.IS", "BASGZ.IS", "MAVI.IS", "MIA.IS",
    "SOKM.IS", "BFREN.IS", "OTKER.IS", "KONTR.IS", "KONKA.IS",
    "SEKURK.IS", "SEKFK.IS", "ISMEN.IS", "ITFGH.IS", "KLNMA.IS",
    "MTRKS.IS", "NTHOL.IS", "OBAMS.IS", "SNGYO.IS", "TNBLO.IS",
    "TRCAS.IS", "TSKB.IS", "TTRAK.IS", "TURSG.IS", "UNYEC.IS",
    "YEOTK.IS", "YKSLN.IS", "YYAPI.IS", "ZEGHD.IS", "ERBOS.IS",
    "ECZAC.IS", "ENSRI.IS", "TEZOL.IS", "MPARK.IS", "QUAGR.IS"
]

# Dünya Borsaları - Önemli Endeksler ve Hisseler
WORLD_MARKETS = {
    "ABD": {
        "name": "Amerika Borsası",
        "indexes": ["^GSPC", "^IXIC", "^DJI"],  # S&P 500, Nasdaq, Dow Jones
        "stocks": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "AMD", "INTC", "NFLX"]
    },
    "AVRUPA": {
        "name": "Avrupa Borsası",
        "indexes": ["^FTSE", "^GDAXI", "^FCHI"],  # FTSE 100, DAX, CAC 40
        "stocks": ["SAP.DE", "ASML.AS", "SHELL.L", "HSBA.L", "BP.L", "SIE.DE", "BMW.DE", "VOW.DE"]
    },
    "ASYA": {
        "name": "Asya Borsası",
        "indexes": ["^N225", "^HSI", "000001.SS"],  # Nikkei 225, Hang Seng, Shanghai
        "stocks": ["9988.HK", "0700.HK", "TCEHY", "BABA", "TSM", "SONY", "TM", "7203.T"]
    },
    "INGILTERE": {
        "name": "İngiltere Borsası",
        "indexes": ["^FTSE"],
        "stocks": ["HSBA.L", "SHEL.L", "BP.L", "RIO.L", "GSK.L", "ULVR.L"]
    },
    "ALMANYA": {
        "name": "Almanya Borsası",
        "indexes": ["^GDAXI"],
        "stocks": ["SAP.DE", "SIE.DE", "ALV.DE", "DB1.DE", "DHL.DE", "BMW.DE"]
    }
}

# Analiz Parametreleri
MIN_POTENTIAL_PERCENT = 5.0  # Minimum potansiyel yüzdesi
DAILY_STOCK_COUNT = 10  # Günlük analiz edilecek hisse sayısı
ANALYSIS_PERIOD = "1mo"  # Analiz periyodu (1d, 1wk, 1mo, 3mo)

# Bildirim Saatleri (TSI - Türkiye Saati)
DAILY_REPORT_HOUR = 9  # Sabah raporu
DAILY_REPORT_MINUTE = 0

# Teknik Gösterge Parametreleri
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
MA_PERIODS = [20, 50, 200]
