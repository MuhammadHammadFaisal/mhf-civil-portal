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
    # ==================================================
    # [NEW] CUSTOM CSS FOR DROPDOWN
    # ==================================================
    st.markdown("""
    <style>
    /* 1. Target the Dropdown's Main Box */
    div[data-baseweb="select"] > div {
        background-color: #262730 !important; /* Dark Grey (Subtle Contrast) */
        border: 1px solid #4c4c52 !important; /* Slight border definition */
        color: white !important;              /* Ensure text is white */
        border-radius: 8px !important;        /* Rounded corners */
    }

    /* 2. Target the SVG Arrow inside the dropdown to make it white */
    div[data-baseweb="select"] svg {
        fill: white !important;
    }
    
    /* 3. Optional: Change hover effect */
    div[data-baseweb="select"] > div:hover {
        border-color: #ff4b4b !important;     /* Highlight on hover */
    }
    </style>
    """, unsafe_allow_html=True)

    # --- PROFESSIONAL HEADER ---
    col_logo, col_text = st.columns([1, 5])

    with col_logo:
        # Logo Styling
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
        # Ensure you have the image or comment this out
        st.image("assets/logo.png", width=150) 

    with col_text:
        # Header Text
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

    # --- TOPIC SELECTION MENU ---
    # Wrapped in a container with a border
    with st.container(border=True):
        topic = st.selectbox(
            "Select Calculation Module:", 
            [
                "Phase Relationships",
                "Effective Stress",
                "Flow of Water in Soils",
                "Consolidation Theory",
                "Shear Strenght of Soils",
                "Lateral Earth Pressure",
                "Stability of Slopes"
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
        
    elif topic == "Shear Strenght of Soils":
        shear_strength.app()
        
    elif topic == "Lateral Earth Pressure":
        lateral_earth_pressure.app()

    elif topic == "Stability of Slopes":
        Stability_of_Slopes.app()


if __name__ == "__main__":
    app()
