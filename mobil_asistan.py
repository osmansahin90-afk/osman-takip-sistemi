import streamlit as st
import requests
from datetime import datetime, date

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

# --- SEKMELİ YAPI ---
tab1, tab2, tab3 = st.tabs(["📅 Günlük Takip", "➕ Öğrenci Yönetimi", "💰 Alacak Durumu"])

with tab1:
    st.subheader("Bugünkü Dersleriniz")
    secilen_tarih = st.date_input("Tarih Seçin", date.today())
    gun_adi = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][secilen_tarih.weekday()]
    t_key = secilen_tarih.strftime("%d-%m-%Y")

    if gun_adi in sabit:
        for ogrenci in sabit[gun_adi]:
            ad = ogrenci['ogrenci']
            ucret = ogrenci['ucret']
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
    st.subheader("Yeni Öğrenci Ekle")
    col_e1, col_e2, col_e3 = st.columns(3)
    yeni_gun = col_e1.selectbox("Gün", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])
    yeni_ad = col_e2.text_input("Öğrenci Adı")
    yeni_ucret = col_e3.number_input("Ücret", min_value=0, value=2000)
    
    if st.button("➕ Listeye Ekle"):
        if yeni_ad:
            if yeni_gun not in sabit: sabit[yeni_gun] = []
            sabit[yeni_gun].append({"ogrenci": yeni_ad, "ucret": yeni_ucret})
            buluta_gonder(veri)
            st.success(f"{yeni_ad} eklendi!")
            st.rerun()

    st.divider()
    st.subheader("📋 Kayıtlı Öğrencileri Sil")
    # Mevcut öğrencileri listeleyelim
    for gun, ogrenciler in sabit.items():
        if ogrenciler:
            st.write(f"**{gun}**")
            for i, ogrenci in enumerate(ogrenciler):
                col_s1, col_s2 = st.columns([4, 1])
                col_s1.write(f"👤 {ogrenci['ogrenci']} ({ogrenci['ucret']} TL)")
                if col_s2.button("🗑️ Sil", key=f"del_{gun}_{i}"):
                    sabit[gun].pop(i) # Listeden çıkar
                    buluta_gonder(veri)
                    st.warning(f"{ogrenci['ogrenci']} silindi!")
                    st.rerun()

with tab3:
    toplam = sum(d['ucret'] for t in arsiv for d in arsiv[t].values() if not d.get('odendi', False))
    st.metric("Bekleyen Toplam Alacak", f"{toplam:,.2f} TL")
    for t, ogrenciler in arsiv.items():
        for ad, detay in ogrenciler.items():
            if not detay.get('odendi', False):
                st.write(f"📅 {t} - 👤 {ad}: {detay['ucret']} TL")
