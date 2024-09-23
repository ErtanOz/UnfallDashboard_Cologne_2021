import streamlit as st
import pandas as pd
import pydeck as pdk
from opencage.geocoder import OpenCageGeocode

# Replace 'YOUR_API_KEY' with your actual OpenCage API key
geocoder = OpenCageGeocode('ac8657fff8634409b4ace821b905ada3')

# Daten einlesen
file_path = 'Unfallstatistik 2021.csv'
data = pd.read_csv(file_path, delimiter=';')

# Daten bereinigen
data['XGCSWGS84'] = data['XGCSWGS84'].str.replace(',', '.').astype(float)
data['YGCSWGS84'] = data['YGCSWGS84'].str.replace(',', '.').astype(float)

# Titel der App
st.title('Unfallstatistik 2021')

# Kartenstil Auswahl
map_style_option = st.selectbox(
    'Wählen Sie den Kartenstil:',
    ('OpenStreetMap', 'Pydeck Light Map', 'Pydeck Dark Map', 'Cesium Standard 3D')
)

# Entsprechenden map_style bestimmen
map_styles = {
    'OpenStreetMap': 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',
    'Pydeck Light Map': 'mapbox://styles/mapbox/light-v10',
    'Pydeck Dark Map': 'mapbox://styles/mapbox/dark-v10',
    'Cesium Standard 3D': 'https://assets.agi.com/stk-terrain/world'
}
map_style = map_styles[map_style_option]

# Layer Optionen und Erstellung
layer_options = {
    'Radfahrer': {'column': 'IstRad', 'color': [255, 0, 0]},
    'PKW': {'column': 'IstPKW', 'color': [0, 255, 0]},
    'Fußgänger': {'column': 'IstFuss', 'color': [0, 0, 255]}
}

# Erstellen der Layer basierend auf Benutzerauswahl
layers = [
    pdk.Layer(
        "ScatterplotLayer",
        data[data[details['column']] == 1],
        get_position='[XGCSWGS84, YGCSWGS84]',
        get_radius=100,
        get_color=details['color'],
        pickable=True,
        tooltip={"text": f"{option} beteiligt"}
    ) for option, details in layer_options.items() if st.checkbox(f'{option} beteiligt', True)
]

# Kartenansicht konfigurieren
view_state = pdk.ViewState(latitude=data['YGCSWGS84'].mean(), longitude=data['XGCSWGS84'].mean(), zoom=11, pitch=0)

# Pydeck-Karte anzeigen, falls Layer vorhanden
if layers:
    r = pdk.Deck(layers=layers, initial_view_state=view_state, map_style=map_style)
    st.pydeck_chart(r)
else:
    st.error("Bitte wählen Sie mindestens eine Unfallbeteiligungsoption.")

# Heatmap Layer
if st.checkbox('Heatmap anzeigen'):
    heatmap_layer = pdk.Layer(
        'HeatmapLayer',
        data,
        get_position='[XGCSWGS84, YGCSWGS84]',
        opacity=0.9,
        get_weight="1",
        radius_pixels=30,
        intensity=1,
        threshold=0.05,
        color_range=[(63, 40, 102), (108, 57, 123), (142, 73, 133), (178, 88, 142), (216, 104, 149),
                     (248, 120, 150), (252, 148, 139), (253, 174, 120), (254, 200, 100), (255, 227, 80)]
    )
    heatmap = pdk.Deck(
        layers=[heatmap_layer],
        initial_view_state=view_state,
        map_style=map_style
    )
    st.subheader("Heatmap der Unfallhäufigkeit")
    st.pydeck_chart(heatmap)

# Datenanzeige
if st.checkbox('Daten anzeigen'):
    st.write("Hier sind die Daten der Unfallstatistik 2021:")
    st.dataframe(data)

# Funktion für Reverse Geocoding mit OpenCage
def reverse_geocode(lat, lon):
    results = geocoder.reverse_geocode(lat, lon)
    if results and len(results):
        return results[0]['formatted']
    else:
        return "Unbekannte Straße"

# Gruppierung nach Koordinaten und Unfälle zählen
st.subheader('Top 5 gefährlichste Orte nach Unfallhäufigkeit')

# Unfallhäufigkeit nach Koordinaten ermitteln
most_accident_locations = data.groupby(['XGCSWGS84', 'YGCSWGS84']).size().reset_index(name='Unfallanzahl')
most_accident_locations = most_accident_locations.nlargest(5, 'Unfallanzahl')

# Straßennamen durch Reverse Geocoding ermitteln
most_accident_locations['Straßenname'] = most_accident_locations.apply(
    lambda row: reverse_geocode(row['YGCSWGS84'], row['XGCSWGS84']), axis=1
)

# Anzeigen der Liste mit den häufigsten Unfallorten und Straßennamen
st.write("Top 5 Unfallorte nach Koordinaten und Anzahl der Unfälle:")
st.table(most_accident_locations[['XGCSWGS84', 'YGCSWGS84', 'Unfallanzahl', 'Straßenname']])

# Farblegende
st.markdown("""
<style>
.dot {
    height: 15px;
    width: 15px;
    border-radius: 50%;
    display: inline-block;
}
</style>
<h4>Farblegende</h4>
<span class="dot" style="background-color: rgb(255, 0, 0);"></span> Radfahrer beteiligt<br>
<span class="dot" style="background-color: rgb(0, 255, 0);"></span> PKW beteiligt<br>
<span class="dot" style="background-color: rgb(0, 0, 255);"></span> Fußgänger beteiligt
""", unsafe_allow_html=True)
