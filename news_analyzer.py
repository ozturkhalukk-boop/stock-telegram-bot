# -*- coding: utf-8 -*-
"""
📰 Hisse Haberleri ve Duygu Analizi Modülü
Hisse haberlerini çeker, duygu analizi yapar ve yatırım sinyalleri üretir
"""
import requests
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import re
import sqlite3
import os


class NewsAnalyzer:
    """
    Hisse haberleri analiz sistemi
    """

    def __init__(self, db_path: str = "news_data.db"):
        self.db_path = db_path
        self.init_database()
        # Türkçe duygu sözlükleri
        self.positive_words = self.load_positive_words()
        self.negative_words = self.load_negative_words()

    def init_database(self):
        """Veritabanını başlat"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                title TEXT,
                summary TEXT,
                source TEXT,
                url TEXT,
                published_date DATETIME,
                sentiment_score REAL,
                sentiment_label TEXT,
                cached_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sentiment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                avg_sentiment REAL,
                news_count INTEGER,
                overall_signal TEXT,
                analysis_date DATE DEFAULT CURRENT_DATE
            )
        """)

        conn.commit()
        conn.close()

    def load_positive_words(self) -> List[str]:
        """Pozitif kelimeler listesi"""
        return [
            'yükseliş', 'kazanç', 'kar', 'büyüme', ' başarı', ' başarılı',
            'pozitif', 'güçlü', 'artış', 'yüksel', 'kar artış', 'satış artış',
            'büyü', 'geliş', 'iyi', 'mükemmel', 'harika', 'muhteşem',
            ' rekor', ' zirve', ' yüksek', ' umut', ' umut verici',
            ' bullish', 'buy', 'gain', 'profit', 'growth', 'surge',
            'soar', 'rally', 'up', 'rise', 'strong', 'positive',
            'breakthrough', 'innovation', 'expansion', 'recovery',
            'upgrade', 'outperform', 'beat', 'exceed', 'optimistic'
        ]

    def load_negative_words(self) -> List[str]:
        """Negatif kelimeler listesi"""
        return [
            'düşüş', 'kayıp', 'zarar', 'kriz', 'başarısızlık', 'başarısız',
            'negatif', 'zayıf', 'düş', 'azal', 'satış', 'düşüş',
            'küçül', 'kötü', 'berbat', 'felaket', ' felaket',
            'rekor düşük', 'dip', 'düşük', 'korku', ' tedirgin',
            ' bearish', 'sell', 'loss', 'decline', 'fall', 'drop',
            'crash', 'plunge', 'down', 'weak', 'negative', 'warning',
            'downgrade', 'underperform', 'miss', 'concern', 'risk',
            'lawsuit', 'investigation', 'scandal', 'fraud'
        ]

    def get_stock_news(self, symbol: str, limit: int = 10) -> List[Dict]:
        """Yahoo Finance'den hisse haberlerini al"""
        try:
            stock = yf.Ticker(symbol)
            news = stock.news
            if not news:
                return []
            result = []
            for item in news[:limit]:
                result.append({
                    'title': item.get('title', ''),
                    'publisher': item.get('publisher', 'Bilinmeyen'),
                    'link': item.get('link', ''),
                    'published': item.get('pubDate', ''),
                    'summary': item.get('summary', '')
                })
            return result
        except Exception as e:
            print(f"Haber çekme hatası ({symbol}): {e}")
            return []

    def analyze_sentiment(self, text: str) -> Tuple[float, str]:
        """
        Metnin duygu puanını hesapla
        Returns: (score: -1.0 to 1.0, label: Pozitif/Nötr/Negatif)
        """
        if not text:
            return 0.0, "Nötr"
        text = text.lower()
        positive_count = 0
        negative_count = 0
        # Pozitif kelime sayısı
        for word in self.positive_words:
            if word.lower() in text:
                positive_count += 1
        # Negatif kelime sayısı
        for word in self.negative_words:
            if word.lower() in text:
                negative_count += 1
        # Toplam kelime sayısı
        words = len(text.split())
        if words == 0:
            return 0.0, "Nötr"
        # Duygu skoru hesapla
        total = positive_count + negative_count
        if total == 0:
            return 0.0, "Nötr"
        score = (positive_count - negative_count) / (positive_count + negative_count)
        # Normalize to -1 to 1 range
        score = max(-1.0, min(1.0, score))
        # Etiket belirle
        if score > 0.2:
            label = "Pozitif 🟢"
        elif score < -0.2:
            label = "Negatif 🔴"
        else:
            label = "Nötr 🟡"
        return score, label

    def analyze_news_for_stock(self, symbol: str) -> Dict:
        """Hisse için tüm haberleri analiz et"""
        news = self.get_stock_news(symbol, limit=10)
        if not news:
            return {
                'symbol': symbol,
                'news_count': 0,
                'avg_sentiment': 0,
                'sentiment_label': "Nötr",
                'signal': "NÖTR",
                'headlines': []
            }
        analyzed_news = []
        total_sentiment = 0.0
        for item in news:
            sentiment, label = self.analyze_sentiment(item.get('title', '') + ' ' + item.get('summary', ''))
            item['sentiment'] = sentiment
            item['sentiment_label'] = label
            analyzed_news.append(item)
            total_sentiment += sentiment
        avg_sentiment = total_sentiment / len(news) if news else 0
        # Genel sinyal oluştur
        if avg_sentiment > 0.3:
            signal = "GÜÇLÜ POZİTİF"
        elif avg_sentiment > 0.1:
            signal = "POZİTİF"
        elif avg_sentiment < -0.3:
            signal = "GÜÇLÜ NEGATİF"
        elif avg_sentiment < -0.1:
            signal = "NEGATİF"
        else:
            signal = "NÖTR"
        # Sonucu önbelleğe al
        self.cache_news(symbol, analyzed_news, avg_sentiment, signal)
        return {
            'symbol': symbol,
            'news_count': len(news),
            'avg_sentiment': round(avg_sentiment, 3),
            'sentiment_label': "Pozitif 🟢" if avg_sentiment > 0.1 else "Negatif 🔴" if avg_sentiment < -0.1 else "Nötr 🟡",
            'signal': signal,
            'headlines': [
                {
                    'title': n['title'][:100] + '...' if len(n['title']) > 100 else n['title'],
                    'sentiment': n['sentiment'],
                    'sentiment_label': n['sentiment_label'],
                    'publisher': n.get('publisher', 'Bilinmeyen')
                }
                for n in analyzed_news[:5]
            ]
        }

    def cache_news(self, symbol: str, news: List[Dict], sentiment: float, signal: str):
        """Haberleri önbelleğe kaydet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for item in news:
            cursor.execute("""
                INSERT OR REPLACE INTO news_cache
                (symbol, title, summary, source, url, published_date, sentiment_score, sentiment_label)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol,
                item.get('title', ''),
                item.get('summary', ''),
                item.get('publisher', ''),
                item.get('link', ''),
                item.get('published', ''),
                item.get('sentiment', 0),
                item.get('sentiment_label', 'Nötr')
            ))
        conn.commit()
        conn.close()

    def get_news_summary(self, symbol: str) -> str:
        """Haber özetini formatla"""
        analysis = self.analyze_news_for_stock(symbol)
        if analysis['news_count'] == 0:
            return f"📰 *{symbol}*\n\nHaber bulunamadı."
        lines = []
        lines.append(f"📰 *{symbol} - HABER ANALİZİ*")
        lines.append(f"📊 Haber Sayısı: {analysis['news_count']}")
        lines.append(f"💭 Duygu Skoru: {analysis['avg_sentiment']:+.2f} ({analysis['sentiment_label']})")
        lines.append(f"📈 Sinyal: *{analysis['signal']}*")
        lines.append(f"\n📋 *Son Haberler:*")
        for i, news in enumerate(analysis['headlines'][:3], 1):
            lines.append(f"\n{i}. {news['sentiment_label']} {news['title']}")
            lines.append(f"   Kaynak: {news['publisher']}")
        return "\n".join(lines)

    def get_market_news_summary(self, symbols: List[str]) -> Dict[str, Dict]:
        """Birden fazla hisse için haber özeti"""
        results = {}
        for symbol in symbols:
            results[symbol] = self.analyze_news_for_stock(symbol)
        return results

    def detect_news_impact(self, symbol: str, price_change: float) -> str:
        """Haberlerin fiyat değişimi üzerindeki etkisini değerlendir"""
        analysis = self.analyze_news_for_stock(symbol)
        sentiment = analysis['avg_sentiment']
        # Etki değerlendirmesi
        if sentiment > 0.3 and price_change > 2:
            return "📰📈 Haber-pozitif fiyat uyumu - Güçlü yükseliş sinyali"
        elif sentiment < -0.3 and price_change < -2:
            return "📰📉 Haber-negatif fiyat uyumu - Güçlü düşüş sinyali"
        elif sentiment > 0.3 and price_change < -2:
            return "📰📉 Haber-pozitif ama fiyat düşüyor - Dikkatli ol"
        elif sentiment < -0.3 and price_change > 2:
            return "📰📈 Haber-negatif ama fiyat yükseliyor - Fırsat mı?"
        else:
            return "📰➡️ Haber-fiyat dengeli"


