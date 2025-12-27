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

veri = verileri_cek()
if veri is None: veri = {"sabit": {}, "arsiv": {}}
sabit = veri.get("sabit", {})
arsiv = veri.get("arsiv", {})

tab1, tab2, tab3 = st.tabs(["📅 Günlük Takip", "➕ Öğrenci Yönetimi", "💰 Alacak Durumu"])

# --- TAB 1 VE TAB 2 KODLARI AYNI KALIYOR (SİLME MANTIĞI DAHİL) ---
with tab1:
    st.subheader("Bugünkü Dersleriniz")
    secilen_tarih = st.date_input("Tarih Seçin", date.today())
    gun_adi = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][secilen_tarih.weekday()]
    t_key = secilen_tarih.strftime("%d-%m-%Y")
    if gun_adi in sabit:
        for ogrenci in sabit[gun_adi]:
            ad, ucret = ogrenci['ogrenci'], ogrenci['ucret']
            is_checked = t_key in arsiv and ad in arsiv[t_key]
            is_paid = is_checked and arsiv[t_key][ad].get('odendi', False)
            c1, c2 = st.columns([3, 1])
            with c1:
                if st.checkbox(f"✅ {ad} ({ucret} TL)", value=is_checked, key=f"c_{t_key}_{ad}"):
                    if not is_checked:
                        if t_key not in arsiv: arsiv[t_key] = {}
                        arsiv[t_key][ad] = {"ucret": ucret, "odendi": False}
                        buluta_gonder(veri); st.rerun()
                elif is_checked:
                    del arsiv[t_key][ad]; buluta_gonder(veri); st.rerun()
            with c2:
                if is_checked and not is_paid:
                    if st.button("💰 Ödeme", key=f"b_{t_key}_{ad}"):
                        arsiv[t_key][ad]['odendi'] = True
                        buluta_gonder(veri); st.rerun()
                elif is_paid: st.write("✔️ Ödendi")

with tab2:
    st.subheader("Öğrenci Yönetimi")
    c_e1, c_e2, c_e3 = st.columns(3)
    y_gun = c_e1.selectbox("Gün", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])
    y_ad = c_e2.text_input("Öğrenci Adı")
    y_u = c_e3.number_input("Ücret", min_value=0, value=2000)
    if st.button("➕ Listeye Ekle"):
        if y_ad:
            t_ad = y_ad.replace(".", "").replace("/", "-").strip()
            if y_gun not in sabit: sabit[y_gun] = []
            sabit[y_gun].append({"ogrenci": t_ad, "ucret": y_u})
            buluta_gonder(veri); st.success(f"{t_ad} eklendi!"); st.rerun()
    st.divider()
    for g in ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]:
        if g in sabit and sabit[g]:
            st.write(f"**{g}**")
            for i, ogr in enumerate(sabit[g]):
                cs1, cs2 = st.columns([4, 1])
                cs1.write(f"👤 {ogr['ogrenci']}")
                if cs2.button("🗑️ Sil", key=f"d_{g}_{i}"):
                    s_ad = ogr['ogrenci']
                    sabit[g].pop(i)
                    for trh in list(arsiv.keys()):
                        if s_ad in arsiv[trh] and not arsiv[trh][s_ad].get('odendi', False):
                            del arsiv[trh][s_ad]
                    buluta_gonder(veri); st.rerun()

# --- TAB 3: HAYALET TEMİZLEYİCİ BURADA ---
with tab3:
    st.subheader("Alacak Takibi")
    
    # Tüm kayıtlı öğrenci isimlerini bir listeye toplayalım
    aktif_ogrenciler = set()
    for gun_dersleri in sabit.values():
        for d in gun_dersleri:
            aktif_ogrenciler.add(d['ogrenci'])

    toplam_bekleyen = 0
    borclular = []
    hayalet_kayitlar = False

    if arsiv:
        for t, ogrenciler in list(arsiv.items()):
            for ad, detay in list(ogrenciler.items()):
                if not detay.get('odendi', False):
                    # Eğer öğrenci artık sabit listede yoksa bu bir "hayalet" kayıttır
                    if ad not in aktif_ogrenciler:
                        hayalet_kayitlar = True
                    
                    toplam_bekleyen += detay['ucret']
                    borclular.append(f"📅 {t} - 👤 {ad}: {detay['ucret']} TL")

    st.metric("Bekleyen Toplam Alacak", f"{toplam_bekleyen:,.2f} TL")
    
    # HAYALET TEMİZLEME BUTONU
    if hayalet_kayitlar:
        st.warning("⚠️ Listede olmayan eski öğrencilere ait borç kayıtları bulundu!")
        if st.button("🧹 Eski/Hayalet Kayıtları Tamamen Temizle"):
            for t in list(arsiv.keys()):
                for ad in list(arsiv[t].keys()):
                    if ad not in aktif_ogrenciler and not arsiv[t][ad].get('odendi', False):
                        del arsiv[t][ad]
                if not arsiv[t]: del arsiv[t]
            buluta_gonder(veri)
            st.success("Tüm eski kayıtlar süpürüldü!")
            st.rerun()

    for b in borclular:
        st.write(b)
