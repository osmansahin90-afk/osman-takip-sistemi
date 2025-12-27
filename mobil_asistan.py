import streamlit as st
import requests
from datetime import datetime, date
import calendar

# --- AYARLAR ---
FIREBASE_URL = "https://osmansahintakip-default-rtdb.europe-west1.firebasedatabase.app/.json"

def verileri_cek():
    res = requests.get(FIREBASE_URL)
    return res.json() if res.status_code == 200 else {"sabit": {}, "arsiv": {}}

def buluta_gonder(veri):
    requests.put(FIREBASE_URL, json=veri)

st.set_page_config(page_title="Osman Şahin Mobil Panel", layout="wide")
st.title("📱 Matematik Öğretmeni Osman Şahin")

# Verileri Yükle
veri = verileri_cek()
sabit = veri.get("sabit", {})
arsiv = veri.get("arsiv", {})

# --- 1. SEKMELİ YAPI ---
tab1, tab2, tab3 = st.tabs(["📅 Günlük Takip", "➕ Öğrenci Ekle", "💰 Alacak Durumu"])

with tab1:
    st.subheader("Bugünkü Dersleriniz")
    secilen_tarih = st.date_input("Tarih Seçin", date.today())
    gun_adi = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][secilen_tarih.weekday()]
    t_key = secilen_tarih.strftime("%d-%m-%Y")

    if gun_adi in sabit:
        for ogrenci in sabit[gun_adi]:
            ad = ogrenci['ogrenci']
            ucret = ogrenci['ucret']
            
            # Arşiv kontrolü
            is_checked = t_key in arsiv and ad in arsiv[t_key]
            is_paid = is_checked and arsiv[t_key][ad].get('odendi', False)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                # DERS TİKİ
                if st.checkbox(f"✅ {ad} ({ucret} TL)", value=is_checked, key=f"cb_{t_key}_{ad}"):
                    if not is_checked:
                        if t_key not in arsiv: arsiv[t_key] = {}
                        arsiv[t_key][ad] = {"ucret": ucret, "odendi": False}
                        buluta_gonder(veri)
                        st.rerun()
                else:
                    if is_checked:
                        del arsiv[t_key][ad]
                        buluta_gonder(veri)
                        st.rerun()
            
            with col2:
                # ÖDEME ALMA
                if is_checked and not is_paid:
                    if st.button("💰 Ödeme", key=f"btn_{t_key}_{ad}"):
                        arsiv[t_key][ad]['odendi'] = True
                        buluta_gonder(veri)
                        st.rerun()
                elif is_paid:
                    st.write("✔️ Ödendi")
    else:
        st.info(f"{gun_adi} günü için kayıtlı ders yok.")

with tab2:
    st.subheader("Yeni Öğrenci/Ders Ekle")
    yeni_gun = st.selectbox("Gün", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])
    yeni_ad = st.text_input("Öğrenci Adı")
    yeni_ucret = st.number_input("Ders Ücreti", min_value=0, value=2000)
    
    if st.button("Sisteme Kaydet"):
        if yeni_ad:
            if yeni_gun not in sabit: sabit[yeni_gun] = []
            sabit[yeni_gun].append({"ogrenci": yeni_ad, "ucret": yeni_ucret})
            buluta_gonder(veri)
            st.success(f"{yeni_ad} başarıyla eklendi!")
            st.rerun()

with tab3:
    # Toplam Alacak Hesaplama
    toplam = sum(d['ucret'] for t in arsiv for d in arsiv[t].values() if not d.get('odendi', False))
    st.metric("Bekleyen Toplam Alacak", f"{toplam:,.2f} TL")
    
    # Detaylı Liste
    for t, ogrenciler in arsiv.items():
        for ad, detay in ogrenciler.items():
            if not detay.get('odendi', False):
                st.write(f"📅 {t} - 👤 {ad}: {detay['ucret']} TL")
