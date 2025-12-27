import streamlit as st
import requests
from datetime import datetime, date

# --- AYARLAR ---
FIREBASE_URL = "https://osmansahintakip-default-rtdb.europe-west1.firebasedatabase.app/"

def verileri_cek():
    try:
        res = requests.get(f"{FIREBASE_URL}.json", timeout=10)
        return res.json() if res.status_code == 200 else {"sabit": {}, "arsiv": {}}
    except:
        return {"sabit": {}, "arsiv": {}}

# Tekil veri güncelleme (Döngüye girmemesi için en hızlı yöntem)
def arsiv_guncelle(tarih, ogrenci_ad, veri_obj):
    path = f"{FIREBASE_URL}arsiv/{tarih}/{ogrenci_ad}.json"
    requests.put(path, json=veri_obj)

def arsiv_sil(tarih, ogrenci_ad):
    path = f"{FIREBASE_URL}arsiv/{tarih}/{ogrenci_ad}.json"
    requests.delete(path)

st.set_page_config(page_title="Osman Şahin Panel", layout="wide")
st.title("📱 Matematik Öğretmeni Osman Şahin")

# Veriyi çek
veri = verileri_cek()
if not veri: veri = {"sabit": {}, "arsiv": {}}
sabit = veri.get("sabit", {})
arsiv = veri.get("arsiv", {})

t1, t2, t3 = st.tabs(["📅 Ders Takibi", "➕ Öğrenci Yönetimi", "💰 Alacak Listesi"])

with t1:
    sec_tarih = st.date_input("Takvim", date.today())
    gun_adi = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"][sec_tarih.weekday()]
    t_key = sec_tarih.strftime("%d-%m-%Y")

    if gun_adi in sabit:
        st.write(f"### {gun_adi} Programı")
        for i, ogr in enumerate(sabit[gun_adi]):
            ad = ogr['ogrenci']
            ucret = ogr['ucret']
            
            # Bulut kontrolü
            is_checked = t_key in arsiv and ad in arsiv[t_key]
            
            # TİKE BASTIĞI AN KAYDEDEN MEKANİZMA
            check = st.checkbox(f"{ad} ({ucret} TL)", value=is_checked, key=f"v2_{t_key}_{ad}")
            
            if check != is_checked:
                if check:
                    # Anında Firebase'e yaz
                    arsiv_guncelle(t_key, ad, {"ucret": ucret, "odendi": False})
                else:
                    # Anında Firebase'den sil
                    arsiv_sil(t_key, ad)
                st.rerun() # Sadece bir kez yenile ki görsel güncellensin
    else:
        st.info("Bugün ders yok.")

with t2:
    st.subheader("Öğrenci Ekle / Sil")
    y_ad = st.text_input("Öğrenci Adı")
    y_gun = st.selectbox("Gün", ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"])
    y_u = st.number_input("Ücret", value=2000)
    if st.button("Sisteme Ekle"):
        t_ad = y_ad.replace(".", "").strip()
        if y_gun not in sabit: sabit[y_gun] = []
        sabit[y_gun].append({"ogrenci": t_ad, "ucret": y_u})
        requests.put(f"{FIREBASE_URL}sabit.json", json=sabit)
        st.success("Eklendi!")
        st.rerun()

    st.divider()
    for g, ogrenciler in list(sabit.items()):
        for i, ogr in enumerate(ogrenciler):
            c1, c2 = st.columns([4, 1])
            c1.write(f"{g}: {ogr['ogrenci']}")
            if c2.button("🗑️", key=f"del_{g}_{i}"):
                sabit[g].pop(i)
                requests.put(f"{FIREBASE_URL}sabit.json", json=sabit)
                st.rerun()

with t3:
    st.subheader("📊 Alacak Listesi")
    toplam = 0
    if arsiv:
        for t in list(arsiv.keys()):
            for ad in list(arsiv[t].keys()):
                detay = arsiv[t][ad]
                if not detay.get('odendi', False):
                    toplam += detay['ucret']
                    c_a1, c_a2 = st.columns([3, 1])
                    c_a1.write(f"📅 {t} - {ad}")
                    if c_a2.button("💰 Öde", key=f"pay_{t}_{ad}"):
                        detay['odendi'] = True
                        arsiv_guncelle(t, ad, detay)
                        st.rerun()
    st.metric("Bekleyen Toplam", f"{toplam:,.2f} TL")
