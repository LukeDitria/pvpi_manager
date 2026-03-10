import os
import streamlit as st
import pandas as pd
import glob
from pathlib import Path
import altair as alt
from datetime import timedelta

from pvpi.config import PvPiConfig
from pvpi import PvPiClient


st.set_page_config(page_title="PV Pi Full System Monitor", layout="wide")


# --- CACHED RESOURCES ---

@st.cache_resource
def get_client():
    return PvPiClient()


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
            with open(f, 'r') as fh:
                temp_df = pd.read_csv(fh)
            if not temp_df.empty:
                temp_df.columns = temp_df.columns.str.strip()
                dataframes.append(temp_df)
        except Exception:
            continue

    if not dataframes:
        return None

    all_df = pd.concat(dataframes, axis=0, join='inner', ignore_index=True)
    all_df['Timestamp'] = pd.to_datetime(all_df['Timestamp'])
    return all_df.sort_values('Timestamp')


# --- PLOTTING ---

def plot_with_trend(series, color, label="Value", window=12):
    """Plots a bold moving average with a faded raw data line."""
    raw = series.rename("Raw Data")
    trend = series.rolling(window=window, center=True).mean().rename("Moving Average")
    plot_df = pd.concat([raw, trend], axis=1).reset_index()
    plot_df = plot_df.melt(id_vars=plot_df.columns[0], var_name="Type", value_name="Value")

    chart = (
        alt.Chart(plot_df)
        .mark_line()
        .encode(
            x=alt.X(plot_df.columns[0], title=""),
            y=alt.Y("Value", scale=alt.Scale(zero=False), title=label),
            color=alt.Color("Type", scale=alt.Scale(
                domain=["Raw Data", "Moving Average"],
                range=[f"{color}44", color]
            )),
            strokeWidth=alt.condition(
                alt.datum.Type == "Raw Data",
                alt.value(5),
                alt.value(3)
            )
        )
    )

    st.altair_chart(chart, width="stretch")


# --- SIDEBAR DATE FILTER (outside fragment so it persists across refreshes) ---

config = load_config()
csv_data_path = Path(config.data_log_path)

# Load once to populate sidebar date bounds
df_initial = load_all_data(csv_data_path)

selected_range = None
if df_initial is not None:
    st.sidebar.header("📅 History Filter")
    min_date = df_initial['Timestamp'].min().date()
    max_date = df_initial['Timestamp'].max().date()

    default_start = max(max_date - timedelta(days=2), min_date)
    default_end = max_date

    date_input_value = default_start if default_start == default_end else (default_start, default_end)

    selected_range = st.sidebar.date_input(
        "Select Date Range",
        value=date_input_value,
        min_value=min_date,
        max_value=max_date
    )


# --- MAIN DASHBOARD (auto-refreshes every 60s) ---

@st.fragment(run_every=60)
def dashboard():
    client = get_client()

    # Live metrics
    st.title("☀️ Live PV Pi Overview")
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Estimated SoC", f"{client.estimated_soc():.2f} %")
    m2.metric("Battery V",     f"{client.get_battery_voltage():.2f} V")
    m3.metric("Battery A",     f"{client.get_battery_current():.2f} A")
    m4.metric("PV Voltage",    f"{client.get_pv_voltage():.2f} V")
    m5.metric("PV Current",    f"{client.get_pv_current():.2f} A")
    m6.metric("Board Temp",    f"{client.get_board_temp()} °C")

    st.divider()

    # Historical data
    st.title("Historical PV Pi Data")
    df_master = load_all_data(csv_data_path)

    if df_master is None:
        st.warning(
            "Cannot display historical data — no log files found. "
            "Please check your system path or enable log_pvpi_stats in config.json"
        )
        return

    # Apply date filter
    if selected_range is None:
        return

    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start_date, end_date = selected_range
        df_filtered = df_master[df_master['Timestamp'].dt.date.between(start_date, end_date)]
    else:
        df_filtered = df_master[df_master['Timestamp'].dt.date == selected_range]

    # Section 1: Solar Input
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
        pv_pwr = (
            df_filtered.set_index('Timestamp')['PV Voltage'] *
            df_filtered.set_index('Timestamp')['PV Current']
        )
        plot_with_trend(pv_pwr, "#FFAA00", "Watts")

    st.divider()

    # Section 2: Battery Storage
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
        batt_pwr = (
            df_filtered.set_index('Timestamp')['Battery Voltage'] *
            df_filtered.set_index('Timestamp')['Battery Current']
        )
        plot_with_trend(batt_pwr, "#0077FF", "Watts")

    st.divider()

    # Section 3: Thermal
    st.header("3. PV Pi Thermal")
    plot_with_trend(df_filtered.set_index('Timestamp')['PV PI Temperature'], "#FF4B4B", "Temp (°C)")


dashboard()