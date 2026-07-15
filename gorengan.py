# ===== BOT SCALPING GORENGAN PRE-MARKET (Rp 2 Juta - 30 Saham Filter) =====
# Dikirim otomatis jam 07:00 WIB (Pagi) & 15:45 WIB (Sore)

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

# ========== DAFTAR 30 SAHAM SCALPING (AMAN & LIKUID) ==========
# Kriteria: Harga < Rp1.200, Volume Tinggi, Tidak Delisting/Suspensi, Tanpa GOTO
LIST_SAHAM = [
    # === ENERGI & BATUBARA (Sering kena sentimen harga komoditas) ===
    'BUMI.JK',    # ~Rp50-100   | Volume super besar, cocok scalping murah
    'ELSA.JK',    # ~Rp450-500  | Energi defensif, likuid
    'ENRG.JK',    # ~Rp200-300  | Kapitalisasi besar, volume harian tinggi
    'MEDC.JK',    # ~Rp1.000-1.200 | Responsif isu migas
    'PGUN.JK',    # ~Rp200-400  | Energi, sering kena isu
    'BREN.JK',    # ~Rp500-800  | Volatil tinggi, sering pump-dump
    
    # === TAMBANG & NIKEL ===
    'ANTM.JK',    # ~Rp1.000-1.200 | Sensitif harga emas & nikel
    'AMMN.JK',    # ~Rp800-1.000  | Tambang tembaga/emas, baru IPO & volatil
    'CUAN.JK',    # ~Rp500-800   | Volatilitas paling agresif
    
    # === PERBANKAN MURAH & LIKUID ===
    'BNII.JK',    # ~Rp1.000-1.200 | Likuiditas cukup, harga masih terjangkau
    
    # === PROPERTI & INFRASTRUKTUR (Sering kena sentimen kebijakan) ===
    'ASRI.JK',    # ~Rp100-200   | Properti murah, masih aktif
    'BIPI.JK',    # ~Rp50-100    | Infrastruktur, aktivitas transaksi besar
    'SMRA.JK',    # ~Rp450-480   | Properti, sering kena sentimen kebijakan
    'PWON.JK',    # ~Rp400-420   | Properti, volatilitas bagus
    'BSDE.JK',    # ~Rp1.000-1.150 | Properti likuid, fundamental kuat
    'WIKA.JK',    # ~Rp200-400   | Konstruksi, volatil
    'JSMR.JK',    # ~Rp4.000-5.000 | Likuid & responsif (opsional, hapus jika terlalu mahal)
    
    # === TELEKOMUNIKASI & TEKNOLOGI (Gorengan favorit) ===
    'FREN.JK',    # ~Rp50-100    | Telekomunikasi murah, paling sering digoreng
    'MORA.JK',    # ~Rp200-400   | Internet, likuiditas cukup
    'MTEL.JK',    # ~Rp500-800   | Menara telekom, bergerak cepat
    'BUKA.JK',    # ~Rp200-300   | Teknologi, volatil, likuid
    
    # === RETAIL, MEDIA & KONSUMER ===
    'FILM.JK',    # ~Rp200-400   | Media, sering kena sentimen
    'MCOL.JK',    # ~Rp300-500   | Ritel, likuid & cepat
    'RANS.JK',    # ~Rp200-400   | Pasca IPO, volatilitas tinggi
    'MYRX.JK',    # ~Rp100-200   | Properti murah, sering pump
]
# =======================================================

def kirim_pesan(pesan):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        resp = requests.get(url, params={
            'chat_id': CHAT_ID, 
            'text': pesan, 
            'parse_mode': 'HTML'
        }, timeout=10)
        if resp.status_code == 200:
            print("✅ Pesan berhasil terkirim!")
        else:
            print(f"❌ Error: {resp.status_code} | {resp.text}")
    except Exception as e:
        print(f"❌ Gagal konek: {e}")

def get_news_sentiment(kode, nama):
    try:
        search_url = f"https://news.google.com/search?q={nama.replace(' ', '+')}+saham"
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = requests.get(search_url, headers=headers, timeout=8)
        if resp.status_code != 200:
            return "📰 Netral (gagal akses)", 0, 0
        
        text = resp.text.lower()
        rumor = ['akuisisi','ekspansi','target','rekomendasi','naik','potensi','kerjasama','dividen','buyback','melesat']
        news = ['turun','anjlok','koreksi','jual','bearish','negatif','gagal','rugi','utang','krisis','skandal']
        
        rumor_count = sum(1 for kw in rumor if kw in text)
        news_count = sum(1 for kw in news if kw in text)
        
        if rumor_count > news_count and rumor_count >= 2:
            return "📰 Buy on RUMOR (Positif)", rumor_count, news_count
        elif news_count > rumor_count and news_count >= 2:
            return "📰 Sell on NEWS (Negatif)", rumor_count, news_count
        else:
            return "📰 Netral", rumor_count, news_count
    except:
        return "📰 Sentimen: Gagal", 0, 0

