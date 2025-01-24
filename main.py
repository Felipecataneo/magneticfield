import streamlit as st
from datetime import datetime
import requests
import os
from pyproj import Transformer

api_key = os.getenv("NOAA_API_KEY")


def dms_to_decimal(degrees, minutes, seconds):
    """Converte coordenadas de Graus, Minutos, Segundos para decimal."""
    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def format_lat_lon(lat, lon):
    """Formata latitude e longitude em graus decimais para incluir N/S e W/E."""
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    return f"{abs(lat):.6f}° {lat_dir}", f"{abs(lon):.6f}° {lon_dir}"


def get_epsg(zone):
    """Retorna o código EPSG correspondente à zona no hemisfério sul no SIRGAS2000."""
    base_epsg = 31978  # EPSG base para o hemisfério sul (Zona 18S)
    if 18 <= zone <= 25:  # Zonas válidas para o Brasil
        return base_epsg + (zone - 18)
    else:
        raise ValueError("Zona inválida. Escolha uma zona entre 18 e 25 no hemisfério sul.")


def utm_to_latlon(northing, easting, zone):
    """Converte coordenadas UTM para Latitude/Longitude no SIRGAS2000."""
    epsg_code = get_epsg(zone)
    transformer = Transformer.from_crs(f"EPSG:{epsg_code}", "EPSG:4674", always_xy=True)  # EPSG:4674 é SIRGAS2000 geográfico
    lon, lat = transformer.transform(easting, northing)
    return lat, lon


def get_magnetic_field(lat, lon, date):
    """Obtém os dados do campo magnético da API do NOAA."""
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
        "key": api_key,
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

    # Avisos importantes
    st.warning(
        """
        **Atenção:**
        - Este aplicativo utiliza o sistema de referência SIRGAS2000 para conversões UTM.
        - Certifique-se de selecionar a **zona UTM correta** para seu local (válida para o hemisfério sul entre as zonas 18 e 25).
        - Northing e Easting são valores em metros no sistema UTM.
        """
    )

    # Escolha do tipo de entrada
    st.subheader("Escolha o Tipo de Entrada")
    input_type = st.radio("Tipo de coordenadas para entrada:", ["Latitude/Longitude", "Northing/Easting"], index=0)

    lat_decimal, lon_decimal = None, None

    if input_type == "Latitude/Longitude":
        # Entrada de Latitude/Longitude
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

        # Converter para decimal
        lat_decimal = dms_to_decimal(lat_deg, lat_min, lat_sec)
        if lat_dir == "S":
            lat_decimal = -lat_decimal

        lon_decimal = dms_to_decimal(lon_deg, lon_min, lon_sec)
        if lon_dir == "W":
            lon_decimal = -lon_decimal

    elif input_type == "Northing/Easting":
        # Entrada de Northing/Easting
        st.subheader("Coordenadas UTM")
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            northing = st.number_input("Northing (metros)", min_value=0.0, value=7460122.0, step=0.1, key="northing")
        with col2:
            easting = st.number_input("Easting (metros)", min_value=0.0, value=234567.0, step=0.1, key="easting")
        with col3:
            zone = st.number_input("Zona UTM (18 a 25)", min_value=18, max_value=25, value=23, step=1, key="zone")

        # Converter UTM para Latitude/Longitude em tempo real
        try:
            lat_decimal, lon_decimal = utm_to_latlon(northing, easting, zone)
        except ValueError as e:
            st.error(str(e))

    # Data
    st.subheader("Data")
    data = st.date_input("Selecione a data", datetime.now())

    # Mostrar coordenadas decimais formatadas
    if lat_decimal is not None and lon_decimal is not None:
        formatted_lat, formatted_lon = format_lat_lon(lat_decimal, lon_decimal)
        st.write(f"Latitude: {formatted_lat}")
        st.write(f"Longitude: {formatted_lon}")

    # Botão para calcular o campo magnético
    if st.button("Calcular Campo Magnético"):
        with st.spinner("Calculando..."):
            results = get_magnetic_field(lat_decimal, lon_decimal, data)

            if results and "result" in results:
                result_data = results["result"][0]
                st.success("Resultados do Campo Magnético:")
                st.metric("Declinação", f"{result_data['declination']:.2f}°")
                st.metric("Inclinação", f"{result_data['inclination']:.2f}°")
                st.metric("Intensidade Total", f"{result_data['totalintensity']:.2f} nT")


if __name__ == "__main__":
    main()
