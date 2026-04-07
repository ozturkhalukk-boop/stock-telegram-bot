# Hisse Tarama ve Potansiyel Analizi Modülü - SPOT İŞLEMLER
import config
from technical_analysis import TechnicalAnalyzer
from datetime import datetime
import time


class StockScanner:
    """SPOT işlemler için BIST 100 hisse tarama"""

    def __init__(self, min_potential=5.0):
        self.min_potential = min_potential
        self.scanned_stocks = []
        self.high_potential_stocks = []
        self.top_picks = []
        self.errors = []

    def scan_bist_100(self, limit=15):
        """BIST 100 hisselerini tara - SPOT için"""
        stocks_to_scan = config.BIST_100_STOCKS[:limit] if limit else config.BIST_100_STOCKS
        results = []
        success_count = 0
        error_count = 0

        print(f"🔍 BIST 100 taranıyor... ({len(stocks_to_scan)} hisse)")

        for i, symbol in enumerate(stocks_to_scan, 1):
            try:
                analyzer = TechnicalAnalyzer(symbol, period="2mo")
                analysis = analyzer.calculate_all()

                if analysis and analysis.get('current_price'):
                    # Potansiyel değerini düzelt
                    potential = self._calculate_spot_potential(analysis)
                    analysis['potential_percent'] = potential
                    analysis['symbol'] = symbol.replace('.IS', '')
                    analysis['market'] = "BIST 100 🇹🇷"
                    results.append(analysis)
                    success_count += 1
                    print(f"  ✅ [{i}/{len(stocks_to_scan)}] {symbol.replace('.IS', '')} - Potansiyel: %{potential:.1f}")
                else:
                    error_count += 1
                    print(f"  ⚠️ [{i}/{len(stocks_to_scan)}] {symbol} - Veri yok")

                # Rate limiting
                time.sleep(0.3)

            except Exception as e:
                error_count += 1
                self.errors.append(f"{symbol}: {str(e)}")
                print(f"  ❌ [{i}/{len(stocks_to_scan)}] {symbol} hata: {str(e)[:50]}")
                continue

        self.scanned_stocks = results
        print(f"📊 Tarama tamamlandı: {success_count} başarılı, {error_count} hata")
        return results

    def scan_world_markets(self, region=None):
        """Dünya borsalarını tara"""
        results = []
        markets = {region: config.WORLD_MARKETS[region]} if region else config.WORLD_MARKETS

        print(f"🌍 Dünya borsaları taranıyor...")

        for region_key, market_data in markets.items():
            print(f"  📍 {market_data['name']}")
            for symbol in market_data.get('stocks', [])[:8]:
                try:
                    analyzer = TechnicalAnalyzer(symbol, period="2mo")
                    analysis = analyzer.calculate_all()

                    if analysis and analysis.get('current_price'):
                        potential = self._calculate_spot_potential(analysis)
                        analysis['potential_percent'] = potential
                        analysis['symbol'] = symbol
                        analysis['market'] = market_data['name']
                        results.append(analysis)
                        print(f"    ✅ {symbol} - Potansiyel: %{potential:.1f}")

                    time.sleep(0.3)

                except Exception as e:
                    self.errors.append(f"{symbol}: {str(e)}")
                    print(f"    ❌ {symbol} hata")
                    continue

        self.scanned_stocks.extend(results)
        return results

    def _calculate_spot_potential(self, analysis):
        """SPOT için gerçekçi potansiyel hesapla"""
        current = analysis.get('current_price', 0)
        resistance = analysis.get('resistance', 0)

        if current > 0 and resistance > current:
            potential = ((resistance - current) / current) * 100
            # Maksimum %15 ile sınırla
            return min(15, max(1, potential))
        return 2.0

    def filter_high_potential(self, min_percent=None):
        """Yüksek potansiyelli hisseleri filtrele"""
        min_pct = min_percent if min_percent else self.min_potential
        self.high_potential_stocks = [
            stock for stock in self.scanned_stocks
            if stock.get('potential_percent', 0) >= min_pct
        ]
        self.high_potential_stocks.sort(key=lambda x: x.get('potential_percent', 0), reverse=True)
        return self.high_potential_stocks

    def get_top_picks(self, count=10, market=None):
        """En iyi SPOT hisse önerileri"""
        if market:
            filtered = [s for s in self.high_potential_stocks if market.lower() in s.get('market', '').lower()]
        else:
            filtered = self.high_potential_stocks
        self.top_picks = filtered[:count]
        return self.top_picks

    def format_daily_report(self, top_stocks=None):
        """SPOT için günlük rapor formatı"""
        if top_stocks is None:
            top_stocks = self.get_top_picks()

        if not top_stocks:
            return """📊 *GÜNLÜK HİSSE RAPORU*

Bugün için yeterli potansiyel hisse bulunamadı.

Tekrar denemek için /rapor yazın."""

        lines = []
        lines.append("📊 *GÜNLÜK HİSSE ANALİZ RAPORU*")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"📅 Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        lines.append(f"🔍 Taranan: {len(self.scanned_stocks)} hisse")
        lines.append(f"🎯 %5+ Potansiyel: {len(self.high_potential_stocks)} hisse")
        lines.append(f"⭐ Önerilen: {len(top_stocks)} hisse")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")
        lines.append("📈 *SPOT İŞLEM İÇİN ÖNERİLER:*")
        lines.append("")

        for i, stock in enumerate(top_stocks, 1):
            potential = stock.get('potential_percent', 0)
            emoji = "🔥" if potential >= 10 else "⚡" if potential >= 7 else "💪"
            symbol = stock.get('symbol', 'N/A')
            price = stock.get('current_price', 'N/A')
            target = stock.get('target_price', price * 1.05)
            stop = stock.get('stop_loss', price * 0.97)
            rsi = stock.get('rsi', 'N/A')

            lines.append(f"{emoji} *{i}. {symbol}*")
            lines.append(f"   💰 Fiyat: {price}")
            lines.append(f"   📈 Potansiyel: *%{potential:.1f}*")
            lines.append(f"   🎯 Hedef: {target:.2f} | Stop: {stop:.2f}")
            lines.append(f"   📊 RSI: {rsi}")
            lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("⚠️ *UYARI:* Bu bilgiler SPOT yatırım tavsiyesi DEĞİLDİR!")
        lines.append("📌 Kendi araştırmanızı yapınız.")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━")

        return "\n".join(lines)


def get_stock_info(symbol):
    """Belirtilen hisse hakkında bilgi al"""
    try:
        analyzer = TechnicalAnalyzer(symbol, period="2mo")
        analysis = analyzer.calculate_all()
        if analysis:
            analysis['symbol'] = symbol.replace('.IS', '')
        return analysis
    except Exception as e:
        print(f"Hisse bilgi hatası: {e}")
        return None
