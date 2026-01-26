import streamlit as st

# --- 1. PAGE CONFIGURATION (MUST BE FIRST) ---
st.set_page_config(
    page_title="Soil Mechanics", 
    page_icon="assets/logo.png", 
    layout="wide"
)

# --- 2. IMPORT TOPIC MODULES ---
# These files must exist in your 'topics' folder
from topics import flow_water
from topics import soil_phase
from topics import effective_stress

def app():
    # --- HEADER SECTION ---
    try:
        col_logo, col_text = st.columns([1, 5], vertical_alignment="center")
    except TypeError: # Fallback for older Streamlit versions
        col_logo, col_text = st.columns([1, 5])

    with col_logo:
        # If you have a logo, un-comment the line below
        # st.image("assets/logo.png", width=120) 
        pass

    with col_text:
        st.markdown("""
            <div style="padding-left: 0px;">
                <h1 style='font-size: 42px; margin-bottom: 0px; line-height: 1.0;'>Soil Mechanics Portal</h1>
                <p style='color: #666; font-size: 16px; font-weight: 300; margin-top: 5px;'>
                    Course CE363 • METU Civil Engineering
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # --- SIDEBAR NAVIGATION ---
    st.sidebar.header("Select Module")
    topic = st.sidebar.radio(
        "Available Topics:",
        [
            "Flow of Water (Seepage)",
            "Phase Relationships", 
            "Effective Stress"
        ]
    )

    # --- ROUTER LOGIC ---
    if topic == "Flow of Water (Seepage)":
        # Calls the main app function inside topics/flow_water.py
        flow_water.app()

    elif topic == "Phase Relationships":
        # Calls the main app function inside topics/soil_phase.py
        soil_phase.app()

    elif topic == "Effective Stress":
        # Calls the main app function inside topics/effective_stress.py
        effective_stress.app()

if __name__ == "__main__":
    app()
