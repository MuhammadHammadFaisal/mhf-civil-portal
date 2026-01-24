import streamlit as st

# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="MHF Civil Portal", 
    page_icon="🏗️", 
    layout="wide"
)

# ==========================================
# 2. CONTENT FUNCTIONS (The "Pages")
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
    
    st.link_button("Connect on LinkedIn", "https://www.linkedin.com/in/muhammad-hammad-20059a229/")
    
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
    # --- A. SIDEBAR HEADER ---
    st.sidebar.markdown("### 🏗️ MHF Civil")
    st.sidebar.caption("Engineering modules appear here as they are released.")

    # --- B. DEFINING THE MENU ---
    menu_options = [
        "🏠 Home Page",
        "--- 2ND YEAR MODULES ---",    # Visual Header
        "CE 221: Statics",
        "CE 224: Strength of Materials",
        "CE 282: Fluid Mechanics",
        "--- 3RD YEAR MODULES ---",    # Visual Header
        "CE 305: Hydromechanics",
        "✅ CE 363: Soil Mechanics",   # The Active Page
        "CE 366: Foundation Eng."
    ]

    # --- C. THE NAVIGATION WIDGET ---
    selection = st.sidebar.radio(
        "Go to", 
        menu_options, 
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("© 2026 MHF Civil")

    # --- D. THE ROUTER (Page Switching Logic) ---
    
    if "Home" in selection:
        original_home_content() 

    elif "Soil Mechanics" in selection:
        # Tries to load your actual engineering code
        try:
            from topics import flow_water
            flow_water.app()
        except ImportError:
            st.error("⚠️ Error: Could not find 'topics/flow_water.py'.")

    elif "---" in selection:
        # Handles accidental clicks on headers
        st.sidebar.warning("That is a category header. Please select a course.")
        original_home_content()

    else:
        # Handles all other "Under Construction" pages
        construction_page(selection)

if __name__ == "__main__":
    main()
