import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Osman Şahin Mobil Panel", layout="wide")

# --- FİREBASE BAĞLANTISI ---
FIREBASE_URL = "https://osmansahintakip-default-rtdb.europe-west1.firebasedatabase.app/.json"

st.title("📊 Osman Şahin - Mobil Takip Paneli")

# --- VERİ ÇEKME ---
try:
    response = requests.get(FIREBASE_URL, timeout=10)
    data = response.json()
    
    # Hatanın Çözümü: Değişkenleri en başta garantiye alıyoruz
    if data and isinstance(data, dict):
        sabit = data.get("sabit", {})
        arsiv = data.get("arsiv", {})
    else:
        st.warning("Veritabanı şu an boş veya veriler henüz işlenmemiş.")
        st.stop()
except Exception as e:
    st.error(f"Bağlantı Hatası: {e}")
    st.stop()

import streamlit as st
import requests
from datetime import datetime

# Firebase Ayarları
FIREBASE_URL = "https://osmansahintakip-default-rtdb.europe-west1.firebasedatabase.app/.json"

def verileri_cek():
    try:
        cevap = requests.get(FIREBASE_URL)
        return cevap.json()
    except:
        return None

veri = verileri_cek()

if veri:
    sabit = veri.get("sabit", {})
    arsiv = veri.get("arsiv", {})

    toplam_alacak = 0
    
    # Bugünün ay ve yılını alalım (Örn: "12/2025")
    su_an = datetime.now()
    bu_ay_yil = su_an.strftime("/%m/%Y") # Bilgisayardaki formatla uyumlu hale getirdik

    for tarih, ogrenciler in arsiv.items():
        # Eğer tarih bu ay ve yıla aitse (Örn: 27/12/2025 içinde /12/2025 var mı?)
        if bu_ay_yil in tarih:
            for ad, detay in ogrenciler.items():
                if not detay.get('odendi', False):
                    toplam_alacak += detay.get('ucret', 0)

    st.metric("Beklenen Alacak (Bu Ay)", f"{toplam_alacak:,.2f} TL")
    
    # Detaylı Liste
    if toplam_alacak > 0:
        st.subheader("Ödeme Bekleyenler")
        for tarih, ogrenciler in arsiv.items():
            if bu_ay_yil in tarih:
                for ad, detay in ogrenciler.items():
                    if not detay.get('odendi', False):
                        st.write(f"📅 {tarih} - 👤 {ad}: {detay.get('ucret')} TL")

# --- GÖRSELLEŞTİRME ---
col1, col2 = st.columns([1, 1])

with col1:
    st.metric(label="💰 Bu Ay Bekleyen Toplam Alacak", value=f"{toplam_alacak:,.2f} TL")
    
    if veli_bazli_alacak:
        df = pd.DataFrame(list(veli_bazli_alacak.items()), columns=['Öğrenci', 'Tutar'])
        fig = px.pie(df, values='Tutar', names='Öğrenci', title='Alacak Dağılımı')
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Bu ay için ödenmemiş ders verisi bulunamadı.")

with col2:
    st.subheader("📅 Haftalık Ders Programınız")
    gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    
    secili_gun = st.selectbox("Gün Seçin", gunler)
    # Burada 'sabit' ismini kullandık, hata artık oluşmayacak
    gunluk_dersler = sabit.get(secili_gun, [])
    
    if gunluk_dersler:
        for d in gunluk_dersler:
            st.info(f"👤 {d['ogrenci']} - 💵 {d['ucret']} TL")
    else:
        st.write("Bu gün için kayıtlı ders yok.")

# --- LİSTE ---
st.divider()
if veli_bazli_alacak:
    st.subheader("📝 Bekleyen Ödemeler")

    st.table(pd.DataFrame(list(veli_bazli_alacak.items()), columns=['Öğrenci Adı', 'Kalan Tutar (TL)']))