class FundamentalAnalyzer:
    """
    Temel analiz sınıfı
    """

    def __init__(self):
        pass

    def get_fundamentals(self, symbol: str) -> Dict:
        """Temel verileri al"""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            return {
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'peg_ratio': info.get('pegRatio', 0),
                'price_to_book': info.get('priceToBook', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'current_ratio': info.get('currentRatio', 0),
                'quick_ratio': info.get('quickRatio', 0),
                'roe': info.get('returnOnEquity', 0),
                'roa': info.get('returnOnAssets', 0),
                'profit_margin': info.get('profitMargin', 0),
                'operating_margin': info.get('operatingMargin', 0),
                'revenue_growth': info.get('revenueGrowth', 0),
                'earnings_growth': info.get('earningsGrowth', 0),
                'book_value': info.get('bookValue', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                '52w_high': info.get('fiftyTwoWeekHigh', 0),
                '52w_low': info.get('fiftyTwoWeekLow', 0),
                'avg_volume': info.get('averageVolume', 0),
                'target_price': info.get('targetMeanPrice', 0),
                'recommendation': info.get('recommendationKey', 'N/A'),
                'analyst_count': info.get('numberOfAnalystOpinions', 0)
            }
        except Exception as e:
            print(f"Temel veri hatası ({symbol}): {e}")
            return {}

    def analyze_fundamentals(self, symbol: str) -> Dict:
        """Temel analiz yap"""
        fundamentals = self.get_fundamentals(symbol)
        if not fundamentals:
            return {'error': 'Veri alınamadı'}
        scores = {}
        # F/K oranı değerlendirmesi
        pe = fundamentals.get('pe_ratio', 0)
        if pe > 0:
            if pe < 15:
                scores['pe'] = 2  # İyi
            elif pe < 25:
                scores['pe'] = 1  # Normal
            else:
                scores['pe'] = -1  # Yüksek
        else:
            scores['pe'] = 0
        # PD/DD oranı değerlendirmesi
        pb = fundamentals.get('price_to_book', 0)
        if pb > 0:
            if pb < 1.5:
                scores['pb'] = 2
            elif pb < 3:
                scores['pb'] = 1
            else:
                scores['pb'] = -1
        else:
            scores['pb'] = 0
        # Büyüme değerlendirmesi
        revenue_growth = fundamentals.get('revenue_growth', 0) or 0
        if revenue_growth > 0.2:
            scores['growth'] = 2
        elif revenue_growth > 0:
            scores['growth'] = 1
        else:
            scores['growth'] = -1
        # Karlılık
        roe = fundamentals.get('roe', 0) or 0
        if roe > 0.2:
            scores['roe'] = 2
        elif roe > 0.1:
            scores['roe'] = 1
        else:
            scores['roe'] = -1
        # Borçluluk
        de = fundamentals.get('debt_to_equity', 0) or 0
        if de < 50:
            scores['debt'] = 2
        elif de < 100:
            scores['debt'] = 1
        else:
            scores['debt'] = -1
        # Toplam skor
        total_score = sum(scores.values())
        # Değerlendirme
        if total_score >= 6:
            recommendation = "ÇOK GÜÇLÜ TEMELLER"
        elif total_score >= 3:
            recommendation = "GÜÇLÜ TEMELLER"
        elif total_score >= 0:
            recommendation = "NORMAL TEMELLER"
        else:
            recommendation = "ZAYIF TEMELLER"
        return {
            'symbol': symbol,
            'fundamentals': fundamentals,
            'scores': scores,
            'total_score': total_score,
            'recommendation': recommendation
        }

    def format_fundamental_report(self, symbol: str) -> str:
        """Temel analiz raporu formatla"""
        analysis = self.analyze_fundamentals(symbol)
        if 'error' in analysis:
            return f"❌ {symbol} için temel veri alınamadı."
        f = analysis['fundamentals']
        lines = []
        lines.append(f"🏢 *{symbol} - TEMEL ANALİZ*")
        lines.append("=" * 45)
        # Değerleme
        lines.append(f"\n📊 *DEĞERLEME*")
        lines.append(f"  Piyasa Değeri: {self.format_large_number(f.get('market_cap', 0))}")
        lines.append(f"  F/K Oranı: {f.get('pe_ratio', 'N/A'):.2f}" if f.get('pe_ratio') else "  F/K: N/A")
        lines.append(f"  PD/DD: {f.get('price_to_book', 'N/A'):.2f}" if f.get('price_to_book') else "  PD/DD: N/A")
        lines.append(f"  PEG: {f.get('peg_ratio', 'N/A'):.2f}" if f.get('peg_ratio') else "  PEG: N/A")
        # Karlılık
        lines.append(f"\n💰 *KARLILIK*")
        lines.append(f"  Net Kar Marjı: %{f.get('profit_margin', 0) * 100:.1f}" if f.get('profit_margin') else "  Net Kar: N/A")
        lines.append(f"  ROE: %{f.get('roe', 0) * 100:.1f}" if f.get('roe') else "  ROE: N/A")
        lines.append(f"  Faaliyet Marjı: %{f.get('operating_margin', 0) * 100:.1f}" if f.get('operating_margin') else "  Marj: N/A")
        # Büyüme
        lines.append(f"\n📈 *BÜYÜME*")
        lines.append(f"  Gelir Büyümesi: %{f.get('revenue_growth', 0) * 100:.1f}" if f.get('revenue_growth') else "  Gelir: N/A")
        lines.append(f"  Kazanç Büyümesi: %{f.get('earnings_growth', 0) * 100:.1f}" if f.get('earnings_growth') else "  Kazanç: N/A")
        # Risk
        lines.append(f"\n⚠️ *RİSK & BORÇ*")
        lines.append(f"  Borç/Öz Sermaye: {f.get('debt_to_equity', 'N/A'):.1f}%" if f.get('debt_to_equity') else "  Borç: N/A")
        lines.append(f"  Beta: {f.get('beta', 'N/A'):.2f}" if f.get('beta') else "  Beta: N/A")
        # Hedef
        lines.append(f"\n🎯 *HEDEF FİYAT*")
        lines.append(f"  52 Hafta Yüksek: {f.get('52w_high', 'N/A')}" if f.get('52w_high') else "  52W Yüksek: N/A")
        lines.append(f"  52 Hafta Düşük: {f.get('52w_low', 'N/A')}" if f.get('52w_low') else "  52W Düşük: N/A")
        lines.append(f"  Analist Hedefi: {f.get('target_price', 'N/A')}" if f.get('target_price') else "  Hedef: N/A")
        lines.append(f"  Analist Sayısı: {f.get('analyst_count', 0)}")
        # Sonuç
        lines.append(f"\n{'=' * 45}")
        lines.append(f"💡 *DEĞERLENDİRME:* {analysis['recommendation']}")
        return "\n".join(lines)

    @staticmethod
    def format_large_number(num: float) -> str:
        """Büyük sayıları formatla"""
        if not num:
            return "N/A"
        if num >= 1e12:
            return f"${num / 1e12:.2f}T"
        elif num >= 1e9:
            return f"${num / 1e9:.2f}M"
        elif num >= 1e6:
            return f"${num / 1e6:.2f}M"
        else:
            return f"${num:,.0f}"
