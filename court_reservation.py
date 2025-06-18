import streamlit as st
import datetime
import sqlite3
import pandas as pd
import re

# ========== Load CSS ==========
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ========== DB Setup ==========
conn = sqlite3.connect("court_bookings.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        court TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL
    )
""")
conn.commit()

# ========== Sidebar Styling ==========
st.markdown("""
    <style>
    section[data-testid="stSidebar"] {
        background: linear-gradient(to bottom right, #007BFF, #FFA500);
        color: white;
        animation: fadeIn 1s ease-in-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    </style>
""", unsafe_allow_html=True)

# ========== Constants ==========
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123456"

# ========== Session State Init ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "home"
if "selected_court" not in st.session_state:
    st.session_state.selected_court = None

# ========== Login Page ==========
if not st.session_state.logged_in:
    st.sidebar.image("logo.png", width=150)
    st.sidebar.subheader("🔐 Login")

    user_type = st.sidebar.selectbox("Login as", ["Client", "Admin"])
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if user_type == "Admin":
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                st.session_state.logged_in = True
                st.session_state.user_type = "admin"
                st.success("✅ Admin login successful")
                st.session_state.page = "home"
                st.rerun()
            else:
                st.error("❌ Invalid admin credentials")
        else:
            if username.strip() and password.strip():
                st.session_state.logged_in = True
                st.session_state.user_type = "client"
                st.session_state.client_name = username
                st.success(f"✅ Welcome, {username}!")
                st.session_state.page = "home"
                st.rerun()
            else:
                st.error("❌ Please enter valid username/password")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("<h1>🏸 Smart Online Court Reservation System</h1>", unsafe_allow_html=True)
    with col2:
        st.image("logo1.png", width=150)
    st.stop()

# ========== Sidebar After Login ==========
st.sidebar.image("logo.png", width=150)
user_label = "Admin" if st.session_state.user_type == "admin" else st.session_state.client_name
st.sidebar.success(f"Logged in as **{user_label}**")

if st.sidebar.button("Logout"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ========== Page Menu ==========
if st.session_state.user_type == "admin":
    page = st.sidebar.radio("📋 Menu", ["Home", "All Bookings"])
else:
    page = st.sidebar.radio("📋 Menu", ["Home", "View My Bookings"])

# ========== Data ==========
courts = [f"Court {i}" for i in range(1, 7)]
time_slots = ["08:00", "09:00", "10:00", "11:00"]

# ========== HOME PAGE ==========
if page == "Home":
    st.title("🏸 Smart Online Court Reservation System")

    if st.session_state.page == "home":
        st.markdown("## Select a Court:")
        cols = st.columns(3)
        for i, court in enumerate(courts):
            if cols[i % 3].button(court):
                st.session_state.selected_court = court
                st.session_state.page = "time"

    elif st.session_state.page == "time":
        court = st.session_state.selected_court
        date = st.date_input("Select a date", datetime.date.today())
        st.markdown(f"### {court} - Select a Time Slot for {date}")

        if st.session_state.user_type == "client":
            name = st.session_state.client_name
            st.markdown(f"**Booking as:** {name}")
        else:
            name = st.text_input("Enter your name")

        phone = st.text_input("Enter your phone number")

        cols = st.columns(len(time_slots))
        for i, slot in enumerate(time_slots):
            cursor.execute("SELECT 1 FROM bookings WHERE date=? AND court=? AND time=?", (str(date), court, slot))
            is_booked = cursor.fetchone() is not None
            label = f"✅ {slot}" if is_booked else slot

            if cols[i].button(label, key=f"{court}_{slot}_{date}", disabled=is_booked):
                if not name.strip() or not phone.strip():
                    st.warning("⚠️ Please enter both name and phone number before booking.")
                elif not re.fullmatch(r"\d{9,12}", phone):
                    st.warning("⚠️ Nombor telefon mesti antara 9 hingga 12 digit.")
                else:
                    cursor.execute("INSERT INTO bookings (name, phone, court, date, time) VALUES (?, ?, ?, ?, ?)",
                                   (name.strip(), phone.strip(), court, str(date), slot))
                    conn.commit()
                    st.success(f"✅ Booked {court} at {slot} on {date} for {name} ({phone})")

        if st.button("⬅️ Back to Court Selection"):
            st.session_state.page = "home"

# ========== Admin Contact Info for Client ==========
    if st.session_state.user_type == "client":
        st.markdown("---")
        st.markdown("### 📞 Contact Admin")
        st.info("""
        **Admin Name**:Muhammad Fauzan Syafiq  
        **Email**: fauzansyafiq18@google.com  
        **Phone**: +6011-2545 8006
        """)

# ========== BOOKINGS PAGE ==========
elif page in ["All Bookings", "View My Bookings"]:
    if st.session_state.user_type == "admin":
        st.title("📋 All Court Bookings")
        cursor.execute("SELECT id, name, phone, court, date, time FROM bookings ORDER BY date, time")
    else:
        st.title("📋 My Court Bookings")
        client_name = st.session_state.client_name
        cursor.execute("SELECT id, name, phone, court, date, time FROM bookings WHERE name=? ORDER BY date, time", (client_name,))

    rows = cursor.fetchall()

    if rows:
        df = pd.DataFrame(rows, columns=["ID", "Name", "Phone", "Court", "Date", "Time"])

        if st.session_state.user_type == "admin":
            for index, row in df.iterrows():
                with st.expander(f"📌 {row['Court']} - {row['Date']} {row['Time']} ({row['Name']})"):
                    st.write(f"**Name:** {row['Name']}")
                    st.write(f"**Phone:** {row['Phone']}")
                    st.write(f"**Court:** {row['Court']}")
                    st.write(f"**Date:** {row['Date']}")
                    st.write(f"**Time:** {row['Time']}")
                    if st.button(f"🗑️ Cancel Booking ID {row['ID']}", key=f"cancel_{row['ID']}"):
                        cursor.execute("DELETE FROM bookings WHERE id=?", (row["ID"],))
                        conn.commit()
                        st.success(f"❌ Booking ID {row['ID']} canceled.")
                        st.rerun()
            csv = df.drop(columns=["ID"]).to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV", csv, "court_bookings.csv", "text/csv")
        else:
            df = df.drop(columns=["ID"])
            st.dataframe(df, use_container_width=True)
    else:
        st.info("No bookings found.")
