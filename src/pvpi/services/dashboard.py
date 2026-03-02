import os
import streamlit as st
import pandas as pd
import glob
from pathlib import Path
import time
import altair as alt

from datetime import timedelta

from pvpi.config import PvPiConfig
from pvpi import PvPiClient

client = PvPiClient()
st.set_page_config(page_title="PV Pi Full System Monitor", layout="wide")

# --- CONFIG LOADING ---
@st.cache_resource
def load_config():
    config_path = os.environ.get("PVPI_CONFIG_PATH")
    
    if config_path:
        return PvPiConfig.from_file(config_path)
    
    return PvPiConfig()

@st.cache_data(ttl=60)
def load_all_data(csv_data_path):
    files = glob.glob(str(csv_data_path / "*.csv"))
    if not files:
        return None
    
    dataframes = []
    for f in files:
        try:
            temp_df = pd.read_csv(f)
            if not temp_df.empty:
                temp_df.columns = temp_df.columns.str.strip()
                dataframes.append(temp_df)
        except Exception:
            continue
            
    if not dataframes:
        return None

    # Merge all days into one master record
    all_df = pd.concat(dataframes, axis=0, join='inner', ignore_index=True)
    all_df['Timestamp'] = pd.to_datetime(all_df['Timestamp'])
    return all_df.sort_values('Timestamp')

def plot_with_trend(series, color, label="Value", window=12):
    """Plots a bold moving average with a faded raw data line"""

    raw = series.rename("Raw Data")
    trend = series.rolling(window=window, center=True).mean().rename("Moving Average")
    plot_df = pd.concat([trend, raw], axis=1).reset_index()

    plot_df = plot_df.melt(id_vars=plot_df.columns[0], 
                           var_name="Type", 
                           value_name="Value")

    chart = (
        alt.Chart(plot_df)
        .mark_line()
        .encode(
            x=alt.X(plot_df.columns[0], title=""),
            y=alt.Y("Value", scale=alt.Scale(zero=False), title=label),
            color=alt.Color("Type", scale=alt.Scale(
                domain=["Moving Average", "Raw Data"],
                range=[color, f"{color}44"]
            ))
        )
    )

    st.altair_chart(chart, width="stretch")

# --- DATA PREP ---
config = load_config()
csv_data_path = Path(config.data_log_path)

df_master = load_all_data(csv_data_path)

# --- TOP SUMMARY BOXES (Always Live) ---
st.title("☀️ Live PV Pi Overview")

m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Estimated SoC", f"{client.estimated_soc():.2f} %")
m2.metric("Battery V", f"{client.get_battery_voltage():.2f} V")
m3.metric("Battery A", f"{client.get_battery_current():.2f} A")
m4.metric("PV Voltage", f"{client.get_pv_voltage():.2f} V")
m5.metric("PV Current", f"{client.get_pv_current():.2f} A")
m6.metric("Board Temp", f"{client.get_board_temp()} °C")

st.divider()

st.title("Historical PV Pi Data")
if df_master is not None:
    # --- SIDEBAR: DATE FILTERING ---
    st.sidebar.header("📅 History Filter")
    min_date = df_master['Timestamp'].min().date()
    max_date = df_master['Timestamp'].max().date()
    
    # Default to showing the last 2 days
    try:
        selected_range = st.sidebar.date_input(
            "Select Date Range",
            value=(max_date - timedelta(days=2), max_date),
            min_value=min_date,
            max_value=max_date
        )
    except ValueError:
        # Fallback if there is less than 2 days of data
        selected_range = (min_date, max_date)

    # Filter Logic
    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start_date, end_date = selected_range
        mask = (df_master['Timestamp'].dt.date >= start_date) & \
               (df_master['Timestamp'].dt.date <= end_date)
        df_filtered = df_master.loc[mask]
    else:
        df_filtered = df_master

    # --- INDIVIDUAL PLOTS (Filtered) ---
    # Section 1: PV
    st.header("1. Solar Input")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Input Voltage (V)")
        plot_with_trend(df_filtered.set_index('Timestamp')['PV Voltage'], "#FFCC00", "Volts")
    with col2:
        st.subheader("Input Current (A)")
        plot_with_trend(df_filtered.set_index('Timestamp')['PV Current'], "#FFAA00", "Amps")
    with col3:
        st.subheader("Input Power Estimate (W)")
        pv_pwr = df_filtered.set_index('Timestamp')['PV Voltage'] * df_filtered.set_index('Timestamp')['PV Current']
        plot_with_trend(pv_pwr, "#FFAA00", "Watts")
    st.divider()

    # Section 2: Battery
    st.header("2. Battery Storage")
    col4, col5, col6 = st.columns(3)
    with col4:
        st.subheader("Battery Voltage (V)")
        plot_with_trend(df_filtered.set_index('Timestamp')['Battery Voltage'], "#00CCFF", "Volts")
    with col5:
        st.subheader("Battery Charge Current (A)")
        plot_with_trend(df_filtered.set_index('Timestamp')['Battery Current'], "#0077FF", "Amps")
    with col6:
        st.subheader("Battery Charge Power Estimate (W)")
        batt_pwr = df_filtered.set_index('Timestamp')['Battery Voltage'] * df_filtered.set_index('Timestamp')['Battery Current']
        plot_with_trend(batt_pwr, "#0077FF", "Watts")
    st.divider()

    # Section 3: Thermal
    st.header("3. PV Pi Thermal")
    plot_with_trend(df_filtered.set_index('Timestamp')['PV PI Temperature'], "#FF4B4B", "Temp")

else:
    st.warning("Cannot display historical data as no log files found. Please check your system path or enable log_pvpi_stats in config.json")

# Live Update Refresh
time.sleep(60)
st.rerun()