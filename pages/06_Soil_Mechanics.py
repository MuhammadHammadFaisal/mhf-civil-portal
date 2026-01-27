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

    st.markdown("---")

    # --- TOPIC SELECTION MENU ---
    with st.container(border=True):
        topic = st.selectbox(
            "Select Calculation Module:", 
            [
                "Basic Properties & Phase Relationships",
                "Effective Stress",
                "Flow of Water (Seepage)",
                "Consolidation Theory",
                "Shear Strength",
                "Lateral Earth Pressure",
                "Stability of Slopes"
            ]
        )

    # --- ROUTER LOGIC ---
    
    # Active Modules
    if topic == "Basic Properties & Phase Relationships":
        soil_phase.app()

    elif topic == "Effective Stress":
        effective_stress.app()

    elif topic == "Flow of Water (Seepage)":
        flow_water.app()

    # Maintenance Modules (Consolidation, Shear Strength, Earth Pressure, Slopes)
    else:
        st.markdown("---")
        st.warning(f"### 🚧 Module Under Maintenance")
        st.info(f"The module for **{topic}** is currently being developed. Please select an active module from the list.")
        
        # Displaying a syllabus reminder of what's coming
        st.write("Current development focus: Implementation of theoretical models and calculation tools for this chapter.")

if __name__ == "__main__":
    app()
