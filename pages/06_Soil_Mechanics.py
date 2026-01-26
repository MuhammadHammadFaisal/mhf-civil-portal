import streamlit as st

# --- 1. CRITICAL: CONFIG MUST BE BEFORE CUSTOM IMPORTS ---
st.set_page_config(
    page_title="Soil Mechanics", 
    page_icon="assets/logo.png", 
    layout="wide"
)

# --- 2. NOW IMPORT TOPICS ---
# (If these imports happened before config, it causes the "Cache/Config" error)
from topics import soil_phase
from topics import effective_stress
from topics import flow_water

def app():
    # Header
    try:
        c1, c2 = st.columns([1, 5], vertical_alignment="center")
    except:
        c1, c2 = st.columns([1, 5])

    with c1:
        # Optional: Add logo here if desired, or keep it clean
        pass 
    with c2:
        st.title("Soil Mechanics Portal")
        st.caption("Phase Relationships • Effective Stress • Flow Nets")

    st.markdown("---")

    # Topic Router
    topic = st.sidebar.radio(
        "Select Module:", 
        ["1D Seepage & Stress", "Permeability Tests", "2D Flow Net Analysis", "Phase Relationships"]
    )

    if topic == "1D Seepage & Stress":
        flow_water.render_tab1_seepage()
        
    elif topic == "Permeability Tests":
        flow_water.render_tab2_permeability()
        
    elif topic == "2D Flow Net Analysis":
        flow_water.render_tab3_flownet()
        
    elif topic == "Phase Relationships":
        soil_phase.app()

if __name__ == "__main__":
    app()