def analisis_scalping(kode):
    try:
        saham = yf.Ticker(kode)
        df = saham.history(period="60d")
        if df.empty or len(df) < 20:
            return None
        
        info = saham.info
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Indikator
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MA20'] = ta.sma(df['Close'], length=20)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        last_rsi = last['RSI']
        harga = last['Close']
        atr = last['ATR']
        perubahan = ((harga - prev['Close']) / prev['Close']) * 100
        
        # Volume
        vol_hari = last['Volume']
        vol_kemarin = prev['Volume']
        avg_vol_5 = df['Volume'].rolling(5).mean().iloc[-1]
        
        vs_kemarin = vol_hari / vol_kemarin if vol_kemarin > 0 else 0
        vs_minggu = vol_hari / avg_vol_5 if avg_vol_5 > 0 else 0
        
        # Bandarmology
        bandar_score = 0
        bandar_label = "⚪ Tidak terdeteksi"
        if vs_minggu > 2.0:
            bandar_score += 3
            bandar_label = "🔴 Akumulasi Bandar (Volume Melonjak)"
        if vs_minggu > 1.5 and harga > last['MA20']:
            bandar_score += 2
            bandar_label += " & Proteksi MA20"
        if vs_minggu > 1.8 and 0 < perubahan < 2:
            bandar_score += 1
            bandar_label += " (Distribusi)"
        
        if bandar_score >= 5: bandar_status = "🔥 BANDAR TERDETEKSI"
        elif bandar_score >= 3: bandar_status = "⚠️ Potensi Bandar"
        else: bandar_status = "✅ Normal (Aman)"
        
        # Sentimen
        nama = info.get('shortName', kode)
        sentimen_label, _, _ = get_news_sentiment(kode, nama)
        
        # Skor Akhir
        skor_akhir = bandar_score
        if last_rsi > 70: skor_akhir += 1
        if abs(perubahan) > 5: skor_akhir += 1
        if vs_minggu > 3.0: skor_akhir += 1
        
        if skor_akhir >= 6:
            status = "🔴 INDIKASI GORENGAN TINGGI"
            rekom = "HINDARI! Resiko besar untuk scalping."
        elif skor_akhir >= 4:
            status = "🟡 POTENSI SCALPING (WASPADA)"
            rekom = "Cocok scalping jika entry di support. Pasang SL!"
        else:
            status = "🟢 Normal / Likuid"
            rekom = "Aman untuk trading harian."
        
        # SL & TP Scalping (lebih ketat)
        if atr:
            sl = round(harga - (1.8 * atr), 2)
            tp = round(harga + (3.0 * atr), 2)
        else:
            sl, tp = 0, 0
        
        market_cap = info.get('marketCap', 0)
        kap_str = f"Rp{market_cap/1e12:.2f}T" if market_cap > 0 else "N/A"
        
        return {
            'kode': kode.replace('.JK', ''),
            'nama': nama[:25],
            'harga': harga,
            'perubahan': perubahan,
            'rsi': round(last_rsi, 2),
            'ma20': round(last['MA20'], 2),
            'vol_hari': int(vol_hari),
            'vol_kemarin': int(vol_kemarin),
            'avg_vol_5': int(avg_vol_5),
            'vs_kemarin': round(vs_kemarin, 1),
            'vs_minggu': round(vs_minggu, 1),
            'bandar_status': bandar_status,
            'sentimen_label': sentimen_label,
            'skor': skor_akhir,
            'status': status,
            'rekom': rekom,
            'sl': sl,
            'tp': tp,
            'kap': kap_str,
        }
    except Exception as e:
        print(f"Error baca {kode}: {e}")
        return None

# ========== MAIN ==========
waktu = datetime.now().strftime('%d-%m-%Y %H:%M')
print(f"Scan Scalping PRE-MARKET dimulai: {waktu}")

semua_hasil = []
for kode in LIST_SAHAM:
    res = analisis_scalping(kode)
    if res:
        semua_hasil.append(res)

semua_hasil.sort(key=lambda x: x['skor'], reverse=True)
berbahaya = [h for h in semua_hasil if h['skor'] >= 4]
aman = [h for h in semua_hasil if h['skor'] < 4]

# === SUSUN PESAN TELEGRAM (Format Rapi) ===
pesan = "<b>⚡ SCALPING GORENGAN PRE-MARKET</b> - " + waktu + " WIB\n"
pesan += "<b>Total:</b> " + str(len(semua_hasil)) + " saham | <b>Sinyal:</b> " + str(len(berbahaya)) + "\n"
pesan += "================================\n"
pesan += "⏰ Scan Pagi (07:00) & Sore (15:45) | 🔥 Fokus Scalping\n"
pesan += "================================\n\n"

if berbahaya:
    pesan += "<b>🚨 SAHAM DENGAN POTENSI SCALPING</b>\n\n"
    for h in berbahaya[:5]:
        pesan += "🏢 <b>" + h['kode'] + "</b> - " + h['nama'] + "\n"
        pesan += "💰 Rp" + f"{h['harga']:.0f}" + " | 📈 " + f"{h['perubahan']:+.2f}" + "%\n"
        pesan += "📊 RSI: " + str(h['rsi']) + " | MA20: Rp" + f"{h['ma20']:.0f}" + "\n"
        pesan += "📦 Vol: " + f"{h['vol_hari']:,}" + " | Vs Minggu: " + f"{h['vs_minggu']}x" + "\n"
        pesan += "🕵️ <b>Bandarmology:</b> " + h['bandar_status'] + "\n"
        pesan += h['sentimen_label'] + "\n"
        pesan += "⚠️ <b>Status:</b> " + h['status'] + "\n"
        pesan += "💡 <b>Strategi:</b> " + h['rekom'] + "\n"
        pesan += "🔴 <b>SL:</b> Rp" + f"{h['sl']:.0f}" + " | 🟢 <b>TP:</b> Rp" + f"{h['tp']:.0f}" + "\n"
        pesan += "📋 Kap: " + h['kap'] + "\n"
        pesan += "------------------------\n"
else:
    pesan += "✅ Tidak ada saham dengan potensi scalping tinggi hari ini.\n\n"

if aman and len(aman) > 0:
    pesan += "<b>📊 PANTAUAN (Skor Tertinggi):</b>\n"
    for h in aman[:3]:
        pesan += "🔹 " + h['kode'] + " | Skor: " + str(h['skor']) + " | RSI: " + str(h['rsi']) + "\n"

kirim_pesan(pesan)
print("✅ Selesai! Cek Telegram.")
