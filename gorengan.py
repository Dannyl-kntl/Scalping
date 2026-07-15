# ===== BOT "DIRECT MASAK" - SCraper + Analisis + Telegram =====
# Ambil data dari website, olah, kirim ke Telegram. FULL OTOMATIS!

import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ========== 🔴 GANTI DENGAN DATA ASLI KAMU ==========
TOKEN = "8777887691:AAHOTjVBkeiCMeHd4xOJkOHcX4dali-8hdE"   # Ganti dengan token dari @BotFather
CHAT_ID = "8467853860"      # ID Telegram kamu
# =====================================================

# ========== DAFTAR SAHAM YANG DI PANTAU ==========
LIST_SAHAM = [
    'BUMI.JK', 'ELSA.JK', 'ENRG.JK', 'MEDC.JK', 'PGUN.JK', 'BREN.JK',
    'ANTM.JK', 'AMMN.JK', 'CUAN.JK', 'BNII.JK',
    'ASRI.JK', 'BIPI.JK', 'SMRA.JK', 'PWON.JK', 'BSDE.JK', 'WIKA.JK',
    'FREN.JK', 'MORA.JK', 'MTEL.JK', 'BUKA.JK',
    'FILM.JK', 'MCOL.JK', 'RANS.JK', 'MYRX.JK'
]

