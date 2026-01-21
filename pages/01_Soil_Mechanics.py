import streamlit as st
# This connects the "Hub" (Sidebar) to the "Spoke" (Calculators)
from topics import soil_phase

st.set_page_config(page_title="Soil Mechanics", page_icon="", layout="wide")

st.header("CE 363: Soil Mechanics")

# THE MENU
# This dropdown lets the user switch questions WITHOUT leaving the Soil Mechanics page
topic = st.selectbox("Select Topic:", [
    "Phase Relationships",
    "Soil Classification",
    "Stress Analysis"
])

# THE ROUTER
if topic == "Phase Relationships":
    # Calls the logic function we just made in Step 1
    soil_phase.app()

elif topic == "Soil Classification":
    st.info("🚧 This module is under construction.")

elif topic == "Stress Analysis":
    st.info("🚧 This module is under construction.")
