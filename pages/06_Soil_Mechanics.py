import streamlit as st
# IMPORT MODULES
from topics import soil_phase
from topics import effective_stress
from topics import flow_water

st.set_page_config(page_title="Soil Mechanics", page_icon="assets/logo.png", layout="wide")

st.header("Soil Mechanics")

# THE MENU
topic = st.selectbox("Select Topic:", [
    "Phase Relationships",
    "Effective Stress",  # <-- Renamed for clarity
    "Flow of Water in Soils" # Moved down as we are skipping it
])

# THE ROUTER
if topic == "Phase Relationships":
    soil_phase.app()

elif topic == "Effective Stress":
    effective_stress.app()  # <-- Activates the new file

elif topic == "Flow of Water in Soils":
    flow_water.app()
