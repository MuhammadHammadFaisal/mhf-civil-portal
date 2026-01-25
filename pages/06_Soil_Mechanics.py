def main():
    # --- HERO SECTION ---
    # We use a tighter ratio [1, 2] to keep text close to the logo.
    # We try to use the 'vertical_alignment' parameter (Streamlit 1.38+ feature).
    try:
        col_logo, col_text = st.columns([1, 2], vertical_alignment="center")
    except TypeError:
        # Fallback for older Streamlit versions
        col_logo, col_text = st.columns([1, 2])

    with col_logo:
        # The logo will resize naturally to the column width
        st.image("assets/logo.png", use_container_width=True) 

    with col_text:
        # CSS Styling for Professional Alignment
        # padding-top adjusts the vertical position manually if needed
        st.markdown(
            """
            <div style="padding-top: 10px; padding-left: 10px;">
                <h1 style='font-size: 55px; margin-bottom: 0px; line-height: 1.1;'>MHF Civil Calc</h1>
                <p style='color: #666; font-size: 20px; font-weight: 300; margin-top: 8px;'>
                    Deterministic Civil Engineering Computation Platform
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )

    st.markdown("---")import streamlit as st
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
