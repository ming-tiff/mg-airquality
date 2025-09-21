# streamlit_app.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="🌱 Air Quality Dashboard", layout="wide")

st.title("🌱 Global Air Quality Dashboard")
st.markdown("This dashboard uses free data from [OpenAQ](https://openaq.org/) to show air quality trends.")

# --- Sidebar ---
st.sidebar.header("Settings")
st.sidebar.markdown("Choose a country, city, and pollutant parameter to explore.")

# --- Fetch Available Countries & Cities ---
@st.cache_data
def get_countries():
    url = "https://api.openaq.org/v2/countries?limit=200"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json().get("results", [])
        return pd.DataFrame(data)
    return pd.DataFrame()

@st.cache_data
def get_cities(country):
    url = f"https://api.openaq.org/v2/cities?country_id={country}&limit=200"
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json().get("results", [])
        return pd.DataFrame(data)
    return pd.DataFrame()

countries_df = get_countries()
country_list = countries_df["code"].tolist() if not countries_df.empty else ["MY"]

country = st.sidebar.selectbox("Select Country", country_list, index=country_list.index("MY") if "MY" in country_list else 0)
cities_df = get_cities(country)

city_list = cities_df["city"].tolist() if not cities_df.empty else []
city = st.sidebar.selectbox("Select City", ["All Cities"] + city_list)

parameter = st.sidebar.selectbox("Select Parameter", ["pm25", "pm10", "no2", "o3"])

# --- Fetch Measurements ---
@st.cache_data
def get_measurements(country, city, parameter):
    if city == "All Cities":
        url = f"https://api.openaq.org/v2/measurements?country_id={country}&parameter={parameter}&limit=100&sort=desc"
    else:
        url = f"https://api.openaq.org/v2/measurements?country_id={country}&city={city}&parameter={parameter}&limit=100&sort=desc"

    res = requests.get(url)
    return res

response = get_measurements(country, city, parameter)

if response.status_code == 200:
    results = response.json().get("results", [])
    if results:
        df = pd.DataFrame(results)

        # --- Process Data ---
        df["datetime"] = pd.to_datetime(df["date"].apply(lambda x: x["utc"]))
        df["value"] = df["value"].astype(float)

        st.subheader(f"Air Quality in {city if city != 'All Cities' else country} ({parameter.upper()})")
        st.write(f"Showing latest {len(df)} measurements")

        # --- Line Chart ---
        fig = px.line(df.sort_values("datetime"), x="datetime", y="value",
                      title=f"{parameter.upper()} levels over time")
        st.plotly_chart(fig, use_container_width=True)

        # --- Map (if coordinates exist) ---
        if "coordinates" in df.columns:
            coords_df = df.dropna(subset=["coordinates"]).copy()
            if not coords_df.empty:
                coords_df["lat"] = coords_df["coordinates"].apply(lambda x: x.get("latitude"))
                coords_df["lon"] = coords_df["coordinates"].apply(lambda x: x.get("longitude"))
                st.map(coords_df[["lat", "lon"]])
    else:
        st.warning(f"No data found for {city}. Try another location or parameter.")
else:
    st.error(f"Failed to fetch data from OpenAQ API (Status {response.status_code})")
    try:
        st.json(response.json())  # show error details for debugging
    except:
        st.write("No detailed error message returned.")
