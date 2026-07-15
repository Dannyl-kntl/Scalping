# ===== BOT SCALPING GORENGAN PRE-MARKET (FIX 0 SAHAM) =====
# Menggunakan data 90 hari agar lebih stabil

import yfinance as yf
import pandas as pd
import pandas_ta as ta
import requests
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# ========== GANTI DENGAN DATA ASLI KAMU ==========
TOKEN = "8777887691:AAHOTjVBkeiCMeHd4xOJkOHcX4dali-8hdE"
CHAT_ID = "8467853860"
# =================================================

LIST_SAHAM = [
    'BUMI.JK', 'ELSA.JK', 'ENRG.JK', 'MEDC.JK', 'PGUN.JK', 'BREN.JK',
    'ANTM.JK', 'AMMN.JK', 'CUAN.JK', 'BNII.JK',
    'ASRI.JK', 'BIPI.JK', 'SMRA.JK', 'PWON.JK', 'BSDE.JK', 'WIKA.JK', 'JSMR.JK',
    'FREN.JK', 'MORA.JK', 'MTEL.JK', 'BUKA.JK',
    'FILM.JK', 'MCOL.JK', 'RANS.JK', 'MYRX.JK'
]

def kirim_pesan(pesan):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        resp = requests.get(url, params={
            'chat_id': CHAT_ID, 
            'text': pesan, 
            'parse_mode': 'HTML'
        }, timeout=10)
        if resp.status_code == 200:
            print("✅ Pesan terkirim!")
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
            return "📰 Netral", 0, 0
        text = resp.text.lower()
        rumor = ['akuisisi','ekspansi','target','rekomendasi','naik','potensi','kerjasama','dividen','buyback','melesat']
        news = ['turun','anjlok','koreksi','jual','bearish','negatif','gagal','rugi','utang','krisis','skandal']
        rumor_count = sum(1 for kw in rumor if kw in text)
        news_count = sum(1 for kw in news if kw in text)
        if rumor_count > news_count and rumor_count >= 2:
            return "📰 Buy on RUMOR", rumor_count, news_count
        elif news_count > rumor_count and news_count >= 2:
            return "📰 Sell on NEWS", rumor_count, news_count
        else:
            return "📰 Netral", rumor_count, news_count
    except:
        return "📰 Netral", 0, 0