def kirim_telegram(pesan):
    """Kirim pesan ke Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        resp = requests.get(url, params={
            'chat_id': CHAT_ID,
            'text': pesan,
            'parse_mode': 'HTML'
        }, timeout=30)
        if resp.status_code == 200:
            print("✅ Pesan terkirim!")
        else:
            print(f"❌ Gagal: {resp.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")

def scrape_berita_idx(kode):
    """
    SCRAPING BERITA DARI IDX (contoh: ambil pengumuman terbaru)
    Sumber: idx.co.id
    """
    try:
        # IDX official announcement URL
        url = f"https://www.idx.co.id/id/perusahaan-tercatat/laporan-keuangan-dan-tahunan/{kode.replace('.JK', '')}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            # Cari keyword di halaman
            text = resp.text.lower()
            keywords = ['laba', 'rugi', 'dividen', 'right issue', 'akuisisi', 'ekspansi']
            found = [kw for kw in keywords if kw in text]
            if found:
                return f"📰 Ditemukan berita: {', '.join(found)}"
        return "📰 Tidak ada berita baru"
    except:
        return "📰 Gagal scrape berita"

def scrape_rti_saham(kode):
    """
    SCRAPING DATA DARI RTI BUSINESS (harga real-time)
    Sumber: rti.co.id
    """
    try:
        # RTI stock quote endpoint (contoh)
        url = f"https://rti.co.id/stock-quote/{kode.replace('.JK', '')}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code == 200:
            # Parse harga dari HTML (sederhana)
            text = resp.text
            # Cari pola harga (contoh: "Rp1,234")
            import re
            harga_match = re.search(r'Rp([\d,]+)', text)
            if harga_match:
                return f"💰 Harga RTI: Rp{harga_match.group(1)}"
        return "📊 Data RTI tidak tersedia"
    except:
        return "📊 Gagal scrape RTI"

def analisis_lengkap(kode):
    """
    Analisis lengkap: Teknikal + Volume + Bandarmology + Berita
    """
    try:
        # 1. AMBIL DATA DARI YAHOO FINANCE (GRATIS)
        saham = yf.Ticker(kode)
        df = saham.history(period="60d")
        if df.empty or len(df) < 20:
            return None
        
        info = saham.info
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 2. HITUNG INDIKATOR TEKNIKAL
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MA20'] = ta.sma(df['Close'], length=20)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        last_rsi = df['RSI'].iloc[-1]
        harga = last['Close']
        atr = df['ATR'].iloc[-1]
        perubahan = ((harga - prev['Close']) / prev['Close']) * 100
        
        # 3. VOLUME
        vol_hari = last['Volume']
        avg_vol_5 = df['Volume'].rolling(5).mean().iloc[-1]
        vs_minggu = vol_hari / avg_vol_5 if avg_vol_5 > 0 else 0
        
        # 4. BANDARMOLOGY (deteksi bandar dari volume)
        bandar_score = 0
        bandar_label = "⚪ Tidak terdeteksi"
        if vs_minggu > 2.0:
            bandar_score += 3
            bandar_label = "🔴 Akumulasi Bandar (Volume Melonjak)"
        if vs_minggu > 1.5 and harga > df['MA20'].iloc[-1]:
            bandar_score += 2
            bandar_label += " & Proteksi MA20"
        
        if bandar_score >= 5:
            bandar_status = "🔥 BANDAR TERDETEKSI"
        elif bandar_score >= 3:
            bandar_status = "⚠️ Potensi Bandar"
        else:
            bandar_status = "✅ Normal"
        
        # 5. SCRAPING BERITA DARI IDX
        berita = scrape_berita_idx(kode)
        
        # 6. SCRAPING DATA DARI RTI
        rti_data = scrape_rti_saham(kode)
        
        # 7. SKOR AKHIR
        skor = bandar_score
        if last_rsi > 70: skor += 1
        if abs(perubahan) > 5: skor += 1
        if vs_minggu > 3.0: skor += 1
        
        if skor >= 6:
            status = "🔴 INDIKASI GORENGAN TINGGI"
            rekom = "HINDARI!"
        elif skor >= 4:
            status = "🟡 POTENSI SCALPING"
            rekom = "Cocok scalping, pasang SL!"
        else:
            status = "🟢 Normal"
            rekom = "Aman untuk trading"
        
        if atr:
            sl = round(harga - (1.8 * atr), 2)
            tp = round(harga + (3.0 * atr), 2)
        else:
            sl, tp = 0, 0
        
        market_cap = info.get('marketCap', 0)
        kap_str = f"Rp{market_cap/1e12:.2f}T" if market_cap > 0 else "N/A"
        
        return {
            'kode': kode.replace('.JK', ''),
            'nama': info.get('shortName', kode)[:25],
            'harga': harga,
            'perubahan': perubahan,
            'rsi': round(last_rsi, 2),
            'ma20': round(df['MA20'].iloc[-1], 2),
            'vol_hari': int(vol_hari),
            'avg_vol_5': int(avg_vol_5),
            'vs_minggu': round(vs_minggu, 1),
            'bandar_status': bandar_status,
            'berita': berita,
            'rti_data': rti_data,
            'skor': skor,
            'status': status,
            'rekom': rekom,
            'sl': sl,
            'tp': tp,
            'kap': kap_str,
        }
    except Exception as e:
        print(f"❌ Error {kode}: {e}")
        return None

# ========== MAIN PROGRAM ==========
waktu = datetime.now().strftime('%d-%m-%Y %H:%M')
print(f"🚀 BOT DIRECT MASAK - {waktu}")

semua_hasil = []
for kode in LIST_SAHAM:
    res = analisis_lengkap(kode)
    if res:
        semua_hasil.append(res)

semua_hasil.sort(key=lambda x: x['skor'], reverse=True)
berbahaya = [h for h in semua_hasil if h['skor'] >= 4]
aman = [h for h in semua_hasil if h['skor'] < 4]

# ========== SUSUN PESAN TELEGRAM ==========
pesan = f"<b>⚡ DIRECT MASAK - SCALPING</b>\n"
pesan += f"📅 {waktu} WIB\n"
pesan += f"📊 Total: {len(semua_hasil)} saham | Sinyal: {len(berbahaya)}\n"
pesan += "=" * 30 + "\n\n"

if berbahaya:
    pesan += "<b>🚨 SAHAM DENGAN POTENSI</b>\n\n"
    for h in berbahaya[:5]:
        pesan += f"🏢 <b>{h['kode']}</b> - {h['nama']}\n"
        pesan += f"💰 Rp{h['harga']:.0f} | 📈 {h['perubahan']:+.2f}%\n"
        pesan += f"📊 RSI: {h['rsi']} | MA20: Rp{h['ma20']:.0f}\n"
        pesan += f"📦 Vol: {h['vol_hari']:,} | Vs Minggu: {h['vs_minggu']}x\n"
        pesan += f"🕵️ {h['bandar_status']}\n"
        pesan += f"{h['berita']}\n"
        pesan += f"{h['rti_data']}\n"
        pesan += f"⚠️ {h['status']}\n"
        pesan += f"💡 {h['rekom']}\n"
        pesan += f"🔴 SL: Rp{h['sl']:.0f} | 🟢 TP: Rp{h['tp']:.0f}\n"
        pesan += f"📋 Kap: {h['kap']}\n"
        pesan += "-" * 25 + "\n"
else:
    pesan += "✅ Tidak ada saham dengan potensi tinggi hari ini.\n"

if aman and len(aman) > 0:
    pesan += "\n<b>📊 PANTAUAN:</b>\n"
    for h in aman[:3]:
        pesan += f"🔹 {h['kode']} | Skor: {h['skor']} | RSI: {h['rsi']}\n"

kirim_telegram(pesan)
print("✅ Selesai! Cek Telegram.")
