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

# --- ANALİZ VE HESAPLAMALAR (GÜNCEL) ---
toplam_alacak = 0
veli_bazli_alacak = {}

# Bugünün ay ve yılını al (Örn: "12/2025")
su_an = datetime.now()
hedef_donem = su_an.strftime("/%m/%Y") # Eğik çizgi ile arama yapar

for tarih, dersler in arsiv.items():
    # Eğer kayıtlı tarih bugün içinde bulunduğumuz ay/yıla aitse
    if hedef_donem in tarih:
        if isinstance(dersler, dict):
            for ogrenci, detay in dersler.items():
                if not detay.get('odendi', False):
                    ucret = detay.get('ucret', 0)
                    toplam_alacak += ucret
                    veli_bazli_alacak[ogrenci] = veli_bazli_alacak.get(ogrenci, 0) + ucret

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

