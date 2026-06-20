import streamlit as st
import pandas as pd
import joblib
from fpdf import FPDF
import sqlite3
from datetime import datetime

import sqlite3

conn = sqlite3.connect("hospital.db", check_same_thread=False)
c = conn.cursor() 
# =========================
# =========================
# DOCTOR LOGIN (SIMPLE)
# =========================
# =========================
# DOCTOR LOGIN (SIMPLE)
# =========================
# =========================
# LOGIN SYSTEM START
# =========================

# ⭐ 1. REGISTRATION (HERE)
st.markdown("## 📝 Doctor Registration")

new_user = st.text_input("New Username")
new_pass = st.text_input("New Password", type="password")

if st.button("Register"):
    try:
        c.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (new_user, new_pass)
        )

        conn.commit()

        st.success("Registration successful")

    except:
        st.error("Username already exists")

# ⭐ 2. LOGIN (BELOW THIS)
def login():
    st.title("🔐 Doctor Login")
\
    username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Login"):
        c.execute("SELECT * FROM users WHERE username=? AND password=?",
                  (username, password))
        result = c.fetchone()

        if result:
            st.session_state.logged_in = True
            st.success("Login successful")
        else:
            st.error("Invalid credentials")

 
# LOAD MODEL
# =========================
model = joblib.load("heart_model.pkl")

# =========================
# DATABASE SETUP
# =========================
conn = sqlite3.connect("hospital.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    age INTEGER,
    risk REAL,
    category TEXT,
    time TEXT
)
""")

conn.commit()

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(
    page_title="Heart Disease AI System",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Heart Disease Risk Prediction System")
st.write("AI-based Clinical Decision Support Tool")

# =========================
# PDF GENERATOR
# =========================
def generate_pdf(name, risk, category):
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", size=16)
    pdf.cell(200, 10, txt="Heart Disease Report", ln=True, align='C')

    pdf.ln(10)

    pdf.set_font("Helvetica", size=12)
    pdf.cell(200, 10, txt=f"Patient Name: {name}", ln=True)
    pdf.cell(200, 10, txt=f"Risk Score: {risk:.2f}%", ln=True)
    pdf.cell(200, 10, txt=f"Risk Category: {category}", ln=True)

    file_name = "report.pdf"
    pdf.output(file_name)

    return file_name

# =========================
# INPUTS
# =========================
st.sidebar.header("Patient Details")

name = st.sidebar.text_input("Patient Name")

gender = st.sidebar.selectbox(
    "Gender",
    ["Male", "Female", "Transgender", "Prefer not to say"]
)

gender_map = {
    "Male": 1,
    "Female": 0,
    "Transgender": 2,
    "Prefer not to say": 3
}
gender_value = gender_map[gender]

age = st.sidebar.number_input("Age", 1, 120, 50)
cigsPerDay = st.sidebar.number_input("Cigarettes Per Day", 0, 50, 0)

BPMeds = st.sidebar.selectbox("BP Medication", ["No", "Yes"])
BPMeds = 1 if BPMeds == "Yes" else 0

diabetes = st.sidebar.selectbox("Diabetes", ["No", "Yes"])
diabetes = 1 if diabetes == "Yes" else 0

totChol = st.sidebar.number_input("Total Cholesterol", 100, 500, 240)
sysBP = st.sidebar.number_input("Systolic BP", 80, 250, 140)
BMI = st.sidebar.number_input("BMI", 10.0, 60.0, 28.0)
glucose = st.sidebar.number_input("Glucose", 40, 400, 85)

# =========================
# PREDICTION BUTTON
# =========================
if st.button("🔍 Predict Risk"):

    input_df = pd.DataFrame(
        [[gender_value, age, cigsPerDay, BPMeds, diabetes,
          totChol, sysBP, BMI, glucose]],
        columns=["male","age","cigsPerDay","BPMeds","diabetes",
                 "totChol","sysBP","BMI","glucose"]
    )

    risk = model.predict_proba(input_df)[0][1] * 100

    st.metric("📊 Risk Score", f"{risk:.2f}%")

    # =========================
    # CATEGORY (FIRST)
    # =========================
    if risk < 20:
        category = "LOW RISK"
        st.success("🟢 LOW RISK - Normal lifestyle")

    elif risk < 50:
        category = "MODERATE RISK"
        st.warning("🟡 MODERATE RISK - Regular checkup")

    elif risk < 75:
        category = "HIGH RISK"
        st.warning("🟠 HIGH RISK - Doctor consult")

    else:
        category = "VERY HIGH RISK"
        st.error("🔴 VERY HIGH RISK - Immediate attention")

    # =========================
    # DATABASE SAVE (AFTER CATEGORY)
    # =========================
    c.execute("""
    INSERT INTO patients (name, age, risk, category, time)
    VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        age,
        float(risk),
        category,
        str(datetime.now())
    ))

    conn.commit()

    # =========================
    # PDF GENERATION
    # =========================
    file = generate_pdf(name, risk, category)

    with open(file, "rb") as f:
        st.download_button(
            "📄 Download Medical Report",
            f,
            file_name="Heart_Report.pdf"
        )
       
        # =========================
st.markdown("## 🏥 Hospital Dashboard")

# =========================
# LOAD DATA FIRST ⭐ IMPORTANT
# =========================
df = pd.read_sql_query("SELECT * FROM patients", conn)

# =========================
# METRICS
# =========================
total = len(df)

high = len(df[df["category"]=="HIGH RISK"])
critical = len(df[df["category"]=="VERY HIGH RISK"])

col1, col2, col3 = st.columns(3)

col1.metric("Total Patients", total)
col2.metric("High Risk", high)
col3.metric("Critical Cases", critical)

# =========================
# 📊 CHART
# =========================
import matplotlib.pyplot as plt

st.markdown("## 📊 Risk Distribution")

fig, ax = plt.subplots()
df["category"].value_counts().plot(kind="pie", autopct="%1.1f%%", ax=ax)

st.pyplot(fig)
# SEARCH PATIENT (BOTTOM SECTION)
# =========================

st.markdown("## 🔍 Search Patient")

search_name = st.text_input("Enter patient name")

if search_name:
    df_search = pd.read_sql_query(
        f"SELECT * FROM patients WHERE name LIKE '%{search_name}%'",
        conn
    )
    st.dataframe(df_search)
    st.markdown("## 📊 Filter by Risk Category")

filter_option = st.selectbox(
    "Select Category",
    ["ALL", "LOW RISK", "MODERATE RISK", "HIGH RISK", "VERY HIGH RISK"]
)

if filter_option == "ALL":
    df = pd.read_sql_query("SELECT * FROM patients", conn)
else:
    df = pd.read_sql_query(
        f"SELECT * FROM patients WHERE category='{filter_option}'",
        conn
    )

st.dataframe(df)
