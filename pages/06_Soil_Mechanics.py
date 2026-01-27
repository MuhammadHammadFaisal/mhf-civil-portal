import streamlit as st
# IMPORT MODULES
from topics import soil_phase
from topics import effective_stress
from topics import flow_water
from topics import consolidation
# 1. PAGE CONFIG
st.set_page_config(
    page_title="Soil Mechanics", 
    page_icon="assets/logo.png", 
    layout="wide"
)

def app():
    # =================================================================
    # 0. DISCLAIMER & HEADER
    # =================================================================
    st.warning("⚠️ **BETA VERSION:** This module is currently in testing. Calculations should be verified manually.", icon="🚧")
    st.header("🏗️ Consolidation Analysis")
    st.markdown("Select your calculation goal below. Step-by-step math is provided in the results.")
    st.markdown("---")

    # --- PROFESSIONAL HEADER ---
    # Column Ratio [1, 5] keeps logo compact
    col_logo, col_text = st.columns([1, 5])

    with col_logo:
        # [STYLE UPGRADE] 
        # Since the logo has a white background, we frame it like an "App Icon"
        # with a subtle border and shadow so it looks intentional.
        st.markdown(
            """
            <style>
            div[data-testid="stImage"] > img {
                border-radius: 15px;
                border: 2px solid #444;
                box-shadow: 0px 4px 6px rgba(0,0,0,0.3);
            }
            </style>
            """, 
            unsafe_allow_html=True
        )
        st.image("assets/logo.png", width=150) 

    with col_text:
        # [ALIGNMENT FIX]
        # Added 'padding-top: 15px' to push text down so it centers with the logo
        st.markdown(
            """
            <div style="padding-top: 15px; padding-left: 10px;">
                <h1 style='font-size: 45px; margin-bottom: 5px; line-height: 1.0;'>Soil Mechanics</h1>
                <p style='color: #888; font-size: 18px; font-weight: 300; margin: 0;'>
                    Phase Relationships, Effective Stress & Flow Analysis
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )

    st.markdown("---")

    # --- TOPIC SELECTION MENU ---
    # Wrapped in a container to separate navigation from the header
    with st.container(border=True):
        topic = st.selectbox(
            "Select Calculation Module:", 
            [
                "Phase Relationships",
                "Effective Stress",
                "Flow of Water in Soils"
                "Consolidation Theory"
            ]
        )

    # --- ROUTER LOGIC ---
    if topic == "Phase Relationships":
        soil_phase.app()

    elif topic == "Effective Stress":
        effective_stress.app()

    elif topic == "Flow of Water in Soils":
        flow_water.app()
    elif topic == "Consolidation Theory":
        consolidation.app()

if __name__ == "__main__":
    app()
