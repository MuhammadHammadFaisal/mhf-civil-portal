import streamlit as st
# IMPORT MODULES (Ensure these files exist in your 'topics' folder)
from topics import soil_phase
from topics import effective_stress
from topics import flow_water

# 1. PAGE CONFIG (Must be the first Streamlit command)
st.set_page_config(
    page_title="Soil Mechanics", 
    page_icon="assets/logo.png", 
    layout="wide"
)

def app():


    # --- HERO SECTION (The Professional Header) ---
    # We use the [1, 2] ratio and vertical centering to align text with the logo
    try:
        # [0.6, 2.5] makes the logo column much narrower
        col_logo, col_text = st.columns([0.6, 2.5], vertical_alignment="center")
    except TypeError:
        col_logo, col_text = st.columns([1, 2])

    with col_logo:
        st.image("assets/logo.png", use_container_width=True) 

    with col_text:
        st.markdown(
            """
            <div style="padding-top: 10px; padding-left: 10px;">
                <h1 style='font-size: 45px; margin-bottom: 0px; line-height: 1.1;'>Soil Mechanics</h1>
                <p style='color: #666; font-size: 18px; font-weight: 300; margin-top: 8px;'>
                    Phase Relationships, Effective Stress & Flow Analysis
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )

    st.markdown("---")

    # --- TOPIC SELECTION MENU ---
    # Using a selectbox to switch between sub-modules
    topic = st.selectbox(
        "Select Calculation Module:", 
        [
            "Phase Relationships",
            "Effective Stress",
            "Flow of Water in Soils"
        ]
    )

    # --- ROUTER LOGIC ---
    if topic == "Phase Relationships":
        soil_phase.app()

    elif topic == "Effective Stress":
        effective_stress.app()

    elif topic == "Flow of Water in Soils":
        flow_water.app()

if __name__ == "__main__":
    app()
