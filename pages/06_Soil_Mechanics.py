import streamlit as st
# IMPORT MODULES
from topics import soil_phase
from topics import effective_stress
from topics import flow_water
from topics import consolidation
from topics import shear_strength
from topics import lateral_earth_pressure
from topics import Stability_of_Slopes

# 1. PAGE CONFIG
st.set_page_config(
    page_title="Soil Mechanics", 
    page_icon="assets/logo.png", 
    layout="wide"
)

def app():
    # CUSTOM CSS
    st.markdown("""
    <style>
    /* Main dropdown box */
    div[data-baseweb="select"] > div {
        background-color: #3b3f4d !important;
        border: 2px solid #5a5f70 !important; 
        color: white !important;
        border-radius: 8px !important;
    }

   /* Dropdown menu background */
    ul[data-baseweb="menu"] {
        background-color: #262730 !important;
        border: 1px solid #5a5f70 !important;
        padding: 10px !important;
    }

    /* Menu options */
    li[data-baseweb="option"] {
        color: white !important;
    }

    /* Hover state */
    li[data-baseweb="option"]:hover {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    
    /* Fix the Arrow Icon color */
    div[data-baseweb="select"] span {
        color: white !important;
    }
    
    /* Fix the Arrow Icon color */
    div[data-baseweb="select"] svg {
        fill: white !important;
    }

    /* Image Styling */
    div[data-testid="stImage"] > img {
        border-radius: 15px;
        border: 2px solid #444;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

    # --- PROFESSIONAL HEADER SECTION ---
    # Adjusted column ratio to give the bigger logo enough space
    col_logo, col_text = st.columns([1.2, 5], vertical_alignment="center")

    with col_logo:
        # Increased logo width slightly to make it "a little big"
        st.image("assets/logo.png", width=180)

    with col_text:
        # Font size set to 55px (Professional look: smaller than logo, but distinct)
        st.markdown(
            """
            <div style="padding-left: 15px;">
                <h1 style='font-size: 55px; margin: 0; line-height: 1.0; font-weight: 700;'>Soil Mechanics</h1>
            </div>
            """, 
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)

    # --- TOPIC SELECTION MENU ---
    topic = st.selectbox(
        "Select Chapter:", 
        [
            "Phase Relationships",
            "Effective Stress",
            "Flow of Water in Soils",
            "Consolidation Theory",
            "Shear Strength of Soils",
            "Lateral Earth Pressure",
            "Stability of Slopes"
        ]
    )

    if topic == "Phase Relationships":
        soil_phase.app()

    elif topic == "Effective Stress":
        effective_stress.app()

    elif topic == "Flow of Water in Soils":
        flow_water.app()
        
    elif topic == "Consolidation Theory":
        consolidation.app()
        
    elif topic == "Shear Strength of Soils":
        shear_strength.app()
        
    elif topic == "Lateral Earth Pressure":
        lateral_earth_pressure.app()

    elif topic == "Stability of Slopes":
        Stability_of_Slopes.app()


if __name__ == "__main__":
    app()
