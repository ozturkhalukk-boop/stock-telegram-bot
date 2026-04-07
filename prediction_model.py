# -*- coding: utf-8 -*-
"""
🎯 SPOT İŞLEMLER İÇİN - Hisse Tahmin ve Öneri Sistemi
Sadece AL ve NÖTR sinyalleri - Short yok!

Gerçekçi potansiyel değerleri: %3 - %15 arası
"""
import pandas as pd
import numpy as np
import yfinance as yf
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import sqlite3


class PredictionModel:
    """
    SPOT işlemler için tahmin modeli
    Sadece AL ve NÖTR sinyalleri verir
    """

    def __init__(self, db_path: str = "predictions.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Veritabanını başlat"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prediction_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    prediction_date DATE,
                    predicted_price REAL,
                    actual_price REAL,
                    direction TEXT,
                    confidence REAL,
                    potential_percent REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
        except:
            pass

    def predict_direction(self, indicators: Dict, fundamentals: Dict = None,
                         sentiment: float = 0) -> Tuple[str, float, float]:
        """
        SPOT İŞLEM - Yön tahmini
        Sadece AL ve NÖTR döner - SAT yok!
        Returns: (direction, confidence, potential_percent)
        """
        buy_signals = 0
        total_signals = 0

        # RSI analizi - en önemli gösterge
        if 'rsi' in indicators:
            total_signals += 2
            rsi = indicators['rsi']
            if rsi < 35:
                buy_signals += 3
            elif rsi < 45:
                buy_signals += 2
            elif rsi < 55:
                buy_signals += 1
            elif rsi < 65:
                buy_signals += 0.5
            else:
                buy_signals -= 1

        # MACD analizi
        if 'macd_histogram' in indicators:
            total_signals += 1
            if indicators['macd_histogram'] > 0:
                buy_signals += 1.5
            else:
                buy_signals -= 0.5

        # ADX analizi
        if 'adx' in indicators:
            total_signals += 1
            adx = indicators['adx']
            if 20 < adx < 40:
                buy_signals += 1
            elif adx >= 40:
                buy_signals += 1.5

        # Fiyat vs SMA20
        if 'sma_20' in indicators and 'current_price' in indicators:
            total_signals += 1
            sma_20 = indicators['sma_20']
            if sma_20 and indicators['current_price'] > sma_20:
                buy_signals += 1
            else:
                buy_signals -= 0.5

        # Fiyat vs SMA50
        if 'sma_50' in indicators and 'current_price' in indicators:
            total_signals += 1
            sma_50 = indicators['sma_50']
            if sma_50 and indicators['current_price'] > sma_50:
                buy_signals += 1.5
            else:
                buy_signals -= 0.5

        # Bollinger Bantları
        if 'bb_position' in indicators:
            total_signals += 0.5
            bb_pos = indicators['bb_position']
            if bb_pos < 0.3:
                buy_signals += 1
            elif bb_pos > 0.7:
                buy_signals -= 0.5

        # Haber duyarlılığı
        if sentiment != 0:
            total_signals += 1
            if sentiment > 0.3:
                buy_signals += 1
            elif sentiment < -0.3:
                buy_signals -= 1

        # Sonuç hesaplama
        if total_signals == 0:
            return "NÖTR", 0.5, 2.0

        score = buy_signals / total_signals

        # Güven skoru
        confidence = min(0.95, max(0.4, 0.5 + (score * 0.3)))

        # SPOT için potansiyel - gerçekçi değerler
        current_price = indicators.get('current_price', 100)
        atr = indicators.get('atr', current_price * 0.02)
        support = indicators.get('support', current_price * 0.98)
        resistance = indicators.get('resistance', current_price * 1.05)

        # Potansiyel hesaplama
        if score >= 1.5:
            potential_to_resistance = ((resistance - current_price) / current_price) * 100
            potential = min(15, max(5, potential_to_resistance))
            direction = "AL"
        elif score >= 0.8:
            potential = min(12, max(3, 3 + (score * 5)))
            direction = "AL"
        elif score >= 0.3:
            potential = min(8, max(2, 2 + (score * 5)))
            direction = "NÖTR"
        else:
            potential = min(5, max(1, 2 + (score * 3)))
            direction = "NÖTR"

        return direction, round(confidence, 2), round(potential, 2)

    def calculate_stop_loss(self, current_price: float, atr: float,
                          support: float, direction: str) -> float:
        """Stop-loss hesapla - SPOT işlemler için"""
        if support and support > 0:
            stop = support * 0.98
        else:
            stop = current_price - (atr * 1.5)
        return round(stop, 2)

    def calculate_target(self, current_price: float, atr: float,
                       resistance: float, potential_percent: float) -> float:
        """Hedef fiyat hesapla"""
        target = current_price * (1 + potential_percent / 100)
        if resistance and resistance > current_price:
            target = min(target, resistance * 0.98)
        return round(target, 2)

    def generate_trade_signal(self, symbol: str, indicators: Dict,
                            fundamentals: Dict = None,
                            sentiment: float = 0) -> Dict:
        """SPOT işlem sinyali üret"""
        direction, confidence, potential_percent = self.predict_direction(
            indicators, fundamentals, sentiment
        )

        current_price = indicators.get('current_price', 0)
        atr = indicators.get('atr', current_price * 0.02)
        support = indicators.get('support', 0)
        resistance = indicators.get('resistance', 0)

        stop_loss = self.calculate_stop_loss(current_price, atr, support, direction)
        target_price = self.calculate_target(current_price, atr, resistance, potential_percent)

        # Risk/Ödül
        risk = current_price - stop_loss
        reward = target_price - current_price
        risk_reward = round(reward / risk, 2) if risk > 0 else 0

        return {
            'symbol': symbol,
            'direction': direction,
            'confidence': confidence,
            'entry_price': current_price,
            'current_price': current_price,
            'target_price': target_price,
            'target_percent': potential_percent,
            'stop_loss': stop_loss,
            'risk_reward': risk_reward,
            'atr': atr,
            'support': support,
            'resistance': resistance,
            'news_sentiment': sentiment,
            'timestamp': datetime.now().isoformat()
        }

    def format_trade_signal(self, signal: Dict) -> str:
        """SPOT sinyal formatla"""
        direction = signal['direction']

        if direction == "AL":
            emoji = "📈"
            direction_text = "AL"
        else:
            emoji = "⚖️"
            direction_text = "NÖTR"

        lines = []
        lines.append(f"\n{emoji} *SPOT İŞLEM SİNYALİ*")
        lines.append("=" * 45)
        lines.append(f"📊 Sembol: {signal['symbol']}")
        lines.append(f"📈 Yön: *{direction_text}*")
        lines.append(f"🎯 GÜVEN: %{signal['confidence'] * 100:.0f}")
        lines.append("")
        lines.append(f"💰 *FİYAT BİLGİSİ*")
        lines.append(f"  Giriş: {signal['entry_price']:.2f}")
        lines.append(f"  Hedef: {signal['target_price']:.2f} (%+{signal['target_percent']:.1f})")
        lines.append(f"  Stop-Loss: {signal['stop_loss']:.2f}")
        lines.append("")
        lines.append(f"⚖️ Risk/Ödül: *{signal['risk_reward']:.2f}*")
        lines.append("")
        lines.append(f"📊 *SEVİYELER*")
        lines.append(f"  Destek: {signal['support']:.2f}")
        lines.append(f"  Direnç: {signal['resistance']:.2f}")
        lines.append("=" * 45)

        if signal['risk_reward'] >= 2:
            lines.append(f"✅ Risk/Ödül İYİ")
        elif signal['risk_reward'] >= 1.5:
            lines.append(f"⚠️ Risk/Ödül ORTA")
        else:
            lines.append(f"⚠️ Risk/Ödül DÜŞÜK")

        if direction == "NÖTR":
            lines.append(f"ℹ️ NÖTR sinyallerde pozisyon almayı düşünün")

        return "\n".join(lines)
