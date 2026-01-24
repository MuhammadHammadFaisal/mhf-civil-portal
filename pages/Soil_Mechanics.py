import streamlit as st

# --- TRY/EXCEPT BLOCKS prevent crashes if files are missing ---
try:
    from topics import flow_water
except ImportError:
    flow_water = None

# Placeholder for files you haven't created yet (prevents crash)
soil_phase = None 
effective_stress = None

# === THE MAIN FUNCTION ===
def app():
    # 1. REMOVED st.set_page_config (It causes errors in sub-pages)
    
    st.header("🪨 CE 363: Soil Mechanics")

    # THE MENU
    topic = st.selectbox("Select Topic:", [
        "Flow of Water",        # Put the working one first for now
        "Phase Relationships",
        "Effective Stress",
    ])

    # THE ROUTER
    if topic == "Phase Relationships":
        if soil_phase:
            soil_phase.app()
        else:
            st.warning("⚠️ Phase Relationships module not found in 'topics/' folder.")

    elif topic == "Effective Stress":
        if effective_stress:
            effective_stress.app()
        else:
            st.warning("⚠️ Effective Stress module not found in 'topics/' folder.")

    elif topic == "Flow of Water":
        if flow_water:
            flow_water.app()
        else:
            st.error("⚠️ Error: 'topics/flow_water.py' was not found.")
