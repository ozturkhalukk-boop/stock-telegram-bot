# -*- coding: utf-8 -*-
"""
📊 İleri Teknik Göstergeler Modülü
Fibonacci, Ichimoku, ADX, VWAP ve diğer gelişmiş göstergeler
"""
import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Optional, Tuple


class AdvancedIndicators:
    """
    İleri teknik analiz göstergeleri
    """

    def __init__(self):
        pass

    def calculate_fibonacci_levels(self, data: pd.DataFrame) -> Dict:
        """Fibonacci retracement seviyelerini hesapla"""
        if len(data) < 50:
            return {}

        high = data['High'].tail(100).max()
        low = data['Low'].tail(100).min()
        diff = high - low

        # Fibonacci seviyeleri
        levels = {
            'fib_0': low,
            'fib_236': low + diff * 0.236,
            'fib_382': low + diff * 0.382,
            'fib_500': low + diff * 0.500,
            'fib_618': low + diff * 0.618,
            'fib_786': low + diff * 0.786,
            'fib_100': high,
            'fib_1618': high + diff * 0.618,
        }

        current_price = data['Close'].iloc[-1]

        # Mevcut fiyatın hangi seviyede olduğunu bul
        nearest_level = None
        for level_name in ['fib_1618', 'fib_100', 'fib_786', 'fib_618', 'fib_500', 'fib_382', 'fib_236', 'fib_0']:
            if abs(current_price - levels[level_name]) < diff * 0.05:
                nearest_level = level_name
                break

        return {
            'fib_high': high,
            'fib_low': low,
            'fib_range': diff,
            'levels': {k: round(v, 2) for k, v in levels.items()},
            'current_price': round(current_price, 2),
            'nearest_level': nearest_level,
            'support_fib': levels.get('fib_618', low),
            'resistance_fib': levels.get('fib_786', high)
        }

    def calculate_ichimoku(self, data: pd.DataFrame) -> Dict:
        """Ichimoku Bulutu hesapla"""
        if len(data) < 52:
            return {}

        # Tenkan-sen (Dönüşüm Hattı) - 9 periyot
        nine_high = data['High'].rolling(window=9).max()
        nine_low = data['Low'].rolling(window=9).min()
        tenkan_sen = (nine_high + nine_low) / 2

        # Kijun-sen (Standart Hattı) - 26 periyot
        twenty_six_high = data['High'].rolling(window=26).max()
        twenty_six_low = data['Low'].rolling(window=26).min()
        kijun_sen = (twenty_six_high + twenty_six_low) / 2

        # Senkou Span A (Önceki Bollinger) - (Tenkan + Kijun) / 2
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)

        # Senkou Span B (Arka Bollinger) - 52 periyot
        fifty_two_high = data['High'].rolling(window=52).max()
        fifty_two_low = data['Low'].rolling(window=52).min()
        senkou_span_b = ((fifty_two_high + fifty_two_low) / 2).shift(26)

        # Chikou Span (Gecikmeli Kapanış) - 26 periyot geri
        chikou_span = data['Close'].shift(-26)

        current_price = data['Close'].iloc[-1]
        tenkan = tenkan_sen.iloc[-1]
        kijun = kijun_sen.iloc[-1]
        span_a = senkou_span_a.iloc[-1] if not pd.isna(senkou_span_a.iloc[-1]) else 0
        span_b = senkou_span_b.iloc[-1] if not pd.isna(senkou_span_b.iloc[-1]) else 0

        # Bulut (Kumo)
        cloud_top = max(span_a, span_b)
        cloud_bottom = min(span_a, span_b)

        # Sinyal
        signal = "NÖTR"
        if current_price > cloud_top and tenkan > kijun:
            signal = "GÜÇLÜ AL"
        elif current_price > cloud_top:
            signal = "AL"
        elif current_price < cloud_bottom and tenkan < kijun:
            signal = "GÜÇLÜ SAT"
        elif current_price < cloud_bottom:
            signal = "SAT"
        elif tenkan > kijun:
            signal = "AL"
        else:
            signal = "SAT"

        return {
            'tenkan_sen': round(tenkan, 2),
            'kijun_sen': round(kijun, 2),
            'senkou_span_a': round(span_a, 2),
            'senkou_span_b': round(span_b, 2),
            'chikou_span': round(chikou_span.iloc[-1], 2) if not pd.isna(chikou_span.iloc[-1]) else 0,
            'cloud_top': round(cloud_top, 2),
            'cloud_bottom': round(cloud_bottom, 2),
            'signal': signal,
            'current_price': round(current_price, 2)
        }

    def calculate_adx(self, data: pd.DataFrame, period: int = 14) -> Dict:
        """Average Directional Index (ADX) hesapla"""
        if len(data) < period + 1:
            return {}

        # True Range
        high = data['High']
        low = data['Low']
        close = data['Close']

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Directional Movement
        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        # Smoothed averages
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

        # DX
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)

        # ADX
        adx = dx.rolling(window=period).mean()

        current_adx = adx.iloc[-1]
        current_plus_di = plus_di.iloc[-1]
        current_minus_di = minus_di.iloc[-1]

        # Trend strength
        if current_adx > 25:
            strength = "GÜÇLÜ TREND"
        elif current_adx > 20:
            strength = "ORTA TREND"
        else:
            strength = "ZAYIF TREND"

        # Trend direction
        if current_plus_di > current_minus_di:
            direction = "YÜKSELIŞ"
        else:
            direction = "DÜŞÜŞ"

        return {
            'adx': round(current_adx, 2),
            'plus_di': round(current_plus_di, 2),
            'minus_di': round(current_minus_di, 2),
            'trend_strength': strength,
            'trend_direction': direction,
            'atr': round(atr.iloc[-1], 2)
        }

    def calculate_vwap(self, data: pd.DataFrame) -> float:
        """Volume Weighted Average Price (VWAP) hesapla"""
        typical_price = (data['High'] + data['Low'] + data['Close']) / 3
        vwap = (typical_price * data['Volume']).cumsum() / data['Volume'].cumsum()
        return round(vwap.iloc[-1], 2)

    def calculate_obv(self, data: pd.DataFrame) -> Dict:
        """On-Balance Volume (OBV) hesapla"""
        obv = (np.sign(data['Close'].diff()) * data['Volume']).fillna(0).cumsum()
        current_obv = obv.iloc[-1]
        obv_trend = "YÜKSELIŞ" if obv.iloc[-1] > obv.iloc[-5] else "DÜŞÜŞ"
        return {
            'obv': round(current_obv, 0),
            'obv_trend': obv_trend,
            'obv_change': round(((obv.iloc[-1] - obv.iloc[-10]) / abs(obv.iloc[-10])) * 100, 2) if abs(obv.iloc[-10]) > 0 else 0
        }

    def calculate_momentum(self, data: pd.DataFrame, period: int = 10) -> Dict:
        """Momentum göstergesi"""
        momentum = data['Close'] - data['Close'].shift(period)
        roc = ((data['Close'] - data['Close'].shift(period)) / data['Close'].shift(period)) * 100

        return {
            'momentum': round(momentum.iloc[-1], 2),
            'roc': round(roc.iloc[-1], 2),  # Rate of Change
            'momentum_trend': "YÜKSELIŞ" if momentum.iloc[-1] > 0 else "DÜŞÜŞ"
        }

    def calculate_cci(self, data: pd.DataFrame, period: int = 20) -> Dict:
        """Commodity Channel Index (CCI) hesapla"""
        typical_price = (data['High'] + data['Low'] + data['Close']) / 3
        sma = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
        cci = (typical_price - sma) / (0.015 * mad)

        current_cci = cci.iloc[-1]
        if current_cci > 100:
            status = "AŞIRI ALIM"
        elif current_cci < -100:
            status = "AŞIRI SATIM"
        else:
            status = "NORMAL"

        return {
            'cci': round(current_cci, 2),
            'status': status
        }

    def calculate_williams_r(self, data: pd.DataFrame, period: int = 14) -> Dict:
        """Williams %R hesapla"""
        highest_high = data['High'].rolling(window=period).max()
        lowest_low = data['Low'].rolling(window=period).min()
        williams_r = -100 * (highest_high - data['Close']) / (highest_high - lowest_low)

        current_wr = williams_r.iloc[-1]
        if current_wr > -20:
            status = "AŞIRI ALIM"
        elif current_wr < -80:
            status = "AŞIRI SATIM"
        else:
            status = "NORMAL"

        return {
            'williams_r': round(current_wr, 2),
            'status': status
        }

    def calculate_volume_profile(self, data: pd.DataFrame, bins: int = 20) -> Dict:
        """Volume Profile hesapla"""
        price_range = data['High'].max() - data['Low'].min()
        bin_size = price_range / bins

        volume_bins = pd.cut(data['Close'], bins=bins)
        volume_profile = data.groupby(volume_bins)['Volume'].sum()

        # POC (Point of Control) - En yüksek hacimli fiyat
        poc_price = volume_profile.idxmax()
        poc_volume = volume_profile.max()

        # VH (Value Area High) - %70 hacim alanı üst sınır
        sorted_profile = volume_profile.sort_values(ascending=False)
        cumulative = 0
        vh = None
        vl = None
        total_volume = volume_profile.sum()

        for price_level in sorted_profile.index:
            cumulative += volume_profile[price_level]
            if vh is None and cumulative > total_volume * 0.85:
                vh = price_level.right
            if cumulative > total_volume * 0.15:
                vl = price_level.left

        return {
            'poc_price': round(poc_price.mid if hasattr(poc_price, 'mid') else poc_price, 2),
            'poc_volume': int(poc_volume),
            'vh': round(vh, 2) if vh else None,
            'vl': round(vl, 2) if vl else None,
            'profile': {str(k): int(v) for k, v in volume_profile.items()}
        }

    def calculate_all_advanced(self, data: pd.DataFrame) -> Dict:
        """Tüm ileri göstergeleri hesapla"""
        result = {}

        # Fibonacci
        fib = self.calculate_fibonacci_levels(data)
        if fib:
            result['fibonacci'] = fib

        # Ichimoku
        ichi = self.calculate_ichimoku(data)
        if ichi and ichi.get('tenkan_sen'):
            result['ichimoku'] = ichi

        # ADX
        adx = self.calculate_adx(data)
        if adx and adx.get('adx'):
            result['adx'] = adx

        # VWAP
        vwap = self.calculate_vwap(data)
        result['vwap'] = vwap

        # OBV
        obv = self.calculate_obv(data)
        if obv:
            result['obv'] = obv

        # Momentum
        mom = self.calculate_momentum(data)
        if mom:
            result['momentum'] = mom

        # CCI
        cci = self.calculate_cci(data)
        if cci:
            result['cci'] = cci

        # Williams %R
        wr = self.calculate_williams_r(data)
        if wr:
            result['williams_r'] = wr

        return result

    def format_advanced_report(self, data: pd.DataFrame) -> str:
        """İleri göstergeler raporu formatla"""
        advanced = self.calculate_all_advanced(data)
        if not advanced:
            return "❌ Yeterli veri yok."

        lines = []
        lines.append("\n📊 *İLERİ GÖSTERGELER*")
        lines.append("-" * 45)

        # Fibonacci
        if 'fibonacci' in advanced:
            fib = advanced['fibonacci']
            lines.append(f"\n🔮 *FİBONACCİ SEVİYELERİ*")
            lines.append(f"  0% (Destek): {fib['levels'].get('fib_0', 'N/A')}")
            lines.append(f"  23.6%: {fib['levels'].get('fib_236', 'N/A')}")
            lines.append(f"  38.2%: {fib['levels'].get('fib_382', 'N/A')}")
            lines.append(f"  50.0%: {fib['levels'].get('fib_500', 'N/A')}")
            lines.append(f"  61.8%: {fib['levels'].get('fib_618', 'N/A')}")
            lines.append(f"  78.6%: {fib['levels'].get('fib_786', 'N/A')}")
            lines.append(f"  100% (Direnç): {fib['levels'].get('fib_100', 'N/A')}")

        # Ichimoku
        if 'ichimoku' in advanced:
            ichi = advanced['ichimoku']
            lines.append(f"\n☁️ *ICHIMOKU BULUTU*")
            lines.append(f"  Tenkan-sen: {ichi.get('tenkan_sen', 'N/A')}")
            lines.append(f"  Kijun-sen: {ichi.get('kijun_sen', 'N/A')}")
            lines.append(f"  Bulut Ust: {ichi.get('cloud_top', 'N/A')}")
            lines.append(f"  Bulut Alt: {ichi.get('cloud_bottom', 'N/A')}")
            lines.append(f"  Sinyal: {ichi.get('signal', 'N/A')}")

        # ADX
        if 'adx' in advanced:
            adx = advanced['adx']
            lines.append(f"\n📈 *ADX TREND GÜCÜ*")
            lines.append(f"  ADX: {adx.get('adx', 'N/A')}")
            lines.append(f"  +DI: {adx.get('plus_di', 'N/A')}")
            lines.append(f"  -DI: {adx.get('minus_di', 'N/A')}")
            lines.append(f"  Trend: {adx.get('trend_strength', 'N/A')}")
            lines.append(f"  Yön: {adx.get('trend_direction', 'N/A')}")

        # VWAP
        if 'vwap' in advanced:
            lines.append(f"\n📉 *VWAP*")
            lines.append(f"  VWAP: {advanced['vwap']}")

        # OBV
        if 'obv' in advanced:
            obv = advanced['obv']
            lines.append(f"\n📊 *OBV (Hacim)*")
            lines.append(f"  OBV: {int(obv.get('obv', 0)):,}")
            lines.append(f"  Trend: {obv.get('obv_trend', 'N/A')}")
            lines.append(f"  Değişim: %{obv.get('obv_change', 0):+.2f}")

        # Momentum
        if 'momentum' in advanced:
            mom = advanced['momentum']
            lines.append(f"\n🚀 *MOMENTUM*")
            lines.append(f"  Momentum: {mom.get('momentum', 'N/A')}")
            lines.append(f"  ROC: %{mom.get('roc', 'N/A'):+.2f}")

        # CCI
        if 'cci' in advanced:
            cci = advanced['cci']
            lines.append(f"\n📉 *CCI*")
            lines.append(f"  CCI: {cci.get('cci', 'N/A')}")
            lines.append(f"  Durum: {cci.get('status', 'N/A')}")

        # Williams %R
        if 'williams_r' in advanced:
            wr = advanced['williams_r']
            lines.append(f"\n📉 *WILLIAMS %R*")
            lines.append(f"  %R: {wr.get('williams_r', 'N/A')}")
            lines.append(f"  Durum: {wr.get('status', 'N/A')}")

        return "\n".join(lines)
