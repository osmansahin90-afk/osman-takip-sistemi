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
        res = requests.put(FIREBASE_URL, json=veri, timeout=15)
        return res.status_code == 200
    except:
        return False

st.set_page_config(page_title="Osman Şahin Mobil", layout="wide")
st.title("📱 Matematik Öğretmeni Osman Şahin")

# 1. VERİLERİ SADECE BİR KEZ YÜKLE
if 'ana_veri' not in st.session_state:
    st.session_state.ana_veri = verileri_cek()

# Kolay kullanım için kısa değişkenler
if st.session_state.ana_veri is None:
    st.session_state.ana_veri = {"sabit": {}, "arsiv": {}}

sabit = st.session_state.ana_veri.get("sabit", {})
arsiv = st.session_state.ana_veri.get("arsiv", {})

tab1, tab2, tab3 = st.tabs(["📅 Ders Takibi", "➕ Öğrenci Ekle/Sil", "💰 Alacak Listesi"])

with tab1:
    secilen_tarih = st.date_input("Tarih Seçin", date.today())
    gun_adi = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][secilen_tarih.weekday()]
    t_key = secilen_tarih.strftime("%d-%m-%Y")

    if gun_adi in sabit:
        st.write(f"### {gun_adi} Dersleri")
        for i, ogrenci in enumerate(sabit[gun_adi]):
            ad, ucret = ogrenci['ogrenci'], ogrenci['ucret']
            is_checked = t_key in arsiv and ad in arsiv[t_key]
            
            # Değişiklikleri sadece yerel hafızada yapıyoruz
            check = st.checkbox(f"✅ {ad} ({ucret} TL)", value=is_checked, key=f"c_{t_key}_{ad}_{i}")
            if check != is_checked:
                if check:
                    if t_key not in arsiv: arsiv[t_key] = {}
                    arsiv[t_key][ad] = {"ucret": ucret, "odendi": False}
                else:
                    if t_key in arsiv and ad in arsiv[t_key]:
                        del arsiv[t_key][ad]
                # Sayfayı hemen yenilemeyelim, döngüyü kıralım. 
                # Sadece yerel veriyi güncelledik.

        st.divider()
        if st.button("💾 TÜM DEĞİŞİKLİKLERİ BULUTA KAYDET", use_container_width=True, type="primary"):
            with st.spinner("Buluta gönderiliyor..."):
                if buluta_gonder(st.session_state.ana_veri):
                    st.success("Başarıyla kaydedildi!")
                else:
                    st.error("Kayıt sırasında hata oluştu. İnterneti kontrol edin.")
    else:
        st.info("Bu gün ders yok.")

with tab2:
    st.subheader("Öğrenci Yönetimi")
    with st.expander("Yeni Öğrenci Ekle"):
        y_ad = st.text_input("Ad Soyad")
        y_gun = st.selectbox("Gün", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])
        y_u = st.number_input("Ücret", value=2000)
        if st.button("Sisteme Ekle"):
            t_ad = y_ad.replace(".", "").strip()
            if y_gun not in sabit: sabit[y_gun] = []
            sabit[y_gun].append({"ogrenci": t_ad, "ucret": y_u})
            buluta_gonder(st.session_state.ana_veri)
            st.rerun()

    st.divider()
    for g, ogrenciler in list(sabit.items()):
        for i, ogr in enumerate(ogrenciler):
            c1, c2 = st.columns([4, 1])
            c1.write(f"{g}: {ogr['ogrenci']}")
            if c2.button("🗑️", key=f"del_{g}_{i}"):
                sabit[g].pop(i)
                buluta_gonder(st.session_state.ana_veri)
                st.rerun()

with tab3:
    st.subheader("📊 Alacak Takibi")
    if st.button("🔄 LİSTEYİ TAZELE"):
        st.session_state.ana_veri = verileri_cek()
        st.rerun()

    toplam = 0
    if arsiv:
        for t in list(arsiv.keys()):
            for ad in list(arsiv[t].keys()):
                detay = arsiv[t][ad]
                if not detay.get('odendi', False):
                    toplam += detay['ucret']
                    c_a1, c_a2 = st.columns([3, 1])
                    c_a1.write(f"📅 {t} - {ad}: {detay['ucret']} TL")
                    if c_a2.button("💰 ÖDE", key=f"pay_{t}_{ad}"):
                        arsiv[t][ad]['odendi'] = True
                        buluta_gonder(st.session_state.ana_veri)
                        st.rerun()
    
    st.metric("Bekleyen Toplam", f"{toplam:,.2f} TL")
