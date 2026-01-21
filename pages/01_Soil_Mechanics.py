import streamlit as st
# IMPORT MODULES
from topics import soil_phase
from topics import effective_stress  # <-- NEW IMPORT

st.set_page_config(page_title="Soil Mechanics", page_icon="🪨", layout="wide")

st.header("🪨 CE 363: Soil Mechanics")

# THE MENU
topic = st.selectbox("Select Topic:", [
    "Phase Relationships",
    "Effective Stress",  # <-- Renamed for clarity
    "Soil Classification" # Moved down as we are skipping it
])

# THE ROUTER
if topic == "Phase Relationships":
    soil_phase.app()

elif topic == "Effective Stress":
    effective_stress.app()  # <-- Activates the new file

elif topic == "Soil Classification":
    st.info("🚧 This module is skipped for now. Will be added later.")
