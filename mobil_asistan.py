import streamlit as st
import requests
from datetime import datetime, date

# --- AYARLAR ---
FIREBASE_URL = "https://osmansahintakip-default-rtdb.europe-west1.firebasedatabase.app/.json"

def verileri_cek():
    try:
        res = requests.get(FIREBASE_URL, timeout=15)
        return res.json() if res.status_code == 200 else {"sabit": {}, "arsiv": {}}
    except:
        return {"sabit": {}, "arsiv": {}}

def buluta_gonder(veri):
    try:
        requests.put(FIREBASE_URL, json=veri, timeout=15)
        return True
    except:
        return False

st.set_page_config(page_title="Osman Şahin Mobil", layout="wide")
st.title("📱 Osman Şahin Yönetim Paneli")

# Veriyi çek (Sadece sayfa ilk açıldığında veya manuel yenilendiğinde)
if 'veri' not in st.session_state:
    st.session_state.veri = verileri_cek()

veri = st.session_state.veri
sabit = veri.get("sabit", {})
arsiv = veri.get("arsiv", {})

tab1, tab2, tab3 = st.tabs(["📅 Günlük Takip", "➕ Öğrenci Yönetimi", "💰 Alacak Durumu"])

with tab1:
    st.subheader("Ders Takibi")
    secilen_tarih = st.date_input("Tarih Seçin", date.today())
    gun_adi = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][secilen_tarih.weekday()]
    t_key = secilen_tarih.strftime("%d-%m-%Y")

    if gun_adi in sabit:
        for i, ogrenci in enumerate(sabit[gun_adi]):
            ad, ucret = ogrenci['ogrenci'], ogrenci['ucret']
            is_checked = t_key in arsiv and ad in arsiv[t_key]
            
            # TİK ATMA (Sadece hafızada tutar, butona basınca gönderir)
            check = st.checkbox(f"✅ {ad} ({ucret} TL)", value=is_checked, key=f"c_{t_key}_{ad}_{i}")
            if check != is_checked:
                if check:
                    if t_key not in arsiv: arsiv[t_key] = {}
                    arsiv[t_key][ad] = {"ucret": ucret, "odendi": False}
                else:
                    if t_key in arsiv and ad in arsiv[t_key]:
                        del arsiv[t_key][ad]

        st.divider()
        # GÜVENLİ KAYDETME BUTONU
        if st.button("🚀 DEĞİŞİKLİKLERİ KAYDET VE GÖNDER", use_container_width=True):
            if buluta_gonder(veri):
                st.success("Veriler başarıyla buluta işlendi!")
                st.session_state.veri = veri # Hafızayı güncelle
            else:
                st.error("Bağlantı hatası! Tekrar deneyin.")
    else:
        st.info("Bu güne ait ders kaydı bulunamadı.")

with tab2:
    st.subheader("Öğrenci Ekle/Sil")
    y_ad = st.text_input("Öğrenci Adı")
    y_gun = st.selectbox("Gün", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])
    y_u = st.number_input("Ücret", value=2000)
    if st.button("➕ Yeni Öğrenciyi Sisteme Kaydet"):
        t_ad = y_ad.replace(".", "").strip()
        if y_gun not in sabit: sabit[y_gun] = []
        sabit[y_gun].append({"ogrenci": t_ad, "ucret": y_u})
        buluta_gonder(veri)
        st.rerun()

    st.divider()
    for g, ogrenciler in sabit.items():
        for i, ogr in enumerate(ogrenciler):
            c1, c2 = st.columns([4, 1])
            c1.write(f"{g}: {ogr['ogrenci']}")
            if c2.button("🗑️", key=f"d_{g}_{i}"):
                sabit[g].pop(i)
                buluta_gonder(veri)
                st.rerun()

with tab3:
    st.subheader("📊 Alacak Listesi")
    if st.button("🔄 LİSTEYİ YENİLE"):
        st.session_state.veri = verileri_cek()
        st.rerun()

    toplam = 0
    if arsiv:
        for t, ogrenciler in arsiv.items():
            for ad, detay in ogrenciler.items():
                if not detay.get('odendi', False):
                    toplam += detay['ucret']
                    col_a1, col_a2 = st.columns([3, 1])
                    col_a1.write(f"📅 {t} - {ad}: {detay['ucret']} TL")
                    if col_a2.button("💰 ÖDENDİ", key=f"pay_{t}_{ad}"):
                        arsiv[t][ad]['odendi'] = True
                        buluta_gonder(veri)
                        st.rerun()
    
    st.metric("Bekleyen Toplam Alacak", f"{toplam:,.2f} TL")
