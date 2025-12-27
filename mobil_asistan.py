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
st.title("📱 Matematik Öğretmeni Osman Şahin")

# Veriyi bir kez çek ve session_state'e kilitle
if 'ana_veri' not in st.session_state:
    st.session_state.ana_veri = verileri_cek()

# Kısa yollar
v = st.session_state.ana_veri
if not v: v = {"sabit": {}, "arsiv": {}}
sabit = v.get("sabit", {})
arsiv = v.get("arsiv", {})

t1, t2, t3 = st.tabs(["📅 Ders Takibi", "➕ Öğrenci Yönetimi", "💰 Alacak Durumu"])

with t1:
    st.info("İstediğiniz tarihlere tik atın ve en alttaki KAYDET butonuna basın.")
    sec_tarih = st.date_input("Takvim", date.today())
    gun_adi = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][sec_tarih.weekday()]
    t_key = sec_tarih.strftime("%d-%m-%Y")

    if gun_adi in sabit:
        st.write(f"### {gun_adi} Programı")
        for i, ogr in enumerate(sabit[gun_adi]):
            ad = ogr['ogrenci']
            ucret = ogr['ucret']
            
            # Bu tarihte bu öğrenci önceden işaretlenmiş mi?
            is_checked = t_key in arsiv and ad in arsiv[t_key]
            
            # KRİTİK DÜZELTME: key kısmına t_key ekleyerek tarihi sabitledik
            check_key = f"cb_{t_key}_{ad}_{i}"
            
            val = st.checkbox(f"{ad} ({ucret} TL)", value=is_checked, key=check_key)
            
            # Değişikliği anında yerel hafızaya (session_state) yaz
            if val != is_checked:
                if val:
                    if t_key not in arsiv: arsiv[t_key] = {}
                    arsiv[t_key][ad] = {"ucret": ucret, "odendi": False}
                else:
                    if t_key in arsiv and ad in arsiv[t_key]:
                        del arsiv[t_key][ad]
        
        st.divider()
        if st.button("💾 TÜM GÜNLERİ VE TİKLERİ KAYDET", type="primary", use_container_width=True):
            if buluta_gonder(st.session_state.ana_veri):
                st.success("Tüm seçimleriniz başarıyla buluta gönderildi!")
            else:
                st.error("Kayıt başarısız! İnterneti kontrol edin.")
    else:
        st.write("Bu güne ait ders tanımlanmamış.")

with t2:
    st.subheader("Öğrenci Ekle / Sil")
    y_ad = st.text_input("Öğrenci Adı")
    y_gun = st.selectbox("Gün", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])
    y_u = st.number_input("Ücret", value=2000)
    if st.button("Sisteme Kaydet"):
        if y_ad:
            t_ad = y_ad.replace(".", "").strip()
            if y_gun not in sabit: sabit[y_gun] = []
            sabit[y_gun].append({"ogrenci": t_ad, "ucret": y_u})
            if buluta_gonder(st.session_state.ana_veri):
                st.success("Yeni öğrenci eklendi.")
                st.rerun()

with t3:
    st.subheader("Alacak Listesi")
    if st.button("🔄 Verileri Yenile"):
        st.session_state.ana_veri = verileri_cek()
        st.rerun()
    
    toplam = 0
    if arsiv:
        for t in list(arsiv.keys()):
            for ad in list(arsiv[t].keys()):
                if not arsiv[t][ad].get('odendi', False):
                    toplam += arsiv[t][ad]['ucret']
                    c1, c2 = st.columns([3, 1])
                    c1.write(f"📅 {t} - {ad}")
                    if c2.button("💰 Öde", key=f"p_{t}_{ad}"):
                        arsiv[t][ad]['odendi'] = True
                        buluta_gonder(st.session_state.ana_veri)
                        st.rerun()
    st.metric("Bekleyen Toplam", f"{toplam:,.2f} TL")
