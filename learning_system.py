# -*- coding: utf-8 -*-
"""
📊 GELİŞMİŞ ÖĞRENEN HİSSE ANALİZ SİSTEMİ
Tarama geçmişini karşılaştıran ve öğrenen sistem
"""
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import numpy as np


class LearningSystem:
    """
    Gelişmiş öğrenen sistem:
    - Tarama geçmişi saklar
    - Önceki ve sonraki taramaları karşılaştırır
    - Kalıplardan öğrenir
    - Gösterge ağırlıklarını optimize eder
    """

    def __init__(self, db_path: str = "learning_data.db"):
        self.db_path = db_path
        self.init_database()
        self.weights = self.load_weights()
        self.last_scan_data = None

    def init_database(self):
        """Veritabanını başlat"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Geri bildirimler tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                user_feedback TEXT NOT NULL,
                price_at_feedback REAL,
                current_price REAL,
                price_change_percent REAL,
                is_profitable INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tarama geçmişi tablosu - HER TARAMA KAYDEDİLİYOR
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_date DATE NOT NULL,
                scan_type TEXT NOT NULL,
                total_stocks INTEGER,
                avg_potential REAL,
                top_picks TEXT,
                market_sentiment TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Hisse tarama detayları - HER HİSSE ANALİZİ
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_scan_details (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                price REAL,
                potential_percent REAL,
                rsi REAL,
                macd REAL,
                signal TEXT,
                recommendation TEXT,
                momentum_score REAL,
                FOREIGN KEY (scan_id) REFERENCES scan_history(id)
            )
        """)

        # Değişim takibi - ÖNCEKİ VS SONRAKI
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                previous_scan_id INTEGER,
                current_scan_id INTEGER,
                price_change REAL,
                potential_change REAL,
                rsi_change REAL,
                recommendation_changed INTEGER,
                was_correct_prediction INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tahminler tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                predicted_direction TEXT NOT NULL,
                predicted_price REAL,
                confidence REAL,
                actual_price REAL,
                actual_direction TEXT,
                actual_change_percent REAL,
                is_correct INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Öğrenilmiş kalıplar tablosu
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                rsi_range TEXT,
                macd_signal TEXT,
                price_position TEXT,
                volume_trend TEXT,
                success_rate REAL,
                occurrence_count INTEGER,
                avg_return_percent REAL,
                avg_duration_days INTEGER,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Teknik parametre ağırlıkları
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS indicator_weights (
                indicator_name TEXT PRIMARY KEY,
                weight REAL DEFAULT 1.0,
                accuracy_score REAL DEFAULT 0.5,
                sample_count INTEGER DEFAULT 0,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Başlatıcı ağırlıklar
        default_indicators = [
            ('rsi', 1.0), ('macd', 1.0), ('sma_20', 0.8),
            ('sma_50', 0.7), ('bollinger', 0.9), ('stochastic', 0.8),
            ('volume', 0.6), ('support_resistance', 1.0),
            ('news_sentiment', 1.2), ('fibonacci', 0.7),
            ('ichimoku', 0.8), ('adx', 0.7), ('momentum', 0.8)
        ]
        for indicator, weight in default_indicators:
            cursor.execute("""
                INSERT OR IGNORE INTO indicator_weights (indicator_name, weight)
                VALUES (?, ?)
            """, (indicator, weight))

        conn.commit()
        conn.close()

    def load_weights(self) -> Dict[str, float]:
        """Ağırlıkları veritabanından yükle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT indicator_name, weight FROM indicator_weights")
        weights = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return weights

    # ============================================
    # TARAMA KAYITLARI
    # ============================================

    def save_scan(self, scan_type: str, total_stocks: int, stocks_data: List[Dict]) -> int:
        """Tarama sonuçlarını kaydet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Ortalama potansiyel hesapla
        potentials = [s.get('potential_percent', 0) for s in stocks_data if s.get('potential_percent')]
        avg_potential = sum(potentials) / len(potentials) if potentials else 0

        # En iyi 10 hisseyi kaydet
        top_picks = sorted(stocks_data, key=lambda x: x.get('potential_percent', 0), reverse=True)[:10]
        top_picks_json = json.dumps([{'symbol': s.get('symbol'), 'potential': s.get('potential_percent')} for s in top_picks])

        # Tarama kaydı oluştur
        cursor.execute("""
            INSERT INTO scan_history (scan_date, scan_type, total_stocks, avg_potential, top_picks)
            VALUES (?, ?, ?, ?, ?)
        """, (datetime.now().date().isoformat(), scan_type, total_stocks, avg_potential, top_picks_json))

        scan_id = cursor.lastrowid

        # Hisse detaylarını kaydet
        for stock in stocks_data:
            cursor.execute("""
                INSERT INTO stock_scan_details
                (scan_id, symbol, price, potential_percent, rsi, macd, signal, recommendation, momentum_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scan_id,
                stock.get('symbol'),
                stock.get('current_price'),
                stock.get('potential_percent', 0),
                stock.get('rsi'),
                stock.get('macd'),
                stock.get('signal', 'NÖTR'),
                stock.get('recommendation', 'NÖTR'),
                stock.get('momentum_score', 0)
            ))

        conn.commit()
        conn.close()

        # Son taramayı güncelle
        self.last_scan_data = {
            'scan_id': scan_id,
            'stocks': stocks_data,
            'date': datetime.now().isoformat()
        }

        return scan_id

    def compare_with_previous_scan(self, current_stocks: List[Dict]) -> Dict:
        """Mevcut taramayı önceki taramayla karşılaştır ve öğren"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Son taramayı al
        cursor.execute("""
            SELECT id, scan_date, total_stocks, avg_potential, top_picks
            FROM scan_history
            ORDER BY scan_id DESC
            LIMIT 1
        """)
        previous_scan = cursor.fetchone()

        if not previous_scan:
            conn.close()
            return {'status': 'İlk tarama', 'learning_data': None}

        prev_scan_id, prev_date, prev_total, prev_avg_pot, prev_top_json = previous_scan
        prev_top = json.loads(prev_top_json) if prev_top_json else []

        # Önceki hisse detaylarını al
        cursor.execute("""
            SELECT symbol, price, potential_percent, rsi, recommendation, momentum_score
            FROM stock_scan_details
            WHERE scan_id = ?
        """, (prev_scan_id,))
        prev_stocks = {row[0]: {
            'price': row[1],
            'potential': row[2],
            'rsi': row[3],
            'recommendation': row[4],
            'momentum': row[5]
        } for row in cursor.fetchall()}

        conn.close()

        # Değişim analizi
        changes = []
        learnings = []

        for stock in current_stocks:
            symbol = stock.get('symbol')
            if symbol in prev_stocks:
                prev = prev_stocks[symbol]
                curr_price = stock.get('current_price', 0)
                prev_price = prev.get('price', 0)
                curr_pot = stock.get('potential_percent', 0)
                prev_pot = prev.get('potential', 0)

                price_change = ((curr_price - prev_price) / prev_price * 100) if prev_price else 0
                pot_change = curr_pot - prev_pot

                # Değişiklik kaydet
                changes.append({
                    'symbol': symbol,
                    'price_change': price_change,
                    'potential_change': pot_change,
                    'previous_recommendation': prev.get('recommendation'),
                    'current_recommendation': stock.get('recommendation', 'NÖTR'),
                    'previous_rsi': prev.get('rsi'),
                    'current_rsi': stock.get('rsi')
                })

                # Öğrenme: Önceki potansiyel yüksekse ve düştüyse?
                if prev_pot > 5 and pot_change < -2:
                    learnings.append({
                        'type': 'potential_drop',
                        'symbol': symbol,
                        'prev_potential': prev_pot,
                        'curr_potential': curr_pot,
                        'lesson': f'{symbol} potansiyeli %{prev_pot:.1f} -> %{curr_pot:.1f} düştü'
                    })

                # Öğrenme: RSI aşırı alımdan normale düştüyse?
                if prev.get('rsi', 0) > 70 and stock.get('rsi', 0) < 70:
                    learnings.append({
                        'type': 'rsi_normalized',
                        'symbol': symbol,
                        'lesson': f'{symbol} RSI normalizasyonu (aşırı alımdan)'
                    })

                # Öğrenme: Fiyat yükseldi ama potansiyel düştüyse (kâr aldırma işareti)
                if price_change > 3 and pot_change < -3:
                    learnings.append({
                        'type': 'profit_taking',
                        'symbol': symbol,
                        'lesson': f'{symbol} kâr aldırma işareti (fiyat %{price_change:.1f} arttı, potansiyel %{pot_change:.1f} düştü)'
                    })

                # Öğrenme: Öneri değişikliği
                if prev.get('recommendation') != stock.get('recommendation', 'NÖTR'):
                    learnings.append({
                        'type': 'recommendation_change',
                        'symbol': symbol,
                        'prev': prev.get('recommendation'),
                        'curr': stock.get('recommendation', 'NÖTR'),
                        'lesson': f'{symbol} önerisi {prev.get("recommendation")} -> {stock.get("recommendation", "NÖTR")}'
                    })

        return {
            'status': 'comparison_done',
            'previous_scan_date': prev_date,
            'total_changes': len(changes),
            'learnings': learnings,
            'stock_changes': changes
        }

    def learn_from_scan_comparison(self, comparison_result: Dict):
        """Karşılaştırma sonucundan öğren"""
        if not comparison_result.get('learnings'):
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for learning in comparison_result.get('learnings', []):
            lesson_type = learning.get('type')

            # Kalıp başarısını güncelle
            if lesson_type == 'potential_drop':
                # Potansiyel düşüş kalıbı
                cursor.execute("""
                    UPDATE patterns
                    SET success_rate = success_rate * 0.95,
                        occurrence_count = occurrence_count + 1,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE pattern_type = 'potential_drop'
                """)

            elif lesson_type == 'rsi_normalized':
                # RSI normalizasyon kalıbı
                cursor.execute("""
                    UPDATE patterns
                    SET occurrence_count = occurrence_count + 1,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE pattern_type = 'rsi_normalized'
                """)

            elif lesson_type == 'profit_taking':
                # Kâr aldırma kalıbı
                cursor.execute("""
                    UPDATE patterns
                    SET success_rate = success_rate * 1.05,
                        occurrence_count = occurrence_count + 1,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE pattern_type = 'profit_taking'
                """)

        conn.commit()
        conn.close()

    # ============================================
    # KULLANICI GERİ BİLDİRİMLERİ
    # ============================================

    def save_feedback(self, symbol: str, recommendation: str, user_feedback: str,
                     price_at_feedback: float, current_price: float):
        """Kullanıcı geri bildirimini kaydet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        price_change = ((current_price - price_at_feedback) / price_at_feedback) * 100 if price_at_feedback else 0
        is_profitable = 1 if price_change > 0 else 0

        cursor.execute("""
            INSERT INTO feedback (symbol, recommendation, user_feedback, price_at_feedback, current_price, price_change_percent, is_profitable)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (symbol, recommendation, user_feedback, price_at_feedback, current_price, price_change, is_profitable))

        conn.commit()
        conn.close()

        # Başarı oranını güncelle
        self.update_indicator_accuracy()

    def record_prediction(self, symbol: str, predicted_direction: str,
                         predicted_price: float, confidence: float):
        """Tahmini kaydet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO predictions (symbol, predicted_direction, predicted_price, confidence)
            VALUES (?, ?, ?, ?)
        """, (symbol, predicted_direction, predicted_price, confidence))
        conn.commit()
        conn.close()

    def update_prediction_result(self, symbol: str, actual_price: float):
        """Tahmin sonucunu güncelle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Son tahmini bul
        cursor.execute("""
            SELECT id, predicted_direction, predicted_price
            FROM predictions
            WHERE symbol = ?
            ORDER BY id DESC
            LIMIT 1
        """, (symbol,))
        pred = cursor.fetchone()

        if pred:
            pred_id, pred_dir, pred_price = pred
            actual_change = ((actual_price - pred_price) / pred_price * 100) if pred_price else 0

            # Doğru tahmin mi?
            is_correct = 0
            if pred_dir == "YÜKSELİŞ" and actual_change > 0:
                is_correct = 1
            elif pred_dir == "DÜŞÜŞ" and actual_change < 0:
                is_correct = 1
            elif pred_dir == "NÖTR" and abs(actual_change) < 2:
                is_correct = 1

            cursor.execute("""
                UPDATE predictions
                SET actual_price = ?, actual_change_percent = ?, is_correct = ?
                WHERE id = ?
            """, (actual_price, actual_change, is_correct, pred_id))

            # Kalıp kaydet
            self.record_pattern(symbol, pred_dir, actual_change)

        conn.commit()
        conn.close()

        # Gösterge doğruluğunu güncelle
        self.update_indicator_accuracy()

    def record_pattern(self, symbol: str, direction: str, change_percent: float):
        """Kalıp kaydet"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Son 30 günde bu kalıp var mı?
        cursor.execute("""
            SELECT id, occurrence_count, success_rate, avg_return_percent
            FROM patterns
            WHERE pattern_type = ?
            AND last_updated >= datetime('now', '-30 days')
            LIMIT 1
        """, (direction,))
        existing = cursor.fetchone()

        if existing:
            # Güncelle
            pattern_id, count, rate, avg_return = existing
            new_count = count + 1
            new_rate = (rate * count + (1 if abs(change_percent) > 2 else 0.5)) / new_count
            new_avg_return = (avg_return * count + change_percent) / new_count
            cursor.execute("""
                UPDATE patterns
                SET occurrence_count = ?, success_rate = ?, avg_return_percent = ?, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_count, new_rate, new_avg_return, pattern_id))
        else:
            # Yeni oluştur
            success = 1 if (direction == "YÜKSELİŞ" and change_percent > 0) or (direction == "DÜŞÜŞ" and change_percent < 0) else 0
            cursor.execute("""
                INSERT INTO patterns (pattern_type, success_rate, occurrence_count, avg_return_percent)
                VALUES (?, ?, 1, ?)
            """, (direction, success, change_percent))

        conn.commit()
        conn.close()

    def update_indicator_accuracy(self):
        """Göstergelerin doğruluğunu güncelle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Son 30 günlük tahminleri analiz et
        cursor.execute("""
            SELECT COUNT(*), SUM(is_correct)
            FROM predictions
            WHERE timestamp >= datetime('now', '-30 days')
        """)
        result = cursor.fetchone()
        total_preds = result[0] or 0
        correct_preds = result[1] or 0

        if total_preds >= 5:
            base_accuracy = correct_preds / total_preds

            # Ağırlıkları güncelle
            for indicator in self.weights.keys():
                # Başarı oranına göre ağırlık güncelle
                new_weight = min(2.0, max(0.3, base_accuracy + 0.5))
                cursor.execute("""
                    UPDATE indicator_weights
                    SET weight = ?, accuracy_score = ?, sample_count = ?, last_updated = CURRENT_TIMESTAMP
                    WHERE indicator_name = ?
                """, (new_weight, base_accuracy, total_preds, indicator))

        conn.commit()
        conn.close()
        self.weights = self.load_weights()

    # ============================================
    # KALIP ANALİZİ
    # ============================================

    def learn_from_patterns(self, technical_data: Dict) -> Dict[str, float]:
        """Kalıplardan öğren"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        pattern_score = 0.0
        weights_used = []
        pattern_boost = 1.0

        # Veritabanındaki başarılı kalıpları kontrol et
        cursor.execute("""
            SELECT pattern_type, success_rate, occurrence_count
            FROM patterns
            WHERE occurrence_count >= 3
            ORDER BY success_rate DESC
            LIMIT 5
        """)
        successful_patterns = cursor.fetchall()

        # RSI kalıbı
        rsi = technical_data.get('rsi')
        if rsi:
            if rsi < 30:
                pattern_score += self.weights.get('rsi', 1.0) * 0.3
                weights_used.append('rsi_oversold')
            elif 30 <= rsi <= 70:
                pattern_score += self.weights.get('rsi', 1.0) * 0.1
                weights_used.append('rsi_neutral')
            else:
                pattern_score -= self.weights.get('rsi', 1.0) * 0.2
                weights_used.append('rsi_overbought')

        # MACD kalıbı
        macd_hist = technical_data.get('macd_histogram', 0)
        if macd_hist > 0:
            pattern_score += self.weights.get('macd', 1.0) * 0.3
            weights_used.append('macd_bullish')
        else:
            pattern_score -= self.weights.get('macd', 1.0) * 0.2
            weights_used.append('macd_bearish')

        # Hacim kalıbı
        if technical_data.get('volume_increase', False):
            pattern_score += self.weights.get('volume', 0.6) * 0.2
            weights_used.append('volume_up')

        # Fiyat-MA kalıbı
        price = technical_data.get('current_price', 0)
        sma_20 = technical_data.get('sma_20')
        if price and sma_20:
            if price > sma_20:
                pattern_score += self.weights.get('sma_20', 0.8) * 0.2
                weights_used.append('price_above_sma20')
            else:
                pattern_score -= self.weights.get('sma_20', 0.8) * 0.1
                weights_used.append('price_below_sma20')

        # Momentum
        momentum = technical_data.get('momentum', 0)
        if momentum > 0:
            pattern_score += self.weights.get('momentum', 0.8) * 0.2
            weights_used.append('momentum_positive')
        else:
            pattern_score -= self.weights.get('momentum', 0.8) * 0.1
            weights_used.append('momentum_negative')

        # Başarılı kalıplardan bonus
        for pattern_type, success_rate, _ in successful_patterns:
            if 'rsi_oversold' in weights_used and 'rsi_oversold' in pattern_type.lower():
                pattern_boost += success_rate * 0.2
            if 'macd_bullish' in weights_used and 'bullish' in pattern_type.lower():
                pattern_boost += success_rate * 0.2

        conn.close()

        return {
            'pattern_score': pattern_score * pattern_boost,
            'weights_used': weights_used,
            'confidence': min(1.0, abs(pattern_score) / 3.0),
            'pattern_boost': pattern_boost,
            'successful_patterns': [p[0] for p in successful_patterns[:3]]
        }

    def get_user_preferences(self, user_id: str = "default") -> Dict:
        """Kullanıcı tercihlerini al"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT symbol, COUNT(*) as count, SUM(is_profitable) as success
            FROM feedback
            GROUP BY symbol
            HAVING count >= 2
        """)
        preferred = {}
        for row in cursor.fetchall():
            symbol, count, success = row
            preferred[symbol] = success / count if success else 0.5
        conn.close()
        return preferred

    def adjust_recommendation(self, base_recommendation: str, pattern_score: float,
                             sentiment_score: float = 0) -> Tuple[str, float]:
        """Öneriyi öğrenilen bilgiye göre ayarla"""
        # Temel puan
        score = 0.0
        if base_recommendation == "GÜÇLÜ AL":
            score = 3.0
        elif base_recommendation == "AL":
            score = 2.0
        elif base_recommendation == "NÖTR":
            score = 1.0
        elif base_recommendation == "SAT":
            score = -1.0
        else:
            score = -2.0

        # Öğrenilen kalıp puanını ekle
        score += pattern_score * 0.5

        # Haber duyarlılığını ekle
        score += sentiment_score * 0.3

        # Ayarlanmış öneri
        if score >= 3.5:
            return "GÜÇLÜ AL", min(1.0, abs(score) / 5.0)
        elif score >= 2.0:
            return "AL", min(1.0, abs(score) / 4.0)
        elif score >= 1.0:
            return "NÖTR", min(1.0, abs(score) / 3.0)
        elif score >= -1.0:
            return "SAT", min(1.0, abs(score) / 3.0)
        else:
            return "GÜÇLÜ SAT", min(1.0, abs(score) / 5.0)

    def get_statistics(self) -> Dict:
        """Öğrenme istatistiklerini al"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        stats = {}

        # Toplam geri bildirim
        cursor.execute("SELECT COUNT(*) FROM feedback")
        stats['total_feedback'] = cursor.fetchone()[0]

        # Toplam tarama
        cursor.execute("SELECT COUNT(*) FROM scan_history")
        stats['total_scans'] = cursor.fetchone()[0]

        # Son tarama
        cursor.execute("SELECT scan_date, scan_type, total_stocks FROM scan_history ORDER BY id DESC LIMIT 1")
        last_scan = cursor.fetchone()
        if last_scan:
            stats['last_scan'] = {
                'date': last_scan[0],
                'type': last_scan[1],
                'stocks': last_scan[2]
            }

        # Son 7 gün
        cursor.execute("""
            SELECT COUNT(*), AVG(price_change_percent), SUM(is_profitable)
            FROM feedback
            WHERE timestamp >= datetime('now', '-7 days')
        """)
        row = cursor.fetchone()
        stats['last_7_days'] = {
            'count': row[0] or 0,
            'avg_change': row[1] or 0,
            'success_count': row[2] or 0
        }

        # Tahmin doğruluğu
        cursor.execute("""
            SELECT COUNT(*), SUM(is_correct)
            FROM predictions
            WHERE timestamp >= datetime('now', '-30 days')
        """)
        pred_result = cursor.fetchone()
        if pred_result[0]:
            stats['prediction_accuracy'] = f"%{(pred_result[1] or 0) / pred_result[0] * 100:.1f}"
        else:
            stats['prediction_accuracy'] = "N/A"

        # En başarılı kalıplar
        cursor.execute("""
            SELECT pattern_type, success_rate, occurrence_count, avg_return_percent
            FROM patterns
            WHERE occurrence_count >= 3
            ORDER BY success_rate DESC
            LIMIT 5
        """)
        stats['top_patterns'] = [
            {'type': r[0], 'success_rate': r[1], 'occurrences': r[2], 'avg_return': r[3]}
            for r in cursor.fetchall()
        ]

        conn.close()
        return stats

    def export_learning_data(self) -> Dict:
        """Öğrenme verilerini dışa aktar"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data = {
            'weights': self.weights,
            'statistics': self.get_statistics(),
            'recent_feedback': [],
            'patterns': []
        }

        # Son geri bildirimler
        cursor.execute("""
            SELECT symbol, recommendation, price_change_percent, timestamp
            FROM feedback
            ORDER BY timestamp DESC
            LIMIT 20
        """)
        for row in cursor.fetchall():
            data['recent_feedback'].append({
                'symbol': row[0],
                'recommendation': row[1],
                'change': row[2],
                'date': row[3]
            })

        # Kalıplar
        cursor.execute("""
            SELECT pattern_type, success_rate, occurrence_count
            FROM patterns
            ORDER BY success_rate DESC
            LIMIT 10
        """)
        for row in cursor.fetchall():
            data['patterns'].append({
                'type': row[0],
                'success_rate': row[1],
                'occurrences': row[2]
            })

        conn.close()
        return data

    def get_comparison_summary(self) -> str:
        """Karşılaştırma özetini al"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Son 2 tarama
        cursor.execute("""
            SELECT scan_id, scan_date, total_stocks, avg_potential
            FROM scan_history
            ORDER BY scan_id DESC
            LIMIT 2
        """)
        scans = cursor.fetchall()

        if len(scans) < 2:
            conn.close()
            return "📊 *Karşılaştırma için en az 2 tarama gerekli*"

        # Farkları hesapla
        curr = scans[0]
        prev = scans[1]

        curr_id, curr_date, curr_total, curr_avg = curr
        prev_id, prev_date, prev_total, prev_avg = prev

        lines = []
        lines.append("🧠 *ÖĞRENME SİSTEMİ KARŞILAŞTIRMASI*")
        lines.append("=" * 45)
        lines.append(f"\n📅 *Tarihler:*")
        lines.append(f"  Önceki: {prev_date}")
        lines.append(f"  Mevcut: {curr_date}")
        lines.append(f"\n📊 *Taramalar:*")
        lines.append(f"  Hisse sayısı: {prev_total} → {curr_total}")
        lines.append(f"  Ort. potansiyel: %{prev_avg:.1f} → %{curr_avg:.1f}")

        # Hisse değişimleri
        cursor.execute("""
            SELECT symbol, price_change, potential_change
            FROM stock_changes
            WHERE current_scan_id = ?
            ORDER BY ABS(price_change) DESC
            LIMIT 5
        """, (curr_id,))
        changes = cursor.fetchall()

        if changes:
            lines.append(f"\n🔄 *En Çok Değişen Hisseler:*")
            for symbol, price_ch, pot_ch in changes:
                emoji = "📈" if price_ch > 0 else "📉"
                lines.append(f"  {emoji} {symbol}: %{price_ch:+.1f} fiyat, %{pot_ch:+.1f} potansiyel")

        conn.close()
        return "\n".join(lines)
