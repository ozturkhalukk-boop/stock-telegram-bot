# Teknik Analiz Modülü
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import config


def calculate_rsi(prices, period=14):
    """RSI hesaplama"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices, fast=12, slow=26, signal=9):
    """MACD hesaplama"""
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_sma(prices, period):
    """Basit Hareketli Ortalama"""
    return prices.rolling(window=period).mean()


def calculate_ema(prices, period):
    """Üstel Hareketli Ortalama"""
    return prices.ewm(span=period, adjust=False).mean()


def calculate_stochastic(high, low, close, period=14):
    """Stokastik Osilatör"""
    lowest_low = low.rolling(window=period).min()
    highest_high = high.rolling(window=period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=3).mean()
    return k, d


def calculate_bollinger_bands(prices, period=20, std_dev=2):
    """Bollinger Bantları"""
    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower


def calculate_atr(high, low, close, period=14):
    """Average True Range"""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


class TechnicalAnalyzer:
    """Teknik analiz sınıfı - RSI, MACD, Destek/Direnç, Grafik analizi"""

    def __init__(self, symbol, period="1mo"):
        self.symbol = symbol
        self.period = period
        self.data = None
        self.analysis = {}

    def fetch_data(self):
        """Yahoo Finance'den veri çekme"""
        try:
            stock = yf.Ticker(self.symbol)
            self.data = stock.history(period=self.period)
            return len(self.data) > 0
        except Exception as e:
            print(f"Veri çekme hatası ({self.symbol}): {e}")
            return False

    def calculate_rsi(self):
        """RSI (Relative Strength Index) hesaplama"""
        if self.data is None or len(self.data) < config.RSI_PERIOD + 1:
            return None
        rsi = calculate_rsi(self.data['Close'], config.RSI_PERIOD)
        self.analysis['rsi'] = round(rsi.iloc[-1], 2)
        return self.analysis['rsi']

    def calculate_macd(self):
        """MACD hesaplama"""
        if self.data is None or len(self.data) < config.MACD_SLOW + config.MACD_SIGNAL:
            return None
        macd_line, signal_line, histogram = calculate_macd(
            self.data['Close'],
            config.MACD_FAST,
            config.MACD_SLOW,
            config.MACD_SIGNAL
        )
        self.analysis['macd'] = round(macd_line.iloc[-1], 4)
        self.analysis['macd_signal'] = round(signal_line.iloc[-1], 4)
        self.analysis['macd_histogram'] = round(histogram.iloc[-1], 4)
        return self.analysis['macd']

    def calculate_moving_averages(self):
        """Hareketli ortalamalar hesaplama"""
        if self.data is None:
            return None
        for period in config.MA_PERIODS:
            if len(self.data) >= period:
                self.data[f'sma_{period}'] = calculate_sma(self.data['Close'], period)
        self.analysis['current_price'] = round(self.data['Close'].iloc[-1], 2)
        self.analysis['sma_20'] = round(self.data['sma_20'].iloc[-1], 2) if 'sma_20' in self.data.columns else None
        self.analysis['sma_50'] = round(self.data['sma_50'].iloc[-1], 2) if 'sma_50' in self.data.columns else None
        self.analysis['sma_200'] = round(self.data['sma_200'].iloc[-1], 2) if 'sma_200' in self.data.columns else None
        return self.analysis

    def calculate_support_resistance(self):
        """Destek ve direnç seviyeleri hesaplama"""
        if self.data is None or len(self.data) < 20:
            return None
        recent_data = self.data.tail(20)
        self.analysis['resistance'] = round(recent_data['High'].max(), 2)
        self.analysis['support'] = round(recent_data['Low'].min(), 2)
        # Pivot noktaları
        last_close = self.data['Close'].iloc[-1]
        last_high = self.data['High'].iloc[-1]
        last_low = self.data['Low'].iloc[-1]
        self.analysis['pivot'] = round((last_high + last_low + last_close) / 3, 2)
        self.analysis['r1'] = round(2 * self.analysis['pivot'] - last_low, 2)
        self.analysis['s1'] = round(2 * self.analysis['pivot'] - last_high, 2)
        return self.analysis

    def calculate_stochastic(self):
        """Stokastik Osilatör hesaplama"""
        if self.data is None or len(self.data) < 14:
            return None
        stoch_k, stoch_d = calculate_stochastic(
            self.data['High'],
            self.data['Low'],
            self.data['Close'],
            14
        )
        self.analysis['stoch_k'] = round(stoch_k.iloc[-1], 2)
        self.analysis['stoch_d'] = round(stoch_d.iloc[-1], 2)
        return self.analysis

    def calculate_bollinger_bands(self):
        """Bollinger Bantları hesaplama"""
        if self.data is None or len(self.data) < 20:
            return None
        bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(self.data['Close'], 20, 2)
        self.analysis['bb_upper'] = round(bb_upper.iloc[-1], 2)
        self.analysis['bb_middle'] = round(bb_middle.iloc[-1], 2)
        self.analysis['bb_lower'] = round(bb_lower.iloc[-1], 2)
        return self.analysis

    def calculate_atr(self):
        """ATR (Average True Range) hesaplama"""
        if self.data is None or len(self.data) < 15:
            return None
        atr = calculate_atr(self.data['High'], self.data['Low'], self.data['Close'], 14)
        self.analysis['atr'] = round(atr.iloc[-1], 2)
        return self.analysis

    def calculate_volatility(self):
        """Volatilite hesaplama"""
        if self.data is None or len(self.data) < 20:
            return None
        returns = self.data['Close'].pct_change().dropna()
        self.analysis['volatility'] = round(returns.std() * 100, 2)
        self.analysis['avg_volume'] = round(self.data['Volume'].mean(), 0)
        self.analysis['current_volume'] = int(self.data['Volume'].iloc[-1])
        return self.analysis

    def calculate_potential(self):
        """Yükseliş potansiyeli hesaplama"""
        if self.data is None or 'resistance' not in self.analysis:
            return None
        current = self.analysis['current_price']
        resistance = self.analysis['resistance']
        self.analysis['potential_percent'] = round(((resistance - current) / current) * 100, 2)
        # Hedef fiyat hesaplama
        atr = self.analysis.get('atr', current * 0.02)
        self.analysis['target_price'] = round(current + (atr * 2), 2)
        self.analysis['stop_loss'] = round(current - (atr * 1.5), 2)
        return self.analysis['potential_percent']

    def calculate_all(self):
        """Tüm analizleri çalıştır"""
        if not self.fetch_data():
            return None
        self.calculate_rsi()
        self.calculate_macd()
        self.calculate_moving_averages()
        self.calculate_support_resistance()
        self.calculate_stochastic()
        self.calculate_bollinger_bands()
        self.calculate_atr()
        self.calculate_volatility()
        self.calculate_potential()
        self.add_price_change()
        return self.analysis

    def add_price_change(self):
        """Fiyat değişimi hesaplama"""
        if self.data is None or len(self.data) < 2:
            return
        current = self.data['Close'].iloc[-1]
        previous = self.data['Close'].iloc[-2]
        self.analysis['price_change'] = round(((current - previous) / previous) * 100, 2)
        # Haftalık değişim
        if len(self.data) >= 5:
            week_ago = self.data['Close'].iloc[-6]
            self.analysis['weekly_change'] = round(((current - week_ago) / week_ago) * 100, 2)
        # Aylık değişim
        if len(self.data) >= 20:
            month_ago = self.data['Close'].iloc[-21] if len(self.data) > 21 else self.data['Close'].iloc[0]
            self.analysis['monthly_change'] = round(((current - month_ago) / month_ago) * 100, 2)
        return self.analysis

    def get_signal(self):
        """Al/Sat/Tut sinyali üretme"""
        if not self.analysis:
            return "VERI_YOK"
        signal = 0
        reasons = []
        # RSI analizi
        rsi = self.analysis.get('rsi')
        if rsi:
            if rsi < 30:
                signal += 1
                reasons.append(f"RSI Aşırı Satım ({rsi}) - AL sinyali")
            elif rsi > 70:
                signal -= 1
                reasons.append(f"RSI Aşırı Alım ({rsi}) - SAT sinyali")
            else:
                reasons.append(f"RSI Nötr ({rsi})")
        # MACD analizi
        macd = self.analysis.get('macd')
        macd_signal = self.analysis.get('macd_signal')
        if macd and macd_signal:
            if macd > macd_signal and self.analysis.get('macd_histogram', 0) > 0:
                signal += 1
                reasons.append("MACD Pozitif - Yükseliş sinyali")
            elif macd < macd_signal and self.analysis.get('macd_histogram', 0) < 0:
                signal -= 1
                reasons.append("MACD Negatif - Düşüş sinyali")
        # Fiyat vs Hareketli ortalamalar
        price = self.analysis.get('current_price')
        sma20 = self.analysis.get('sma_20')
        if price and sma20:
            if price > sma20:
                signal += 1
                reasons.append(f"Fiyat SMA20 üzerinde")
            else:
                signal -= 1
                reasons.append(f"Fiyat SMA20 altında")
        # Sonuç
        self.analysis['signal'] = signal
        self.analysis['signal_reason'] = reasons
        if signal >= 2:
            self.analysis['recommendation'] = "GÜÇLÜ AL"
        elif signal == 1:
            self.analysis['recommendation'] = "AL"
        elif signal == 0:
            self.analysis['recommendation'] = "NÖTR"
        elif signal == -1:
            self.analysis['recommendation'] = "SAT"
        else:
            self.analysis['recommendation'] = "GÜÇLÜ SAT"
        return self.analysis['recommendation']

    def format_report(self):
        """Türkçe rapor formatı oluşturma"""
        if not self.analysis:
            return "❌ Analiz verisi bulunamadı."
        a = self.analysis
        lines = []
        lines.append(f"📊 *{self.symbol} - TEKNİK ANALİZ RAPORU*")
        lines.append("=" * 45)
        # Fiyat bilgileri
        lines.append(f"\n💰 *FİYAT BİLGİLERİ*")
        lines.append(f"  Güncel Fiyat: {a.get('current_price', 'N/A')} USD")
        if a.get('price_change'):
            emoji = "📈" if a['price_change'] > 0 else "📉"
            lines.append(f"  {emoji} Günlük Değişim: %{a['price_change']:+.2f}")
        if a.get('weekly_change'):
            lines.append(f"  Haftalık Değişim: %{a['weekly_change']:+.2f}")
        if a.get('monthly_change'):
            lines.append(f"  Aylık Değişim: %{a['monthly_change']:+.2f}")
        # Teknik göstergeler
        lines.append(f"\n📉 *TEKNİK GÖSTERGELER*")
        rsi = a.get('rsi')
        if rsi:
            status = "Aşırı Satım 🔴" if rsi < 30 else "Aşırı Alım 🔴" if rsi > 70 else "Nötr 🟡"
            lines.append(f"  RSI (14): {rsi} - {status}")
        if a.get('macd'):
            lines.append(f"  MACD: {a['macd']} | Sinyal: {a.get('macd_signal', 'N/A')}")
            hist = a.get('macd_histogram', 0)
            hist_emoji = "🟢" if hist > 0 else "🔴"
            lines.append(f"  {hist_emoji} Histogram: {hist}")
        if a.get('stoch_k'):
            lines.append(f"  Stokastik: K={a['stoch_k']}, D={a.get('stoch_d', 'N/A')}")
        # Hareketli ortalamalar
        lines.append(f"\n📊 *HAREKETLİ ORTALAMALAR*")
        lines.append(f"  SMA 20: {a.get('sma_20', 'N/A')}")
        lines.append(f"  SMA 50: {a.get('sma_50', 'N/A')}")
        lines.append(f"  SMA 200: {a.get('sma_200', 'N/A')}")
        # Destek/Direnç
        lines.append(f"\n🎯 *DESTEK VE DİRENÇ*")
        lines.append(f"  Direnç: {a.get('resistance', 'N/A')}")
        lines.append(f"  Destek: {a.get('support', 'N/A')}")
        lines.append(f"  Pivot: {a.get('pivot', 'N/A')}")
        lines.append(f"  R1: {a.get('r1', 'N/A')} | S1: {a.get('s1', 'N/A')}")
        # Bollinger Bantları
        if a.get('bb_upper'):
            lines.append(f"\n📐 *BOLLINGER BANTLARI*")
            lines.append(f"  Üst Bant: {a['bb_upper']}")
            lines.append(f"  Orta Bant: {a['bb_middle']}")
            lines.append(f"  Alt Bant: {a['bb_lower']}")
        # İşlem sinyali
        lines.append(f"\n{'=' * 45}")
        lines.append(f"💡 *ÖNERİ:* {a.get('recommendation', 'BEKLE')}")
        # Potansiyel
        if a.get('potential_percent'):
            lines.append(f"\n🎯 *HEDEF VE RİSK*")
            lines.append(f"  Yükseliş Potansiyeli: %{a['potential_percent']:+.2f}")
            lines.append(f"  Hedef Fiyat: {a.get('target_price', 'N/A')}")
            lines.append(f"  Stop Loss: {a.get('stop_loss', 'N/A')}")
        lines.append(f"\n  ATR: {a.get('atr', 'N/A')}")
        lines.append(f"  Volatilite: %{a.get('volatility', 'N/A')}")
        # Sinyal gerekçeleri
        if a.get('signal_reason'):
            lines.append(f"\n📝 *SİNYAL GEREKÇELERİ:*")
            for reason in a['signal_reason']:
                lines.append(f"  • {reason}")
        lines.append(f"\n⏰ Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        return "\n".join(lines)
