import streamlit as st
import os

# --- 1. PAGE CONFIGURATION (MUST BE FIRST) ---
st.set_page_config(
    page_title="Soil Mechanics", 
    page_icon="assets/logo.png", 
    layout="wide"
)

# --- 2. IMPORT TOPIC MODULES ---
from topics import flow_water
from topics import soil_phase
from topics import effective_stress

def app():
    # --- HEADER SECTION ---
    # Creates a 2-column layout: Small Logo (1) | Big Text (5)
    try:
        col_logo, col_text = st.columns([1, 5], vertical_alignment="center")
    except TypeError:
        col_logo, col_text = st.columns([1, 5])

    with col_logo:
        # CHECK: Ensure 'assets/logo.png' exists in your folder
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", width=120)
        else:
            # Fallback if image is missing
            st.info("Logo missing")

    with col_text:
        st.markdown("""
            <div style="padding-left: 0px;">
                <h1 style='font-size: 42px; margin-bottom: 0px; line-height: 1.0;'>Soil Mechanics Portal</h1>
                <p style='color: #666; font-size: 16px; font-weight: 300; margin-top: 5px;'>
                    Course CE363 • METU Civil Engineering
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # --- MAIN SELECTION MENU (NOT SIDEBAR) ---
    # We use a container to make it look distinct
    with st.container():
        # Using a pill-like selection or radio for easy toggling
        topic = st.radio(
            "Select Calculation Module:",
            [
                "Phase Relationships", 
                "Effective Stress",
                "Flow of Water (Seepage)"
            ],
            horizontal=True # Makes it a nice top bar instead of a vertical list
        )

    st.markdown("---")

    # --- ROUTER LOGIC ---
    if topic == "Phase Relationships":
        soil_phase.app()

    elif topic == "Flow of Water (Seepage)":
        flow_water.app()

    elif topic == "Effective Stress":
        effective_stress.app()

if __name__ == "__main__":
    app()
