import streamlit as st
import folium
import osmnx as ox
import networkx as nx
import leafmap.foliumap as leafmap

from apps.navigator import (get_location_from_address,
                            get_graph,
                            get_graph_from_mode,
                            find_shortest_path) 

# Constants
BASEMAPS = ['Satellite', 'Roadmap', 'Terrain', 'Hybrid', 'OpenStreetMap']
TRAVEL_MODE = ['Drive', 'Walk', 'Bike']
TRAVEL_OPTIMIZER = ['Length', 'Time']
ADDRESS_DEFAULT = "Shivamogga, Karnataka, India 577204"

# Functions
def clear_text():
    st.session_state["go_from"] = ""
    st.session_state["go_to"] = ""

def sidebar():
    st.sidebar.title("Choose your travel settings")
    st.sidebar.markdown("A simple app that finds and displays the shortest path between two points on a map.")
    
    basemap = st.sidebar.selectbox("Choose basemap", BASEMAPS)
    if basemap in BASEMAPS[:-1]:
        basemap = basemap.upper()
    
    transport = st.sidebar.selectbox("Choose transport", TRAVEL_MODE)
    optimizer = st.sidebar.selectbox("Choose optimizer", TRAVEL_OPTIMIZER)
    
    address_from = st.sidebar.text_input("Go from", key="go_from")
    address_to = st.sidebar.text_input("Go to", key="go_to")
    
    st.sidebar.button("Clear all address boxes", on_click=clear_text)
    
    st.sidebar.info(
        "This is an open source project and you are very welcome to contribute your "
        "comments, questions, resources and apps as "
        "[issues](https://github.com/maxmarkov/streamlit-navigator/issues) or "
        "[pull requests](https://github.com/maxmarkov/streamlit-navigator/pulls) "
        "to the [source code](https://github.com/maxmarkov/streamlit-navigator)."
    )
    
    return basemap, transport, optimizer, address_from, address_to

def main_page(basemap, address_from, address_to):
    lat, lon = get_location_from_address(address=ADDRESS_DEFAULT)
    if lat is None or lon is None:
        st.write(f"Unable to find location for {ADDRESS_DEFAULT}")
    else:
        # rest of your code 
        m.add_basemap(basemap)
    
    if address_from and address_to:
        graph, location_orig, location_dest = get_graph(address_from, address_to)
        
        st.markdown(f'**From**: {address_from}')
        st.markdown(f'**To**: {address_to}')
        st.write(graph)
        
        leafmap.Map(center=location_orig, zoom=16)
        
        m.add_marker(location=list(location_orig), icon=folium.Icon(color='red', icon='suitcase', prefix='fa'))
        m.add_marker(location=list(location_dest), icon=folium.Icon(color='green', icon='street-view', prefix='fa'))
        
        route = find_shortest_path(graph, location_orig, location_dest, optimizer)
        ox.plot_route_folium(graph, route, m)
    else:
        m.add_marker(location=(lat, lon), popup=f"lat, lon: {lat}, {lon}", icon=folium.Icon(color='green', icon='eye', prefix='fa'))
        st.write(f"Lat, Lon: {lat}, {lon}")
    
    m.to_streamlit()

# Streamlit configuration
st.set_page_config(page_title="🚋 Route finder", layout="wide")

# Sidebar configuration
basemap, transport, optimizer, address_from, address_to = sidebar()

# Main page configuration
main_page(basemap, address_from, address_to)
