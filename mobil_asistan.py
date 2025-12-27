import streamlit as st
import requests
from datetime import datetime, date

# --- AYARLAR ---
FIREBASE_URL = "https://osmansahintakip-default-rtdb.europe-west1.firebasedatabase.app/.json"

def verileri_cek():
    try:
        res = requests.get(FIREBASE_URL)
        return res.json() if res.status_code == 200 else {"sabit": {}, "arsiv": {}}
    except:
        return {"sabit": {}, "arsiv": {}}

def buluta_gonder(veri):
    requests.put(FIREBASE_URL, json=veri)

st.set_page_config(page_title="Osman Şahin Mobil Panel", layout="wide")
st.title("📱 Matematik Öğretmeni Osman Şahin")

# Verileri Yükle
veri = verileri_cek()
if veri is None: veri = {"sabit": {}, "arsiv": {}}
sabit = veri.get("sabit", {})
arsiv = veri.get("arsiv", {})

# --- SEKMELİ YAPI ---
tab1, tab2, tab3 = st.tabs(["📅 Günlük Takip", "➕ Öğrenci Yönetimi", "💰 Alacak Durumu"])

with tab1:
    st.subheader("Bugünkü Dersleriniz")
    secilen_tarih = st.date_input("Tarih Seçin", date.today())
    gun_adi = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][secilen_tarih.weekday()]
    # Firebase uyumlu tireli tarih formatı
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
                check_status = st.checkbox(f"✅ {ad} ({ucret} TL)", value=is_checked, key=f"cb_{t_key}_{ad}")
                if check_status != is_checked:
                    if check_status:
                        if t_key not in arsiv: arsiv[t_key] = {}
                        arsiv[t_key][ad] = {"ucret": ucret, "odendi": False}
                    else:
                        if t_key in arsiv and ad in arsiv[t_key]:
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
    st.subheader("Yeni Öğrenci Ekle")
    col_e1, col_e2, col_e3 = st.columns(3)
    yeni_gun = col_e1.selectbox("Gün", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])
    yeni_ad = col_e2.text_input("Öğrenci Adı")
    yeni_ucret = col_e3.number_input("Ücret", min_value=0, value=2000)
    
    if st.button("➕ Listeye Ekle"):
        if yeni_ad:
            # Karakter temizliği (Nokta ve Slash istemiyoruz)
            temiz_ad = yeni_ad.replace(".", "").replace("/", "-").strip()
            if yeni_gun not in sabit: sabit[yeni_gun] = []
            sabit[yeni_gun].append({"ogrenci": temiz_ad, "ucret": yeni_ucret})
            buluta_gonder(veri)
            st.success(f"{temiz_ad} eklendi!")
            st.rerun()

    st.divider()
    st.subheader("📋 Kayıtlı Öğrencileri Sil")
    for gun in ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]:
        if gun in sabit and sabit[gun]:
            st.write(f"**{gun}**")
            for i, ogrenci in enumerate(sabit[gun]):
                col_s1, col_s2 = st.columns([4, 1])
                ogrenci_adi = ogrenci['ogrenci']
                col_s1.write(f"👤 {ogrenci_adi} ({ogrenci['ucret']} TL)")
                
                if col_s2.button("🗑️ Sil", key=f"del_{gun}_{ogrenci_adi}_{i}"):
                    # 1. Sabit listeden çıkar
                    sabit[gun].pop(i)
                    
                    # 2. Arşivdeki bu öğrenciye ait TÜM ödenmemiş dersleri temizle
                    for tarih in list(arsiv.keys()):
                        if ogrenci_adi in arsiv[tarih]:
                            if not arsiv[tarih][ogrenci_adi].get('odendi', False):
                                del arsiv[tarih][ogrenci_adi]
                        if not arsiv[tarih]: # Tarih boş kaldıysa temizle
                            del arsiv[tarih]
                    
                    buluta_gonder(veri)
                    st.warning(f"{ogrenci_adi} ve bekleyen borçları silindi!")
                    st.rerun()

with tab3:
    # Gerçek zamanlı alacak hesaplama
    toplam_bekleyen = 0
    borclular = []
    
    if arsiv:
        for t, ogrenciler in arsiv.items():
            for ad, detay in ogrenciler.items():
                if not detay.get('odendi', False):
                    toplam_bekleyen += detay['ucret']
                    borclular.append(f"📅 {t} - 👤 {ad}: {detay['ucret']} TL")
    
    st.metric("Bekleyen Toplam Alacak", f"{toplam_bekleyen:,.2f} TL")
    
    if borclular:
        for b in borclular:
            st.write(b)
    else:
        st.write("🎉 Borcu olan ders bulunamadı.")
