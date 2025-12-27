import streamlit as st
import requests
from datetime import datetime, date

# --- AYARLAR ---
FIREBASE_URL = "https://osmansahintakip-default-rtdb.europe-west1.firebasedatabase.app/.json"

def verileri_cek():
    res = requests.get(FIREBASE_URL, timeout=10)
    return res.json() if res.status_code == 200 else {"sabit": {}, "arsiv": {}}

def buluta_gonder(veri):
    requests.put(FIREBASE_URL, json=veri, timeout=10)

st.set_page_config(page_title="Osman Şahin Mobil", layout="wide")
st.title("📱 Matematik Öğretmeni Osman Şahin")

# VERİYİ HER SEFERİNDE TAZE ÇEKELİM (Hafıza kaybını önlemek için st.session_state kullanmıyoruz)
veri = verileri_cek()
if not veri: veri = {"sabit": {}, "arsiv": {}}
sabit = veri.get("sabit", {})
arsiv = veri.get("arsiv", {})

tab1, tab2, tab3 = st.tabs(["📅 Günlük Takip", "➕ Öğrenci Yönetimi", "💰 Alacak Durumu"])

with tab1:
    st.subheader("Bugünkü Dersler")
    # Tarih seçimi değiştikçe sayfa yenilenir ama veriyi yukarıda taze çektiğimiz için silinmez
    secilen_tarih = st.date_input("Takvimden Gün Seçin", date.today())
    gun_adi = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][secilen_tarih.weekday()]
    t_key = secilen_tarih.strftime("%d-%m-%Y")

    if gun_adi in sabit:
        for i, ogrenci in enumerate(sabit[gun_adi]):
            ad, ucret = ogrenci['ogrenci'], ogrenci['ucret']
            
            # Arşivde var mı kontrolü
            is_checked = t_key in arsiv and ad in arsiv[t_key]
            is_paid = is_checked and arsiv[t_key][ad].get('odendi', False)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                # ANAHTAR NOKTA: Her checkbox'ın kendine özel ve tarihe bağlı bir anahtarı (key) var
                check = st.checkbox(f"✅ {ad} ({ucret} TL)", value=is_checked, key=f"chk_{t_key}_{ad}_{i}")
                
                # Eğer kullanıcı kutuya dokunursa:
                if check != is_checked:
                    if check:
                        if t_key not in arsiv: arsiv[t_key] = {}
                        arsiv[t_key][ad] = {"ucret": ucret, "odendi": False}
                    else:
                        if t_key in arsiv and ad in arsiv[t_key]:
                            del arsiv[t_key][ad]
                    
                    buluta_gonder(veri)
                    st.rerun() # Değişikliği anında kaydet ve sayfayı tazele
            
            with col2:
                if is_checked and not is_paid:
                    if st.button("💰 Öde", key=f"btn_{t_key}_{ad}_{i}"):
                        arsiv[t_key][ad]['odendi'] = True
                        buluta_gonder(veri)
                        st.rerun()
                elif is_paid:
                    st.write("✔️")
    else:
        st.info("Bu gün için ders programı boş.")

with tab2:
    st.subheader("Öğrenci Yönetimi")
    # Yeni Ekleme
    y_ad = st.text_input("Öğrenci Ad Soyad")
    y_gun = st.selectbox("Ders Günü", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])
    y_u = st.number_input("Ders Ücreti", value=2000)
    if st.button("Sisteme Ekle"):
        if y_ad:
            t_ad = y_ad.replace(".", "").strip()
            if y_gun not in sabit: sabit[y_gun] = []
            sabit[y_gun].append({"ogrenci": t_ad, "ucret": y_u})
            buluta_gonder(veri)
            st.success(f"{t_ad} başarıyla eklendi.")
            st.rerun()

    st.divider()
    st.write("🗑️ **Kayıtlı Öğrencileri Sil**")
    for g, ogrenciler in sabit.items():
        for i, ogr in enumerate(ogrenciler):
            c_s1, c_s2 = st.columns([4, 1])
            c_s1.write(f"{g}: {ogr['ogrenci']}")
            if c_s2.button("Sil", key=f"del_{g}_{i}"):
                s_ad = ogr['ogrenci']
                sabit[g].pop(i)
                # Arşiv temizliği
                for trh in list(arsiv.keys()):
                    if s_ad in arsiv[trh] and not arsiv[trh][s_ad].get('odendi', False):
                        del arsiv[trh][s_ad]
                buluta_gonder(veri)
                st.rerun()

with tab3:
    st.subheader("📊 Toplam Alacak")
    toplam = 0
    if arsiv:
        for t, ogrenciler in arsiv.items():
            for ad, detay in ogrenciler.items():
                if not detay.get('odendi', False):
                    toplam += detay['ucret']
                    st.write(f"📅 {t} - {ad}: {detay['ucret']} TL")
    
    st.metric("Bekleyen Bakiyeniz", f"{toplam:,.2f} TL")
