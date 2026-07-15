# ============================================================
# BOT SCALPING + BERITA + DATA FRESHNESS (VERSI FINAL)
# Sumber: Yahoo Finance (harga/vol), Google News, IDX scraping
# ============================================================

import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime
import time
import warnings
warnings.filterwarnings('ignore')

# ================= KONFIGURASI =================
TOKEN = "8777887691:AAHOTjVBkeiCMeHd4xOJkOHcX4dali-8hdE"      # Ganti dengan token dari @BotFather
CHAT_ID = "8467853860"         # ID Telegram kamu (atau grup)
# ===============================================

# ========== DAFTAR SAHAM SCALPING ==========
LIST_SAHAM = [
    'BUMI.JK', 'ELSA.JK', 'ENRG.JK', 'MEDC.JK', 'PGUN.JK', 'BREN.JK',
    'ANTM.JK', 'AMMN.JK', 'CUAN.JK', 'BNII.JK',
    'ASRI.JK', 'BIPI.JK', 'SMRA.JK', 'PWON.JK', 'BSDE.JK', 'WIKA.JK',
    'FREN.JK', 'MORA.JK', 'MTEL.JK', 'BUKA.JK',
    'FILM.JK', 'MCOL.JK', 'RANS.JK', 'MYRX.JK'
]
# ============================================

def kirim_telegram(pesan):
    """Kirim pesan ke Telegram (mode HTML)"""
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
            print(f"❌ Gagal: {resp.status_code} | {resp.text[:200]}")
    except Exception as e:
        print(f"❌ Error kirim: {e}")

def cek_freshness_data(df):
    """Cek apakah data terakhir = hari ini atau H-1"""
    last_date = df.index[-1].date()
    today_date = datetime.now().date()
    
    # Jika data terakhir adalah hari ini
    if last_date == today_date:
        return "✅ Data Fresh (Hari Ini)", ""
    
    # Jika data terakhir adalah kemarin (dan hari ini bukan akhir pekan)
    if today_date.weekday() < 5:  # Senin-Jumat
        if last_date == today_date - pd.Timedelta(days=1):
            return "⚠️ DATA TELAT (H-1)", f"⚠️ Harga pakai data {last_date}, BUKAN hari ini!"
        else:
            return f"⚠️ DATA TELAT ({ (today_date - last_date).days } hari)", f"⚠️ Data terakhir: {last_date}"
    else:
        # Akhir pekan (Sabtu/Minggu), data Jumat masih OK
        return "🟡 Pasar Libur (Data Jumat)", ""

