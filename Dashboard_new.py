
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
    "Padi":   {"N":"Sedang","P":"Sedang","K":"Sedang","temp":(24,30),"rh":(70,90),"rain":(200,350)},
    "Jagung": {"N":"Rendah","P":"Sedang","K":"Sedang","temp":(21,32),"rh":(60,85),"rain":(100,250)},
    "Cabai":  {"N":"Sedang","P":"Tinggi","K":"Tinggi","temp":(24,30),"rh":(60,80),"rain":(100,250)},
    "Tomat":  {"N":"Sedang","P":"Sedang","K":"Tinggi","temp":(20,28),"rh":(60,80),"rain":(80,200)},
    "Terong": {"N":"Sedang","P":"Sedang","K":"Tinggi","temp":(22,30),"rh":(60,85),"rain":(100,250)},
    "Kelapa": {"N":"sedang","P":"Rendah","K":"Rendah","temp":(27,32),"rh":(40,90),"rain":(150,400)}
}

def skor_tanaman(n, p, k, temp, rh, rain):

    hasil = []

    for nama, d in TANAMAN.items():

        skor = 0
        detail = {}

        # ==========================
        # DATA TANAH
        # ==========================

        if n == d["N"]:
            skor += 20
            detail["Nitrogen"] = {"Status": "Sesuai", "Skor": 20}
        else:
            detail["Nitrogen"] = {"Status": "Tidak Sesuai", "Skor": 0}

        if p == d["P"]:
            skor += 20
            detail["Fosfor"] = {"Status": "Sesuai", "Skor": 20}
        else:
            detail["Fosfor"] = {"Status": "Tidak Sesuai", "Skor": 0}

        if k == d["K"]:
            skor += 20
            detail["Kalium"] = {"Status": "Sesuai", "Skor": 20}
        else:
            detail["Kalium"] = {"Status": "Tidak Sesuai", "Skor": 0}

        # ==========================
        # DATA MIKROIKLIM (BMKG)
        # ==========================

        if d["temp"][0] <= temp <= d["temp"][1]:
            skor += 15
            detail["Suhu"] = {"Status": "Optimal", "Skor": 15}
        else:
            detail["Suhu"] = {"Status": "Tidak Optimal", "Skor": 0}

        if d["rh"][0] <= rh <= d["rh"][1]:
            skor += 10
            detail["Kelembapan"] = {"Status": "Optimal", "Skor": 10}
        else:
            detail["Kelembapan"] = {"Status": "Tidak Optimal", "Skor": 0}

        if d["rain"][0] <= rain <= d["rain"][1]:
            skor += 15
            detail["Curah Hujan"] = {"Status": "Optimal", "Skor": 15}
        else:
            detail["Curah Hujan"] = {"Status": "Tidak Optimal", "Skor": 0}

        hasil.append({
            "Tanaman": nama,
            "Skor": skor,
            "Detail": detail
        })

    hasil = sorted(
        hasil,
        key=lambda x: x["Skor"],
        reverse=True
    )

    return hasil
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
        catatan.append("Curah hujan tinggi(Nitrogen lebih cepat tercuci), dosis Urea ditingkatkan 15%.")

    if temp > 30:
        catatan.append("Pemupukan disarankan pagi atau sore hari.")

    if rh > 80:
        catatan.append(
            "Kelembapan udara relatif tinggi (>85%). "
            "Pemupukan disarankan dilakukan saat cuaca cerah untuk meningkatkan efektivitas penyerapan pupuk dan mengurangi risiko kehilangan pupuk akibat kondisi lingkungan yang lembap."
    )

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

    colA,colB = st.columns([1,1])

    st.subheader("📋 Ringkasan Analisis")
    st.write(f"Status Nitrogen : **{n_cat}**")
    st.write(f"Status Fosfor : **{p_cat}**")
    st.write(f"Status Kalium : **{k_cat}**")
    st.write(f"Status Kesuburan Lahan : **{npk_label}**")

    with colA:

        st.subheader("🌿 Tanaman yang Direkomendasikan")

        for item in ranking[:6]:

            st.write(
                f"**{item['Tanaman']}** ({item['Skor']}%)"
            )
        st.markdown("---")
        st.subheader("🔍 Analisis Rekomendasi Tanaman")
        terbaik = ranking[0]

        st.write(
            f"Tanaman dengan tingkat kesesuaian tertinggi adalah **{terbaik['Tanaman']}** "
            f"dengan skor **{terbaik['Skor']}%**."
)

        detail_df = pd.DataFrame([
            {
                "Parameter": k,
                "Status": v["Status"],
                "Kontribusi Skor": v["Skor"]
            }
            for k, v in terbaik["Detail"].items()
        ])
         
        st.dataframe(
            detail_df,
            hide_index=True,
            use_container_width=True
        )
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

  
    with colB:
        st.subheader("📊 Visualisasi Kondisi NPK")
        chart = pd.DataFrame({
            "Unsur":["N","P","K"],
            "ppm":[n_val,p_val,k_val]
        })
        st.bar_chart(chart.set_index("Unsur"))
        st.subheader("🌦️ Analisis Pengaruh Mikroiklim (BMKG)")

    # ======================
    # SUHU
    # ======================

        suhu_status = status_suhu(temp_val)

        st.markdown(f"""
**🌡️ Suhu Udara**

Nilai : **{temp_val} °C**

Status : **{suhu_status}**
""")

        if suhu_status == "Optimal":
            st.success(
                "Suhu berada pada rentang optimum sehingga mendukung pertumbuhan tanaman dan penyerapan unsur hara."
        )

        elif suhu_status == "Terlalu Tinggi":
            st.warning(
                "Suhu yang tinggi dapat meningkatkan kehilangan Nitrogen melalui penguapan. Pemupukan disarankan dilakukan pada pagi atau sore hari."
        )

        else:
            st.info(
                "Suhu belum berada pada kondisi optimum sehingga pertumbuhan tanaman dapat terpengaruh."
        )

        st.markdown("---")

    # ======================
    # RH
    # ======================

        rh_status = status_rh(rh_val)

        st.markdown(f"""
**💧 Kelembapan Udara (RH)**

Nilai : **{rh_val}%**

Status : **{rh_status}**
""")

        if rh_status == "Optimal":
            st.success(
                "Kelembapan udara berada pada rentang optimum sehingga mendukung pertumbuhan tanaman."
        )

        elif rh_status == "Terlalu Tinggi":
            st.warning(
                "Kelembapan udara tinggi. Pemupukan sebaiknya dilakukan saat cuaca cerah agar penyerapan pupuk lebih optimal."
        )

        else:
            st.info(
                "Kelembapan udara relatif rendah sehingga perlu memperhatikan kondisi lingkungan tanaman."
        )

        st.markdown("---")

    # ======================
    # CURAH HUJAN
    # ======================

        rain_status = status_hujan(rain_val)

        st.markdown(f"""
**🌧️ Curah Hujan**

Nilai : **{rain_val} mm/bulan**

Status : **{rain_status}**
""")

        if rain_status == "Optimal":
            st.success(
                "Curah hujan berada pada rentang yang sesuai sehingga mendukung proses budidaya dan pemupukan."
        )

        elif rain_status == "Terlalu Tinggi":
            st.error(
                "Curah hujan tinggi meningkatkan risiko pencucian (leaching) unsur Nitrogen. Oleh karena itu sistem menyesuaikan dosis Urea dan menyarankan pemupukan dilakukan setelah intensitas hujan menurun."
        )

        else:
            st.info(
                "Curah hujan relatif rendah sehingga ketersediaan air perlu diperhatikan selama budidaya."
        )
    

    if catatan:
        for c in catatan:
            st.info(c)
    else:
        st.success("Kondisi mikroiklim mendukung pemupukan normal.")
