
import streamlit as st
import pandas as pd
import numpy as np
import joblib

st.set_page_config(page_title="Sistem Cerdas IoT-ML", layout="wide")
st.markdown("""
<style>
.main .block-container{
    max-width: 1400px;
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)

# =====================
# LOAD MODEL
# =====================
MODEL_FILE = "et_model1_npk.pkl"

@st.cache_resource
def load_model():
    try:
        return joblib.load(MODEL_FILE)
    except Exception:
        return None

model = load_model()

# =====================
# THRESHOLD (SESUAIKAN DENGAN NOTEBOOK JIKA SUDAH ADA NILAI FINAL)
# =====================
THRESHOLDS = {
    "N": (60.0, 113.0),
    "P": (35.0, 62.0),
    "K": (45.0, 83.0)
}

def kategori(v, low, high):
    if v < low:
        return "Rendah"
    elif v <= high:
        return "Sedang"
    return "Tinggi"

def status_suhu(temp):
    if 24 <= temp <= 32:
        return "Optimal"
    elif 20 <= temp <= 24:
        return "Cukup"
    elif temp > 32 :
        return "Terlalu Tinggi"
    return "Kurang"

def status_rh(rh):
    if 60 <= rh <= 85:
        return "Optimal"
    elif 50 <= rh <= 60:
        return "Cukup"
    elif rh > 85:
        return "Terlalu Tinggi"
    return "Kurang"

def status_hujan(rain):
    if 100 <= rain <= 300:
        return "Optimal"
    elif 50 <= rain <= 100:
        return "Cukup"
    elif rain > 300:
        return "Terlalu Tinggi"
    return "Kurang"

# =====================
# BASIS PENGETAHUAN TANAMAN
# =====================
TANAMAN = {
    "Padi":   {"N":"Sedang","P":"Sedang","K":"Sedang","temp":(24,30),"rh":(70,90),"rain":(200,400)},
    "Jagung": {"N":"Tinggi","P":"Sedang","K":"Sedang","temp":(21,32),"rh":(60,85),"rain":(100,250)},
    "Cabai":  {"N":"Sedang","P":"Tinggi","K":"Tinggi","temp":(24,30),"rh":(60,80),"rain":(100,250)},
    "Tomat":  {"N":"Sedang","P":"Sedang","K":"Tinggi","temp":(20,28),"rh":(60,80),"rain":(80,200)},
    "Terong": {"N":"Sedang","P":"Sedang","K":"Tinggi","temp":(22,30),"rh":(60,85),"rain":(100,250)},
    "Kelapa": {"N":"sedang","P":"Rendah","K":"Rendah","temp":(27,32),"rh":(40,90),"rain":(150,400)}
}

def skor_tanaman(n,p,k,temp,rh,rain):
    hasil=[]
    for nama,d in TANAMAN.items():
        skor=0
        skor += 20 if n==d["N"] else 0
        skor += 20 if p==d["P"] else 0
        skor += 20 if k==d["K"] else 0
        skor += 15 if d["temp"][0] <= temp <= d["temp"][1] else 0
        skor += 10 if d["rh"][0] <= rh <= d["rh"][1] else 0
        skor += 15 if d["rain"][0] <= rain <= d["rain"][1] else 0
        hasil.append((nama,skor))
    return sorted(hasil,key=lambda x:x[1],reverse=True)

# =====================
# PUPUK
# =====================
def rekom_pupuk(n,p,k,temp,rh,rain):
    pupuk={
        "Urea":150 if n=="Rendah" else 100 if n=="Sedang" else 50,
        "SP36":100 if p=="Rendah" else 75 if p=="Sedang" else 50,
        "KCl":100 if k=="Rendah" else 75 if k=="Sedang" else 50
    }

    catatan=[]

    if rain > 300:
        pupuk["Urea"]=round(pupuk["Urea"]*1.15,1)
        catatan.append("Curah hujan tinggi, dosis Urea ditingkatkan 15%.")

    if temp > 30:
        catatan.append("Pemupukan disarankan pagi atau sore hari.")

    if rh > 85:
        catatan.append("Lakukan pemupukan saat cuaca cerah.")

    return pupuk,catatan

# =====================
# STYLE
# =====================
st.markdown("""
<style>

.metric-card{
    padding:15px;
    border-radius:16px;
    border:1px solid #E5E7EB;
    background:white;
    text-align:center;
    min-height:220px;
}

.metric-title{
    font-size:22px;
    font-weight:600;
    color:#374151;
}

.metric-value{
    font-size:60px;
    font-weight:700;
    color:#111827;
    margin-top:20px;
}

.metric-status{
    font-size:22px;
    color:#6B7280;
}

</style>
""", unsafe_allow_html=True)

# =====================
# SIDEBAR
# =====================
with st.sidebar:
    st.header("📡 Data Tanah")

    n_val = st.number_input("Nitrogen (ppm)",0.0,300.0,75.0)
    p_val = st.number_input("Fosfor (ppm)",0.0,300.0,42.0)
    k_val = st.number_input("Kalium (ppm)",0.0,300.0,58.0)

    ph_val = st.slider("pH Tanah",3.0,10.0,6.5)
    moisture_val = st.slider("Kelembapan Tanah (%)",0,100,40)
    ec_val = st.slider("EC (dS/m)",0.0,10.0,1.5)

    st.header("🌦️ Mikroiklim")

    temp_val = st.slider("Suhu (°C)",15.0,40.0,28.0)
    rh_val = st.slider("Kelembapan Udara (%)",30,100,80)
    rain_val = st.number_input("Curah Hujan Bulanan (mm)",0,1000,200)

    analisis = st.button("🚀 Analisis", use_container_width=True)

st.title("🌱 Sistem Cerdas IoT‑ML")
st.caption("Rekomendasi Adaptif Tanaman dan Pemupukan Berbasis Data Tanah dan Mikroiklim")

if analisis:

    n_cat = kategori(n_val,*THRESHOLDS["N"])
    p_cat = kategori(p_val,*THRESHOLDS["P"])
    k_cat = kategori(k_val,*THRESHOLDS["K"])

    npk_label = "-"
    confidence = 0

    if model is not None:
        try:
            X = pd.DataFrame([[
                ph_val,
                moisture_val,
                ec_val,
                n_val,
                p_val,
                k_val
            ]], columns=[
                "Soil_pH",
                "Soil_Moisture",
                "Electrical_Conductivity",
                "Nitrogen_Level",
                "Phosphorus_Level",
                "Potassium_Level"
            ])

            pred = int(model.predict(X)[0])
            label_map = {0:"Rendah",1:"Sedang",2:"Tinggi"}
            npk_label = label_map.get(pred,"Sedang")

            if hasattr(model,"predict_proba"):
                confidence = round(np.max(model.predict_proba(X))*100,1)

        except Exception as e:
            st.warning(f"Model tidak dapat digunakan: {e}")

    c1,c2,c3,c4 = st.columns(
    [1,1,1,1],
    gap="medium"
)

    cards = [
        (c1,"NITROGEN (N)",n_val,n_cat),
        (c2,"FOSFOR (P)",p_val,p_cat),
        (c3,"KALIUM (K)",k_val,k_cat)
    ]

    for col,title,val,status in cards:
        with col:
            st.markdown(f"""
            <div class='metric-card'>
            <h3>{title}</h3>
            <div><h2>{int(val)}</h2></div>
            <div>{status}</div>
            </div>
            """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class='metric-card'>
        <h5>STATUS KESUBURAN LAHAN</h5>
        <h2>{npk_label}</h2>
        <div>Confidence: {confidence}%</div>
        </div>
        """, unsafe_allow_html=True)

    if npk_label == "Rendah":
        st.error(
            "Kesuburan lahan rendah. Diperlukan peningkatan unsur hara sebelum budidaya."
    )

    elif npk_label == "Sedang":
        st.warning(
            "Kesuburan lahan cukup baik namun masih memerlukan optimasi pemupukan."
    )

    else:
        st.success(
            "Kesuburan lahan tinggi dan mendukung budidaya tanaman."
    )
    
    mikro = 0
    if 24 <= temp_val <= 30: mikro += 35
    if 60 <= rh_val <= 85: mikro += 30
    if 100 <= rain_val <= 300: mikro += 35

    if mikro >= 80:
        st.success(
        f"🟢 Sangat Sesuai | Indeks Mikroiklim: {mikro}%"
    )
    elif mikro >= 60:
        st.warning(
        f"🟡 Cukup Sesuai | Indeks Mikroiklim: {mikro}%"
    )
    else:
        st.error(
        f"🔴 Kurang Sesuai | Indeks Mikroiklim: {mikro}%"
    )

    ranking = skor_tanaman(
        n_cat,p_cat,k_cat,
        temp_val,rh_val,rain_val
    )

    pupuk,catatan = rekom_pupuk(
        n_cat,p_cat,k_cat,
        temp_val,rh_val,rain_val
    )

    colA,colB = st.columns(2)

    st.subheader("📋 Ringkasan Analisis")
    st.write(f"Status Nitrogen : **{n_cat}**")
    st.write(f"Status Fosfor : **{p_cat}**")
    st.write(f"Status Kalium : **{k_cat}**")
    st.write(f"Status Kesuburan Lahan : **{npk_label}**")

    with colA:
        st.subheader("🌿 Tanaman yang Direkomendasikan")
        for t,s in ranking[:6]:
            st.write(f"• {t} ({s}%)")

    with colB:
        st.subheader("📊 Visualisasi Kondisi NPK")
        chart = pd.DataFrame({
            "Unsur":["N","P","K"],
            "ppm":[n_val,p_val,k_val]
        })
        st.bar_chart(chart.set_index("Unsur"))

    colC,colD = st.columns(2)

    with colC:
        st.subheader("💊 Jenis & Dosis Pupuk")
        st.dataframe(
            pd.DataFrame(list(pupuk.items()),
            columns=["Pupuk","Dosis (kg/ha)"]),
            use_container_width=True,
            hide_index=True
        )
        prioritas = []

        if n_cat == "Rendah":
            prioritas.append(
            "Nitrogen menjadi prioritas utama pemupukan."
        )

        if p_cat == "Rendah":
            prioritas.append(
            "Fosfor perlu ditingkatkan."
        )

        if k_cat == "Rendah":
            prioritas.append(
            "Kalium perlu ditingkatkan."
        )

        for item in prioritas:
            st.warning(item)

    with colD:
        st.subheader("🌦️ Kondisi Mikroiklim")
        st.dataframe(
            pd.DataFrame({
                 "Parameter":["Suhu","RH","Curah Hujan"],
                "Nilai":[
                      f"{temp_val} °C",
                      f"{rh_val} %",
                      f"{rain_val} mm"
         ],
                 "Status":[
                      status_suhu(temp_val),
                      status_rh(rh_val),
                      status_hujan(rain_val)
        ]
         }),
        hide_index=True,
        use_container_width=True
        )

    st.subheader("📌 Catatan")

    if catatan:
        for c in catatan:
            st.info(c)
    else:
        st.success("Kondisi mikroiklim mendukung pemupukan normal.")