def scrape_berita_google(kode):
    """Scrape sentimen dari Google News"""
    try:
        saham = yf.Ticker(kode)
        nama = saham.info.get('shortName', kode.replace('.JK', ''))
        search_url = f"https://news.google.com/search?q={nama.replace(' ', '+')}+saham"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        resp = requests.get(search_url, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            return "📰 Sentimen: Gagal akses"
        
        text = resp.text.lower()
        pos = ['naik', 'melesat', 'rekor', 'laba', 'dividen', 'ekspansi', 'akuisisi', 'serok', 'target']
        neg = ['turun', 'anjlok', 'rugi', 'utang', 'krisis', 'skandal', 'warning', 'delisting']
        
        pos_count = sum(1 for kw in pos if kw in text)
        neg_count = sum(1 for kw in neg if kw in text)
        
        if pos_count > neg_count and pos_count >= 2:
            return "📰 Sentimen: Positif (Buy on Rumor)"
        elif neg_count > pos_count and neg_count >= 2:
            return "📰 Sentimen: Negatif (Sell on News)"
        else:
            return "📰 Sentimen: Netral"
    except:
        return "📰 Sentimen: Error"

def scrape_pengumuman_idx(kode):
    """Cek pengumuman emiten dari IDX (sederhana)"""
    try:
        ticker = kode.replace('.JK', '')
        url = f"https://www.idx.co.id/id/perusahaan-tercatat/laporan-keuangan-dan-tahunan/{ticker}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            return "📢 IDX: Gagal akses"
        
        text = resp.text.lower()
        keywords = {
            'dividen': '💵 Dividen',
            'right issue': '📈 Right Issue',
            'akuisisi': '🤝 Akuisisi',
            'rugi': '⚠️ Rugi',
            'laba': '📊 Laba',
            'korporasi': '🏢 Aksi Korporasi',
            'buyback': '🔄 Buyback'
        }
        found = [v for k, v in keywords.items() if k in text]
        return f"📢 IDX: {', '.join(found) if found else 'Tidak ada pengumuman baru'}"
    except:
        return "📢 IDX: Error"

def scrape_foreign_flow():
    """Cek net foreign dari CNBC Indonesia (sederhana)"""
    try:
        url = "https://www.cnbcindonesia.com/market"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return "🌏 Asing: Gagal akses"
        text = resp.text.lower()
        if 'net foreign buy' in text or 'asing serok' in text or 'asing borong' in text:
            return "🌏 Asing: Net Buy (cenderung positif)"
        elif 'net foreign sell' in text or 'asing obral' in text or 'asing lepas' in text:
            return "🌏 Asing: Net Sell (cenderung negatif)"
        else:
            return "🌏 Asing: Netral / Tidak terdeteksi"
    except:
        return "🌏 Asing: Error"

def analisis_lengkap(kode):
    """
    Analisis lengkap: teknikal + volume + bandarmology + berita + data freshness
    """
    try:
        # 1. Ambil data dari Yahoo Finance
        saham = yf.Ticker(kode)
        df = saham.history(period="60d")
        if df.empty or len(df) < 20:
            return None
        
        info = saham.info
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 2. Freshness data
        data_status, data_warning = cek_freshness_data(df)
        
        # 3. Hitung indikator teknikal
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MA20'] = ta.sma(df['Close'], length=20)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        last_rsi = df['RSI'].iloc[-1]
        harga = last['Close']
        atr = df['ATR'].iloc[-1]
        perubahan = ((harga - prev['Close']) / prev['Close']) * 100
        
        # 4. Volume
        vol_hari = last['Volume']
        avg_vol_5 = df['Volume'].rolling(5).mean().iloc[-1]
        vs_minggu = vol_hari / avg_vol_5 if avg_vol_5 > 0 else 0
        
        # 5. Bandarmology
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
        
        # 6. Scraping berita & pengumuman
        berita_google = scrape_berita_google(kode)
        pengumuman_idx = scrape_pengumuman_idx(kode)
        foreign_flow = scrape_foreign_flow()  # global, tidak per saham
        
        # 7. Skor akhir
        skor = bandar_score
        if last_rsi > 70: skor += 1
        if abs(perubahan) > 5: skor += 1
        if vs_minggu > 3.0: skor += 1
        
        if skor >= 6:
            status = "🔴 INDIKASI GORENGAN TINGGI"
            rekom = "HINDARI! Resiko besar."
        elif skor >= 4:
            status = "🟡 POTENSI SCALPING"
            rekom = "Cocok scalping, pasang SL ketat!"
        else:
            status = "🟢 Normal"
            rekom = "Aman untuk trading harian"
        
        # 8. SL & TP (scalping)
        if atr:
            sl = round(harga - (1.8 * atr), 2)
            tp = round(harga + (3.0 * atr), 2)
        else:
            sl, tp = 0, 0
        
        # 9. Fundamental singkat
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
            'berita_google': berita_google,
            'pengumuman_idx': pengumuman_idx,
            'foreign_flow': foreign_flow,
            'data_status': data_status,
            'data_warning': data_warning,
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
print(f"🚀 BOT SCALPING FINAL - {waktu}")

# Ambil foreign flow global (sekali saja)
foreign_flow_global = scrape_foreign_flow()

semua_hasil = []
for kode in LIST_SAHAM:
    res = analisis_lengkap(kode)
    if res:
        # Timpa foreign flow global agar semua saham punya info yang sama
        res['foreign_flow'] = foreign_flow_global
        semua_hasil.append(res)

# Urutkan berdasarkan skor (tertinggi = paling berpotensi)
semua_hasil.sort(key=lambda x: x['skor'], reverse=True)
berbahaya = [h for h in semua_hasil if h['skor'] >= 4]
aman = [h for h in semua_hasil if h['skor'] < 4]

# ========== SUSUN PESAN TELEGRAM (FORMAT KUAT) ==========
pesan = f"<b>⚡ SCALPING GORENGAN - FINAL</b>\n"
pesan += f"📅 {waktu} WIB\n"
pesan += f"📊 Total: {len(semua_hasil)} saham | Sinyal: {len(berbahaya)}\n"
pesan += "=" * 30 + "\n\n"

if berbahaya:
    pesan += "<b>🚨 SAHAM DENGAN POTENSI SCALPING</b>\n\n"
    for h in berbahaya[:5]:
        pesan += f"🏢 <b>{h['kode']}</b> - {h['nama']}\n"
        pesan += f"💰 Rp{h['harga']:.0f} | 📈 {h['perubahan']:+.2f}%\n"
        pesan += f"📅 {h['data_status']}\n"
        if h['data_warning']:
            pesan += f"   ⚠️ {h['data_warning']}\n"
        pesan += f"📊 RSI: {h['rsi']} | MA20: Rp{h['ma20']:.0f}\n"
        pesan += f"📦 Vol: {h['vol_hari']:,} | Vs Minggu: {h['vs_minggu']}x\n"
        pesan += f"🕵️ {h['bandar_status']}\n"
        pesan += f"{h['berita_google']}\n"
        pesan += f"{h['pengumuman_idx']}\n"
        pesan += f"{h['foreign_flow']}\n"
        pesan += f"⚠️ <b>Status:</b> {h['status']}\n"
        pesan += f"💡 <b>Strategi:</b> {h['rekom']}\n"
        pesan += f"🔴 <b>SL:</b> Rp{h['sl']:.0f} | 🟢 <b>TP:</b> Rp{h['tp']:.0f}\n"
        pesan += f"📋 Kap: {h['kap']}\n"
        pesan += "-" * 25 + "\n"
else:
    pesan += "✅ Tidak ada saham dengan potensi scalping tinggi hari ini.\n"

if aman and len(aman) > 0:
    pesan += "\n<b>📊 PANTAUAN (Skor Tertinggi):</b>\n"
    for h in aman[:3]:
        pesan += f"🔹 {h['kode']} | Skor: {h['skor']} | RSI: {h['rsi']} | Rp{h['harga']:.0f}\n"

# Tambahkan footer info
pesan += "\n" + "=" * 30 + "\n"
pesan += "📌 Bot by Senior Quant | Data: Yahoo Finance + IDX + CNBC"

kirim_telegram(pesan)
print("✅ Selesai! Cek Telegram.")
