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
                    Comprehensive Geotechnical Engineering Suite
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
                "1. Introduction",
                "2. Phase Relationships",
                "3. Effective Stress",
                "4. Flow of Water in Soils (Seepage)",
                "5. Consolidation Theory",
                "6. Shear Strength",
                "7. Lateral Earth Pressure",
                "8. Stability of Slopes"
            ],
            index=1 # Defaults to Phase Relationships
        )

    # --- ROUTER LOGIC ---
    
    # Active Modules
    if topic == "2. Phase Relationships":
        soil_phase.app()

    elif topic == "3. Effective Stress":
        effective_stress.app()

    elif topic == "4. Flow of Water in Soils (Seepage)":
        flow_water.app()

    # Maintenance Modules
    else:
        st.warning(f"### 🚧 Under Maintenance")
        st.info(f"The module for **{topic}** is currently being developed. Please check back later!")
        
        # Optional: Show what is coming soon based on the syllabus image
        if "Consolidation" in topic:
            st.write("Upcoming features: Oedometer test analysis, Terzaghi's theory, and Compression indices.")
        elif "Shear Strength" in topic:
            st.write("Upcoming features: Mohr-Coulomb failure criterion and Triaxial test simulations.")

if __name__ == "__main__":
    app()
