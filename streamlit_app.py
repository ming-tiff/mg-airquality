# air_quality_dashboard.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="🌱 Air Quality Dashboard", layout="wide")

st.title("🌱 Global Air Quality Dashboard")
st.markdown("This dashboard uses free data from [OpenAQ](https://openaq.org/) to show PM2.5 levels worldwide.")

# --- Sidebar ---
st.sidebar.header("Settings")
city = st.sidebar.text_input("Enter a city name", "Kuala Lumpur")
parameter = st.sidebar.selectbox("Select parameter", ["pm25", "pm10", "no2", "o3"])

# --- Fetch Data ---
url = f"https://api.openaq.org/v2/measurements?city={city}&parameter={parameter}&limit=100&sort=desc"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()["results"]
    if len(data) > 0:
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"]["utc"])

        st.subheader(f"Air Quality in {city} ({parameter.upper()})")
        st.write(f"Showing latest {len(df)} measurements")

        # --- Line Chart ---
        fig = px.line(df, x="date", y="value", title=f"{parameter.upper()} levels over time")
        st.plotly_chart(fig, use_container_width=True)

        # --- Map ---
        if "coordinates" in df.columns:
            coords = df.dropna(subset=["coordinates"])
            if not coords.empty:
                coords["lat"] = coords["coordinates"].apply(lambda x: x.get("latitude"))
                coords["lon"] = coords["coordinates"].apply(lambda x: x.get("longitude"))
                st.map(coords[["lat", "lon"]])
    else:
        st.warning(f"No data found for {city}. Try another city.")
else:
    st.error("Failed to fetch data from OpenAQ API")
