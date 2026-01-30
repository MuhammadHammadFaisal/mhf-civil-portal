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
    # CUSTOM CSS (Fixed Dropdown Visibility)
    # ==================================================
    st.markdown("""
    <style>
    /* 1. Target the Dropdown's Main Box */
    /* We use a lighter grey (#3b3f4d) so it pops out from the black background */
    div[data-baseweb="select"] > div {
        background-color: #3b3f4d !important; 
        border: 2px solid #5a5f70 !important;  /* Lighter border for contrast */
        color: white !important;
        border-radius: 8px !important;
    }

    /* 2. Target the SVG Arrow inside the dropdown */
    div[data-baseweb="select"] svg {
        fill: white !important;
    }
    
    /* 3. Text color inside the dropdown options */
    div[data-baseweb="select"] span {
        color: white !important;
    }
    
    /* 4. Dropdown Menu Items (The list that opens up) */
    ul[data-baseweb="menu"] {
        background-color: #3b3f4d !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- PROFESSIONAL HEADER ---
    col_logo, col_text = st.columns([1, 5])

    with col_logo:
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

    # ==================================================
    # [NEW] SPACING FIX
    # This adds 40px of vertical empty space
    # ==================================================
    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)

    # --- TOPIC SELECTION MENU ---
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
