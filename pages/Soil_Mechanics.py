import streamlit as st
# IMPORT MODULES
from topics import soil_phase
from topics import effective_stress  
from topics import flow_water

st.set_page_config(page_title="Soil Mechanics", page_icon="🪨", layout="wide")

st.header("🪨 CE 363: Soil Mechanics")

# THE MENU
topic = st.selectbox("Select Topic:", [
    "Phase Relationships",
    "Effective Stress",
    "Flow of Water",      
])

# THE ROUTER
if topic == "Phase Relationships":
    soil_phase.app()

elif topic == "Effective Stress":
    effective_stress.app()  # <-- Activates the new file
elif topic == "Flow of Water":   # <--- ADD THIS BLOCK
    flow_water.app()