def analisis_scalping(kode):
    try:
        saham = yf.Ticker(kode)
        # Ambil data 90 hari untuk stabilitas
        df = saham.history(period="90d")
        if df.empty or len(df) < 20:
            return None
        
        info = saham.info
        last = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Jika data hari ini kosong (0 volume), pakai data kemarin
        if last['Volume'] == 0 or pd.isna(last['Close']):
            # Ambil data yang valid (hari kerja sebelumnya)
            df_valid = df[df['Volume'] > 0]
            if len(df_valid) < 2:
                return None
            last = df_valid.iloc[-1]
            prev = df_valid.iloc[-2]
        
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['MA20'] = ta.sma(df['Close'], length=20)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        
        last_rsi = df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else 50
        harga = last['Close']
        atr = df['ATR'].iloc[-1] if not pd.isna(df['ATR'].iloc[-1]) else 1
        perubahan = ((harga - prev['Close']) / prev['Close']) * 100 if prev['Close'] > 0 else 0
        
        vol_hari = last['Volume']
        vol_kemarin = prev['Volume'] if prev['Volume'] > 0 else vol_hari
        avg_vol_5 = df['Volume'].rolling(5).mean().iloc[-1]
        avg_vol_5 = avg_vol_5 if avg_vol_5 > 0 else 1
        
        vs_kemarin = vol_hari / vol_kemarin if vol_kemarin > 0 else 1
        vs_minggu = vol_hari / avg_vol_5 if avg_vol_5 > 0 else 1
        
        bandar_score = 0
        bandar_label = "⚪ Tidak terdeteksi"
        if vs_minggu > 2.0:
            bandar_score += 3
            bandar_label = "🔴 Akumulasi Bandar (Volume Melonjak)"
        if vs_minggu > 1.5 and harga > df['MA20'].iloc[-1]:
            bandar_score += 2
            bandar_label += " & Proteksi MA20"
        if vs_minggu > 1.8 and 0 < perubahan < 2:
            bandar_score += 1
            bandar_label += " (Distribusi)"
        
        if bandar_score >= 5: bandar_status = "🔥 BANDAR TERDETEKSI"
        elif bandar_score >= 3: bandar_status = "⚠️ Potensi Bandar"
        else: bandar_status = "✅ Normal"
        
        nama = info.get('shortName', kode)
        sentimen_label, _, _ = get_news_sentiment(kode, nama)
        
        skor_akhir = bandar_score
        if last_rsi > 70: skor_akhir += 1
        if abs(perubahan) > 5: skor_akhir += 1
        if vs_minggu > 3.0: skor_akhir += 1
        
        if skor_akhir >= 6:
            status = "🔴 INDIKASI GORENGAN TINGGI"
            rekom = "HINDARI! Resiko besar."
        elif skor_akhir >= 4:
            status = "🟡 POTENSI SCALPING"
            rekom = "Cocok scalping di support. Pasang SL!"
        else:
            status = "🟢 Normal / Likuid"
            rekom = "Aman untuk trading harian."
        
        sl = round(harga - (1.8 * atr), 2) if atr else 0
        tp = round(harga + (3.0 * atr), 2) if atr else 0
        
        market_cap = info.get('marketCap', 0)
        kap_str = f"Rp{market_cap/1e12:.2f}T" if market_cap > 0 else "N/A"
        
        return {
            'kode': kode.replace('.JK', ''),
            'nama': nama[:25],
            'harga': harga,
            'perubahan': perubahan,
            'rsi': round(last_rsi, 2),
            'ma20': round(df['MA20'].iloc[-1], 2),
            'vol_hari': int(vol_hari),
            'avg_vol_5': int(avg_vol_5),
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
        print(f"Error {kode}: {e}")
        return None

# ========== MAIN ==========
waktu = datetime.now().strftime('%d-%m-%Y %H:%M')
print(f"Scan Scalping dimulai: {waktu}")

semua_hasil = []
for kode in LIST_SAHAM:
    res = analisis_scalping(kode)
    if res:
        semua_hasil.append(res)

semua_hasil.sort(key=lambda x: x['skor'], reverse=True)
berbahaya = [h for h in semua_hasil if h['skor'] >= 4]
aman = [h for h in semua_hasil if h['skor'] < 4]

pesan = f"<b>⚡ SCALPING GORENGAN</b> - {waktu} WIB\n"
pesan += f"<b>Total:</b> {len(semua_hasil)} saham | <b>Sinyal:</b> {len(berbahaya)}\n"
pesan += "================================\n"
pesan += "⏰ Scan Pagi (07:00) & Sore (15:45)\n"
pesan += "================================\n\n"

if berbahaya:
    pesan += "<b>🚨 SAHAM DENGAN POTENSI SCALPING</b>\n\n"
    for h in berbahaya[:5]:
        pesan += f"🏢 <b>{h['kode']}</b> - {h['nama']}\n"
        pesan += f"💰 Rp{h['harga']:.0f} | 📈 {h['perubahan']:+.2f}%\n"
        pesan += f"📊 RSI: {h['rsi']} | MA20: Rp{h['ma20']:.0f}\n"
        pesan += f"📦 Vol: {h['vol_hari']:,} | Vs Minggu: {h['vs_minggu']}x\n"
        pesan += f"🕵️ <b>Bandarmology:</b> {h['bandar_status']}\n"
        pesan += f"{h['sentimen_label']}\n"
        pesan += f"⚠️ <b>Status:</b> {h['status']}\n"
        pesan += f"💡 <b>Strategi:</b> {h['rekom']}\n"
        pesan += f"🔴 <b>SL:</b> Rp{h['sl']:.0f} | 🟢 <b>TP:</b> Rp{h['tp']:.0f}\n"
        pesan += f"📋 Kap: {h['kap']}\n"
        pesan += "------------------------\n"
else:
    pesan += "✅ Tidak ada saham dengan potensi scalping tinggi.\n\n"

if aman and len(aman) > 0:
    pesan += "<b>📊 PANTAUAN (Skor Tertinggi):</b>\n"
    for h in aman[:3]:
        pesan += f"🔹 {h['kode']} | Skor: {h['skor']} | RSI: {h['rsi']}\n"

kirim_pesan(pesan)
print("✅ Selesai! Cek Telegram.")
