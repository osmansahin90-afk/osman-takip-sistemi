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
        requests.put(FIREBASE_URL, json=veri, timeout=10)
        return True
    except:
        return False

st.set_page_config(page_title="Osman Şahin Mobil", layout="wide")
st.title("📱 Matematik Öğretmeni Osman Şahin")

# Veriyi bir kez çekelim
if 'veri' not in st.session_state:
    st.session_state.veri = verileri_cek()

veri = st.session_state.veri
if veri is None: veri = {"sabit": {}, "arsiv": {}}
sabit = veri.get("sabit", {})
arsiv = veri.get("arsiv", {})

tab1, tab2, tab3 = st.tabs(["📅 Günlük Takip", "➕ Öğrenci Yönetimi", "💰 Alacak Durumu"])

with tab1:
    st.subheader("Bugünkü Dersler")
    secilen_tarih = st.date_input("Tarih", date.today())
    gun_adi = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][secilen_tarih.weekday()]
    t_key = secilen_tarih.strftime("%d-%m-%Y")

    if gun_adi in sabit:
        for ogrenci in sabit[gun_adi]:
            ad, ucret = ogrenci['ogrenci'], ogrenci['ucret']
            is_checked = t_key in arsiv and ad in arsiv[t_key]
            is_paid = is_checked and arsiv[t_key][ad].get('odendi', False)
            
            c1, c2 = st.columns([3, 1])
            with c1:
                # Tik atma işlemi
                if st.checkbox(f"✅ {ad} ({ucret} TL)", value=is_checked, key=f"c_{t_key}_{ad}"):
                    if not is_checked:
                        if t_key not in arsiv: arsiv[t_key] = {}
                        arsiv[t_key][ad] = {"ucret": ucret, "odendi": False}
                        buluta_gonder(veri)
                else:
                    if is_checked:
                        del arsiv[t_key][ad]
                        buluta_gonder(veri)
            with c2:
                if is_checked and not is_paid:
                    if st.button("💰 Öde", key=f"b_{t_key}_{ad}"):
                        arsiv[t_key][ad]['odendi'] = True
                        buluta_gonder(veri)
                        st.rerun()
                elif is_paid: st.write("✔️")
    else: st.info("Ders yok.")

with tab2:
    st.subheader("Öğrenci Yönetimi")
    with st.expander("➕ Yeni Öğrenci Ekle"):
        y_gun = st.selectbox("Gün", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])
        y_ad = st.text_input("Ad Soyad")
        y_u = st.number_input("Ücret", value=2000)
        if st.button("Kaydet"):
            if y_ad:
                t_ad = y_ad.replace(".", "").strip()
                if y_gun not in sabit: sabit[y_gun] = []
                sabit[y_gun].append({"ogrenci": t_ad, "ucret": y_u})
                buluta_gonder(veri)
                st.success("Eklendi!")
                st.rerun()

    st.divider()
    st.write("🗑️ **Öğrenci Sil**")
    for g, ogrenciler in sabit.items():
        for i, ogr in enumerate(ogrenciler):
            col_s1, col_s2 = st.columns([4, 1])
            col_s1.write(f"{g}: {ogr['ogrenci']}")
            if col_s2.button("Sil", key=f"d_{g}_{i}"):
                s_ad = ogr['ogrenci']
                sabit[g].pop(i)
                # Arşivdeki ödenmemişleri de sil
                for trh in list(arsiv.keys()):
                    if s_ad in arsiv[trh] and not arsiv[trh][s_ad].get('odendi', False):
                        del arsiv[trh][s_ad]
                buluta_gonder(veri)
                st.rerun()

with tab3:
    st.subheader("Alacak Takibi")
    # Sayfayı manuel yenilemek için buton
    if st.button("🔄 Verileri Yenile"):
        st.session_state.veri = verileri_cek()
        st.rerun()

    toplam_bekleyen = 0
    if arsiv:
        for t, ogrenciler in arsiv.items():
            for ad, detay in ogrenciler.items():
                if not detay.get('odendi', False):
                    toplam_bekleyen += detay['ucret']
                    st.write(f"📅 {t} - {ad}: {detay['ucret']} TL")
    
    st.metric("Bekleyen Toplam", f"{toplam_bekleyen:,.2f} TL")
