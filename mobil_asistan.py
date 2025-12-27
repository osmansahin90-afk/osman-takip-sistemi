import streamlit as st
import requests
from datetime import datetime, date

# --- AYARLAR ---
FIREBASE_URL = "https://osmansahintakip-default-rtdb.europe-west1.firebasedatabase.app/.json"

def verileri_cek():
    try:
        res = requests.get(FIREBASE_URL, timeout=10)
        return res.json() if res.status_code == 200 else {"sabit": {}, "arsiv": {}}
    except:
        return {"sabit": {}, "arsiv": {}}

def buluta_gonder(veri):
    try:
        requests.put(FIREBASE_URL, json=veri, timeout=15)
        return True
    except:
        return False

st.set_page_config(page_title="Osman Şahin Panel", layout="wide")
st.title("📱 Yönetim Paneli")

# Veriyi Başlat
if 'v' not in st.session_state:
    st.session_state.v = verileri_cek()

v = st.session_state.v
if not v: v = {"sabit": {}, "arsiv": {}}
sabit = v.get("sabit", {})
arsiv = v.get("arsiv", {})

# SEKMELER
t1, t2, t3 = st.tabs(["📅 Takip", "➕ Ekle/Sil", "💰 Alacak"])

with t1:
    st.info("Tikleri atın ve en alttaki KAYDET butonuna basın.")
    secilen_tarih = st.date_input("Tarih", date.today())
    gun_adi = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][secilen_tarih.weekday()]
    t_key = secilen_tarih.strftime("%d-%m-%Y")

    if gun_adi in sabit:
        for i, ogrenci in enumerate(sabit[gun_adi]):
            ad, ucret = ogrenci['ogrenci'], ogrenci['ucret']
            is_checked = t_key in arsiv and ad in arsiv[t_key]
            
            # Seçim kutusu
            val = st.checkbox(f"{ad} ({ucret} TL)", value=is_checked, key=f"c_{t_key}_{i}")
            
            # Değişikliği anında hafızaya işle
            if val != is_checked:
                if val:
                    if t_key not in arsiv: arsiv[t_key] = {}
                    arsiv[t_key][ad] = {"ucret": ucret, "odendi": False}
                else:
                    if t_key in arsiv and ad in arsiv[t_key]:
                        del arsiv[t_key][ad]
        
        st.divider()
        # KAYDET BUTONU (Bu sefer t1 içinde en altta)
        if st.button("💾 DEĞİŞİKLİKLERİ BULUTA YAZ", type="primary"):
            if buluta_gonder(st.session_state.v):
                st.success("Kaydedildi!")
            else:
                st.error("Hata!")
    else:
        st.write("Ders yok.")

with t2:
    st.subheader("Öğrenci Yönetimi")
    y_ad = st.text_input("Ad")
    y_gun = st.selectbox("Gün", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])
    y_u = st.number_input("Ücret", value=2000)
    if st.button("Ekle"):
        t_ad = y_ad.replace(".", "").strip()
        if y_gun not in sabit: sabit[y_gun] = []
        sabit[y_gun].append({"ogrenci": t_ad, "ucret": y_u})
        buluta_gonder(st.session_state.v)
        st.rerun()

with t3:
    st.subheader("Alacaklar")
    if st.button("🔄 Yenile"):
        st.session_state.v = verileri_cek()
        st.rerun()
    
    toplam = 0
    if arsiv:
        for t in list(arsiv.keys()):
            for ad in list(arsiv[t].keys()):
                if not arsiv[t][ad].get('odendi', False):
                    toplam += arsiv[t][ad]['ucret']
                    st.write(f"{t} - {ad}")
                    if st.button(f"Öde {ad}", key=f"p_{t}_{ad}"):
                        arsiv[t][ad]['odendi'] = True
                        buluta_gonder(st.session_state.v)
                        st.rerun()
    st.metric("Toplam", f"{toplam} TL")
