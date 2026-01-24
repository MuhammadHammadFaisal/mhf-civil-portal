import streamlit as st

# 1. PAGE CONFIG (Must be the first command)
st.set_page_config(
    page_title="MHF Civil Portal", 
    page_icon="🏗️", 
    layout="wide"
)

# ==========================================
# 2. CONTENT FUNCTIONS
# ==========================================

def original_home_content():
    """The Branding & Bio Page"""
    st.markdown("# MHF Civil Portal")
    st.caption("Deterministic Civil Engineering Computation Platform")
    st.markdown("---")
    
    # Welcome Message
    st.markdown("""
    ### Precision. Logic. Deterministic.
    
    MHF Civil is a focused engineering workspace built for **civil engineers who care about correctness**.
    No black-box guesses. No approximations without context.
    Just transparent, deterministic engineering calculations.
    """)
    st.markdown("")
    st.markdown("")

    # --- ABOUT THE DEVELOPER ---
    st.markdown("---")
    st.subheader("About MHF Civil")
    
    st.markdown("""
    ### Muhammad Hammad Faisal
    **Final Year Civil Engineering Student (METU)** Founder — MHF Civil
    
    MHF Civil is built on a simple principle:  
    **engineering results should be reproducible, transparent, and mathematically defensible.**
    """)
    
    st.link_button("Connect on LinkedIn", "https://www.linkedin.com/in/muhammad-hammad-20059a229/")
    
    # --- FOOTER ---
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 12px;'>
        © 2026 MHF Civil. All rights reserved.<br>
        Version 1.1.0 · Ankara, Turkey
        </div>
        """, 
        unsafe_allow_html=True
    )

def construction_page(module_name):
    """Placeholder for modules not yet built"""
    st.title(f"🔒 {module_name}")
    st.warning("This module is currently under active development.")
    st.caption("Check back later for updates.")
    st.progress(0.1)

# ==========================================
# 3. MAIN APP LOGIC
# ==========================================

def main():
    # --- SIDEBAR CONFIGURATION ---
    st.sidebar.markdown("### 🏗️ MHF Civil")
    st.sidebar.caption("Engineering modules appear here as they are released.")

    # Menu Options
    menu_options = [
        "🏠 Home Page",
        "--- 2ND YEAR MODULES ---",    
        "CE 221: Statics",
        "CE 224: Strength of Materials",
        "CE 282: Fluid Mechanics",
        "--- 3RD YEAR MODULES ---",    
        "CE 305: Hydromechanics",
        "✅ CE 363: Soil Mechanics",   
        "CE 366: Foundation Eng."
    ]

    # Selection Widget
    selection = st.sidebar.radio(
        "Navigation", 
        menu_options, 
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")
    st.sidebar.caption("© 2026 MHF Civil")

    # --- ROUTER LOGIC ---
    # This decides which function to run based on the sidebar click

    if "Home" in selection:
        original_home_content() 

    elif "Soil Mechanics" in selection:
        try:
            from topics import flow_water
            flow_water.app()
        except ImportError:
            st.error("⚠️ Error: Could not find 'topics/flow_water.py'. Please check your file structure.")

    elif "---" in selection:
        # If they click the dashed header lines
        st.sidebar.warning("Please select a course name, not the header.")
        original_home_content()

    else:
        # For all "Under Construction" courses
        construction_page(selection)

if __name__ == "__main__":
    main()
