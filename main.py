import streamlit as st
from datetime import datetime
import requests


def dms_to_decimal(degrees, minutes, seconds):
    """Converte coordenadas de Graus, Minutos, Segundos para decimal"""
    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def format_lat_lon(lat, lon):
    """Formata latitude e longitude em graus decimais para incluir N/S e W/E"""
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    return f"{abs(lat):.6f}° {lat_dir}", f"{abs(lon):.6f}° {lon_dir}"


def get_magnetic_field(lat, lon, date):
    """Obtém os dados do campo magnético da API do NOAA"""
    url = "https://www.ngdc.noaa.gov/geomag-web/calculators/calculateIgrfwmm"

    params = {
        "lat1": lat,
        "lon1": lon,
        "elevation": 0,
        "coordinateSystem": "D",
        "model": "IGRF",
        "startYear": date.year,
        "startMonth": date.month,
        "startDay": date.day,
        "key": "EAU2y",
        "resultFormat": "json",
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao obter dados do NOAA: {e}")
        return None


def main():
    st.set_page_config(page_title="Calculadora de Campo Magnético", layout="wide")
    st.title("Calculadora de Campo Magnético (IGRF)")

    # Latitude
    st.subheader("Latitude")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    with col1:
        lat_deg = st.number_input("Graus", -90, 90, value=24, key="lat_deg")
    with col2:
        lat_min = st.number_input("Minutos", 0, 59, value=33, key="lat_min")
    with col3:
        lat_sec = st.number_input("Segundos", 0.0, 59.9999, value=35.3454, format="%.4f", key="lat_sec")
    with col4:
        lat_dir = st.selectbox("Direção", ["N", "S"], index=1)

    # Longitude
    st.subheader("Longitude")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    with col1:
        lon_deg = st.number_input("Graus", -180, 180, value=42, key="lon_deg")
    with col2:
        lon_min = st.number_input("Minutos", 0, 59, value=14, key="lon_min")
    with col3:
        lon_sec = st.number_input("Segundos", 0.0, 59.9999, value=4.462, format="%.4f", key="lon_sec")
    with col4:
        lon_dir = st.selectbox("Direção", ["E", "W"], index=1)

    # Data
    st.subheader("Data")
    data = st.date_input("Selecione a data", datetime.now())

    # Converter para decimal
    lat_decimal = dms_to_decimal(lat_deg, lat_min, lat_sec)
    if lat_dir == "S":
        lat_decimal = -lat_decimal

    lon_decimal = dms_to_decimal(lon_deg, lon_min, lon_sec)
    if lon_dir == "W":
        lon_decimal = -lon_decimal

    # Mostrar coordenadas decimais formatadas
    formatted_lat, formatted_lon = format_lat_lon(lat_decimal, lon_decimal)
    st.write(f"Latitude: {formatted_lat}")
    st.write(f"Longitude: {formatted_lon}")

    # Botão para calcular o campo magnético
    if st.button("Calcular Campo Magnético"):
        with st.spinner("Calculando..."):
            results = get_magnetic_field(lat_decimal, lon_decimal, data)

            if results and "result" in results:
                # Obter latitude e longitude formatadas do JSON
                result_data = results["result"][0]
                json_lat, json_lon = format_lat_lon(result_data["latitude"], result_data["longitude"])

                st.success("Resultados do Campo Magnético:")
                st.write(f"Latitude (API): {json_lat}")
                st.write(f"Longitude (API): {json_lon}")

                # Exibir outros valores relevantes
                st.metric("Declinação", f"{result_data['declination']:.2f}°")
                st.metric("Inclinação", f"{result_data['inclination']:.2f}°")
                st.metric("Intensidade Total", f"{result_data['totalintensity']:.2f} nT")


if __name__ == "__main__":
    main()
