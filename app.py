import streamlit as st
import time
import random
import google.generativeai as genai
import folium
import osmnx
import networkx as nx
import leafmap.foliumap as leafmap
from apps.navigator import (get_location_from_address,
                            get_graph,
                            get_graph_from_mode,
                            find_shortest_path)

# Retrieve the API key from Streamlit secrets
api_key = st.secrets["GOOGLE_API_KEY"]

if not api_key:
    raise ValueError("API key not found. Please set the GOOGLE_API_KEY in the Streamlit secrets.")

genai.configure(api_key=api_key)

# Function to load Gemini Pro model and get responses
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

def get_gemini_response(question):
    response = chat.send_message(question, stream=True)
    return response

# Function to simulate speed change
def get_new_speed(current_speed):
    change = random.uniform(-5, 5)
    new_speed = current_speed + change
    return max(min_speed, min(new_speed, max_speed))

# Set initial values
min_speed = 0
max_speed = 200
fuel_capacity = random.uniform(60, 70)
fuel_consumption_rate = 0.05  # Fuel consumption per update

# Initialize session state
if 'current_speed' not in st.session_state:
    st.session_state.current_speed = 0

if 'fuel_level' not in st.session_state:
    st.session_state.fuel_level = fuel_capacity

if 'running' not in st.session_state:
    st.session_state.running = False

# Create placeholders for speed and fuel level
speed_placeholder = st.empty()
fuel_placeholder = st.empty()
response_placeholder = st.empty()

# Buttons
if st.session_state.running:
    stop = st.button("Stop")
else:
    start = st.button("Start")

if not st.session_state.running and 'start' in locals() and start:
    st.session_state.running = True
    st.session_state.current_speed = 0
    st.session_state.fuel_level = fuel_capacity
    response_placeholder.empty()

if st.session_state.running and 'stop' in locals() and stop:
    st.session_state.running = False
    input_text = f"I am driving the vehicle at {st.session_state.current_speed:.2f} Km/Hr and with {st.session_state.fuel_level:.2f} Litres. Suggest me one line fuel saving tip."
    response = get_gemini_response(input_text)

    # Display response
    response_placeholder.subheader("The Response is")
    for chunk in response:
        response_text = chunk.text
        response_placeholder.write(response_text)

while st.session_state.running and st.session_state.fuel_level > 0:
    # Update speed
    st.session_state.current_speed = get_new_speed(st.session_state.current_speed)

    # Update fuel level based on current speed
    fuel_consumed = (st.session_state.current_speed / max_speed) * fuel_consumption_rate
    st.session_state.fuel_level -= fuel_consumed
    st.session_state.fuel_level = max(0, st.session_state.fuel_level)  # Ensure fuel level doesn't go below 0

    # Display current speed and fuel level
    speed_placeholder.markdown(f"### Speed: {st.session_state.current_speed:.2f} Km/Hr")
    fuel_placeholder.markdown(f"### Fuel Level: {st.session_state.fuel_level:.2f} Litres")

    # Pause for a short duration to simulate real-time update
    time.sleep(1)

    # Refresh the page
    st.experimental_rerun()

# Navigation Map Setup
BASEMAPS = ['Satellite', 'Roadmap', 'Terrain', 'Hybrid', 'OpenStreetMap']
TRAVEL_MODE = ['Drive', 'Walk', 'Bike']
TRAVEL_OPTIMIZER = ['Length', 'Time']

ADDRESS_DEFAULT = "Grand Place, Bruxelles"

def clear_text():
    st.session_state["go_from"] = ""
    st.session_state["go_to"] = ""

st.set_page_config(page_title="🚋 Route finder", layout="wide")

# ====== SIDEBAR ======
with st.sidebar:
    st.title("Choose your travel settings")
    st.markdown("A simple app that finds and displays the shortest path between two points on a map.")

    basemap = st.selectbox("Choose basemap", BASEMAPS)
    if basemap in BASEMAPS[:-1]:
        basemap = basemap.upper()

    transport = st.selectbox("Choose transport", TRAVEL_MODE)
    optimizer = st.selectbox("Choose optimizer", TRAVEL_OPTIMIZER)

    address_from = st.text_input("Go from", key="go_from")
    address_to = st.text_input("Go to", key="go_to")
    
    st.button("Clear all address boxes", on_click=clear_text)
    st.write(address_to)

    st.info(
        "This is an open source project and you are very welcome to contribute your "
        "comments, questions, resources and apps as "
        "[issues](https://github.com/maxmarkov/streamlit-navigator/issues) or "
        "[pull requests](https://github.com/maxmarkov/streamlit-navigator/pulls) "
        "to the [source code](https://github.com/maxmarkov/streamlit-navigator). "
    )

# ====== MAIN PAGE ======
lat, lon = get_location_from_address(address=ADDRESS_DEFAULT)

m = leafmap.Map(center=(lat, lon), zoom=16)
m.add_basemap(basemap)

if address_from and address_to:
    # === FIND THE PATH ===
    graph, location_orig, location_dest = get_graph(address_from, address_to)
    
    # Search information 
    st.markdown(f'**From**: {address_from}')
    st.markdown(f'**To**: {address_to}')
    st.write(graph)

    # re-center
    leafmap.Map(center=location_orig, zoom=16)

    # find the nearest node to the start location
    m.add_marker(location=list(location_orig), icon=folium.Icon(color='red', icon='suitcase', prefix='fa'))
    m.add_marker(location=list(location_dest), icon=folium.Icon(color='green', icon='street-view', prefix='fa'))

    # find the shortest path
    route = find_shortest_path(graph, location_orig, location_dest, optimizer)
    osmnx.plot_route_folium(graph, route, m)
else:
    m.add_marker(location=(lat, lon), popup=f"lat, lon: {lat}, {lon}", icon=folium.Icon(color='green', icon='eye', prefix='fa'))
    st.write(f"Lat, Lon: {lat}, {lon}")

m.to_streamlit()
