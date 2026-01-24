import streamlit as st

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="MHF Civil Portal", 
    page_icon="🏗️", 
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

    # About Section
    st.markdown("---")
    st.subheader("About MHF Civil")
    st.markdown("""
    ### Muhammad Hammad Faisal
    **Final Year Civil Engineering Student (METU)** Founder — MHF Civil
    
    MHF Civil is built on a simple principle:  
    **engineering results should be reproducible, transparent, and mathematically defensible.**
    """)
    
    # 2. CHANGED: Normal Clickable Link instead of Button
    st.markdown("[Connect on LinkedIn](https://www.linkedin.com/in/muhammad-hammad-20059a229/)")
    
    # Footer
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
    st.info("Status: planned for future release.")
    st.progress(0.1)

# ==========================================
# 3. MAIN APP & SIDEBAR LOGIC
# ==========================================

def main():
    # --- SIDEBAR HEADER ---
    st.sidebar.markdown("### 🏗️ MHF Civil")
    # 1. REMOVED: The caption "Engineering modules appear here..." is gone.

    # --- DEFINING THE MENU ---
    # 3. REMOVED: "--- 2ND YEAR ---" headers are removed so they cannot be clicked.
    # 5. REMOVED: Green Tick ✅ from Soil Mechanics.
    menu_options = [
        "🏠 Home Page",
        "CE 221: Statics",
        "CE 224: Strength of Materials",
        "CE 282: Fluid Mechanics",
        "CE 305: Hydromechanics",
        "CE 363: Soil Mechanics",  # 4. FIXED: Clean Name
        "CE 366: Foundation Eng."
    ]

    # --- THE NAVIGATION WIDGET ---
    selection = st.sidebar.radio(
        "Navigation", 
        menu_options, 
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("© 2026 MHF Civil")

    # --- THE ROUTER ---
    
    if "Home" in selection:
        original_home_content() 

    elif "Soil Mechanics" in selection:
        # 4. FIXED: Ensures it loads the 'flow_water' module (the whole file)
        try:
            from pages import 01_Soil_Mechanics.py
            01_Soil_Mechanics.app()
        except ImportError:
            st.error("⚠️ Error: Could not find 'topics/flow_water.py'. Please check your file structure.")

    else:
        # Handles all other "Under Construction" pages
        construction_page(selection)

if __name__ == "__main__":
    main()

