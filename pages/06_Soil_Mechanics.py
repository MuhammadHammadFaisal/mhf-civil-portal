import streamlit as st
# IMPORT MODULES
from topics import soil_phase
from topics import effective_stress
from topics import flow_water

# 1. PAGE CONFIG
st.set_page_config(
    page_title="Soil Mechanics", 
    page_icon="assets/logo.png", 
    layout="wide"
)

def app():
    # --- PROFESSIONAL HEADER ---
    # We use a standard [1, 5] ratio.
    # The logo gets a small slot (1), the text gets the rest (5).
    try:
        col_logo, col_text = st.columns([1, 5], vertical_alignment="center")
    except TypeError:
        col_logo, col_text = st.columns([1, 5])

    with col_logo:
        # [STYLE TWEAK] Round the corners of the white logo box so it looks like an App Icon
        st.markdown(
            """
            <style>
            img[data-testid="stImage"] {
                border-radius: 12px;
            }
            </style>
            """, 
            unsafe_allow_html=True
        )
        # Reduced width to 150px. This is the sweet spot for headers.
        st.image("assets/logo.png", width=150) 

    with col_text:
        # Removed left padding to bring text closer to the icon
        st.markdown(
            """
            <div style="padding-left: 0px;">
                <h1 style='font-size: 48px; margin-bottom: 0px; line-height: 1.0;'>Soil Mechanics</h1>
                <p style='color: #888; font-size: 18px; font-weight: 300; margin-top: 5px;'>
                    Phase Relationships, Effective Stress & Flow Analysis
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )

    st.markdown("---")

    # --- TOPIC SELECTION MENU ---
    # Moved to a visual container to separate it from the header
    with st.container(border=True):
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
