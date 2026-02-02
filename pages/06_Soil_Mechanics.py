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
        background-color: #3b3f4d !important; /* Lighter Grey */
        border: 2px solid #5a5f70 !important; 
        color: white !important;
        border-radius: 8px !important;
    }

   /* Dropdown menu background */
    ul[data-baseweb="menu"] {
        background-color: #262730 !important;  /* Dark Grey Background */
        border: 1px solid #5a5f70 !important;  /* Border to separate from page */
        padding: 10px !important;
    }

    /* Menu options */
    li[data-baseweb="option"] {
        color: white !important;              /* Text color */
    }

    /* Hover state */
    li[data-baseweb="option"]:hover {
        background-color: #ff4b4b !important; /* Red highlight on hover */
        color: white !important;
    }
    
    /* 6. Fix the Arrow Icon color */
    div[data-baseweb="select"] span {
        color: white !important;
    }
    
    /* 6. Fix the Arrow Icon color */
    div[data-baseweb="select"] svg {
        fill: white !important;
    }
    </style>
    """, unsafe_allow_html=True)


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

    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)

    # --- TOPIC SELECTION MENU ---
    # Removed the border around the container to make it cleaner
    topic = st.selectbox(
        "Select Calculation Module:", 
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
        
    elif topic == "Shear Strength of Soil":
        shear_strength.app()
        
    elif topic == "Lateral Earth Pressure":
        lateral_earth_pressure.app()

    elif topic == "Stability of Slopes":
        Stability_of_Slopes.app()


if __name__ == "__main__":
    app()
