import streamlit as st
from datetime import datetime
import requests

def dms_to_decimal(degrees, minutes, seconds):
    """Converte coordenadas de Graus, Minutos, Segundos para decimal"""
    return degrees + (minutes / 60.0) + (seconds / 3600.0)

def get_magnetic_field(lat, lon, date):
    """Obtém os dados do campo magnético da API do NOAA"""
    url = "https://www.ngdc.noaa.gov/geomag-web/calculators/calculateIgrfwmm"
    
    # Preparar os parâmetros da URL
    params = {
        'key': 'EAU2y',  # Chave de acesso obrigatória
        'lat1': lat,  # Latitude em decimal
        'lon1': lon,  # Longitude em decimal
        'coordinateSystem': 'D',  # Sistema de coordenadas GPS
        'elevation': 0,  # Elevação em km
        'elevationUnits': 'K',  # Unidade de elevação (K = km)
        'model': 'WMM',  # Modelo magnético
        'startYear': date.year,  # Ano inicial
        'startMonth': date.month,  # Mês inicial
        'startDay': date.day,  # Dia inicial
        'endYear': date.year,  # Ano final (mesmo ano para um único cálculo)
        'endMonth': date.month,  # Mês final
        'endDay': date.day,  # Dia final
        'resultFormat': 'json',  # Formato de resposta em JSON
    }
    
    try:
        # Fazer a requisição
        response = requests.get(url, params=params)
        
        # Debug: Exibir URL e status da requisição
        print("Debug - URL:", response.url)
        print("Debug - Status:", response.status_code)
        
        # Verificar erros na resposta
        response.raise_for_status()
        
        # Retornar os resultados como JSON
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao obter dados do NOAA: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            st.error(f"Detalhes da resposta: {e.response.text}")
            st.error(f"URL da requisição: {e.response.url}")
        return None
    except Exception as e:
        st.error(f"Erro inesperado: {str(e)}")
        return None

def main():
    st.set_page_config(page_title="Calculadora de Campo Magnético", layout="wide")
    st.title("Calculadora de Campo Magnético (IGRF)")
    
    # Latitude
    st.subheader("Latitude")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    with col1:
        lat_deg = st.number_input("Graus", -90, 90, value=24, key='lat_deg')
    with col2:
        lat_min = st.number_input("Minutos", 0, 59, value=33, key='lat_min')
    with col3:
        lat_sec = st.number_input("Segundos", 0.0, 59.9999, value=35.3454, format="%.4f", key='lat_sec')
    with col4:
        lat_dir = st.selectbox("Direção", ["N", "S"], index=1)

    # Longitude
    st.subheader("Longitude")
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    with col1:
        lon_deg = st.number_input("Graus", -180, 180, value=42, key='lon_deg')
    with col2:
        lon_min = st.number_input("Minutos", 0, 59, value=14, key='lon_min')
    with col3:
        lon_sec = st.number_input("Segundos", 0.0, 59.9999, value=4.462, format="%.4f", key='lon_sec')
    with col4:
        lon_dir = st.selectbox("Direção", ["E", "W"], index=1)

    # Data
    st.subheader("Data")
    date = st.date_input("Selecione a data", datetime.now())

    # Converter para decimal
    lat_decimal = dms_to_decimal(lat_deg, lat_min, lat_sec)
    if lat_dir == "S":
        lat_decimal = -lat_decimal
        
    lon_decimal = dms_to_decimal(lon_deg, lon_min, lon_sec)
    if lon_dir == "W":
        lon_decimal = -lon_decimal

    # Mostrar coordenadas decimais
    st.write(f"Latitude decimal: {lat_decimal:.6f}°")
    st.write(f"Longitude decimal: {lon_decimal:.6f}°")

    # Botão para cálculo
    if st.button("Calcular Campo Magnético"):
        with st.spinner('Calculando...'):
            results = get_magnetic_field(lat_decimal, lon_decimal, date)
            
            if results:
                # Exibir resultados
                st.subheader("Resultados do Campo Magnético")
                st.json(results)

if __name__ == "__main__":
    main()
