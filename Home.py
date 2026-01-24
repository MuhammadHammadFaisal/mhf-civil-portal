import streamlit as st

# 1. PAGE CONFIG
st.set_page_config(
    page_title="MHF Civil Portal", 
    page_icon="assets/logo.png", 
    layout="wide"
)

# ==========================================
# 2. CONTENT FUNCTIONS
# ==========================================

def original_home_content():
    """Content for the Home Page"""
    st.markdown("# MHF Civil Portal")
    st.caption("Deterministic Civil Engineering Computation Platform")
    st.markdown("---")
    
    st.markdown("""
    ### Precision. Logic. Deterministic.
    
    MHF Civil is a focused engineering workspace built for **civil engineers who care about correctness**.
    No black-box guesses. No approximations without context.
    Just transparent, deterministic engineering calculations.
    """)
    st.markdown("")

    st.markdown("---")
    st.subheader("About MHF Civil")
    st.markdown("""
    ### Muhammad Hammad Faisal
    **Final Year Civil Engineering Student (METU)** Founder — MHF Civil
    
    MHF Civil is built on a simple principle:  
    **engineering results should be reproducible, transparent, and mathematically defensible.**
    """)
    
    st.markdown("[Connect on LinkedIn](https://www.linkedin.com/in/muhammad-hammad-20059a229/)")
    
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666; font-size: 12px;'>"
        "© 2026 MHF Civil. All rights reserved.<br>Version 1.1.0 · Ankara, Turkey"
        "</div>", 
        unsafe_allow_html=True
    )

def construction_page(module_name):
    """Placeholder for empty pages"""
    st.title(f"🔒 {module_name}")
    st.warning("This module is currently under active development.")
    st.info("Status: Planned for future release.")
    st.progress(0.1)

# ==========================================
# 3. MAIN APP LOGIC
# ==========================================

def main():
    # --- [FIX 1] HIDE THE MESSY DEFAULT LIST ---
    # This CSS removes the automatic list of files so only your menu shows.
    st.markdown("""
        <style>
            [data-testid="stSidebarNav"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

    # --- [FIX 2] BIGGER SIDEBAR LOGO ---
    # We use st.sidebar.image instead of st.logo to make it readable.
    with st.sidebar:
        st.image("assets/logo.png", use_container_width=True)
        st.markdown("---")

    # --- MENU DEFINITION ---
    menu_options = [
        "🏠 Home Page",
        "CE 221: Statics",
        "CE 224: Strength of Materials",
        "CE 282: Fluid Mechanics",
        "CE 305: Hydromechanics",
        "CE 363: Soil Mechanics",
        "CE 366: Foundation Eng."
    ]

    # --- NAVIGATION WIDGET ---
    selection = st.sidebar.radio(
        "Navigation", 
        menu_options, 
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("© 2026 MHF Civil")

    # --- ROUTER ---
    if "Home" in selection:
        original_home_content() 

    elif "Soil Mechanics" in selection:
        try:
            from topics import flow_water
            flow_water.app()
        except ImportError:
            st.error("⚠️ Error: Could not find 'topics/flow_water.py'.")

    else:
        construction_page(selection)

if __name__ == "__main__":
    main()
