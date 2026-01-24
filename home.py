import streamlit as st

# ==========================================
# 1. PAGE CONTENT FUNCTIONS
# ==========================================

def original_home_content():
    """Restored Original Home Page Content"""
    st.title("MHF Civil Portal")
    st.caption("Deterministic Civil Engineering Computation Platform")
    st.markdown("---")
    
    st.subheader("Precision. Logic. Deterministic.")
    st.markdown("""
    MHF Civil is a focused engineering workspace built for **civil engineers who care about correctness**. 
    
    No black-box guesses. No approximations without context. Just transparent, deterministic engineering calculations.
    """)
    
    st.markdown("---")
    
    st.subheader("About MHF Civil")
    st.markdown("### Muhammad Hammad Faisal")
    st.markdown("**Final Year Civil Engineering Student (METU)**")
    st.caption("Founder — MHF Civil")
    
    st.markdown("""
    MHF Civil is built on a simple principle:
    **engineering results should be reproducible, transparent, and mathematically defensible.**
    """)
    
    st.link_button("Connect on LinkedIn", "https://www.linkedin.com/") # Add your actual URL here

def construction_page(module_name):
    """Placeholder for missing courses"""
    st.title(f"🔒 {module_name}")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.warning("Module Under Construction")
        st.caption("This engineering module is currently in the development queue.")
    
    with col2:
        st.write("### Development Roadmap")
        st.write(f"**Target Release:** Fall 2026")
        st.progress(0.05, text="Coding in progress...")

# ==========================================
# 2. MAIN APP & SIDEBAR LOGIC
# ==========================================

def main():
    st.set_page_config(page_title="MHF Civil", page_icon="🏗️", layout="wide")

    # --- SIDEBAR SETUP ---
    st.sidebar.title("🏗️ MHF Civil")
    st.sidebar.markdown("### Navigation")

    # Define the Menu Structure (The "Blocks")
    menu_options = [
        "🏠 Home Page",
        "--- 2ND YEAR MODULES ---",
        "CE 221: Statics",
        "CE 224: Strength of Materials",
        "CE 241: Materials Science",
        "CE 282: Fluid Mechanics",
        "--- 3RD YEAR MODULES ---",
        "CE 305: Hydromechanics",
        "CE 353: Transportation Eng.",
        "✅ CE 363: Soil Mechanics",  # Active Module
        "CE 366: Foundation Eng.",
        "CE 383: Structural Analysis"
    ]

    # The Selection Widget
    selection = st.sidebar.radio("Go to:", menu_options, label_visibility="collapsed")

    # --- ROUTER LOGIC ---
    
    # 1. Home Page
    if "Home" in selection:
        original_home_content()

    # 2. Active Module (Soil Mechanics)
    elif "Soil Mechanics" in selection:
        try:
            from topics import flow_water 
            flow_water.app()
        except ImportError:
            st.error("⚠️ Error: Could not load Soil Mechanics module. Ensure 'topics/flow_water.py' exists.")

    # 3. Separators (If user clicks the dashed lines)
    elif "---" in selection:
        st.sidebar.warning("Please select a course below the header.")
        original_home_content()

    # 4. Under Construction Pages (Everything else)
    else:
        construction_page(selection)

    # --- SIDEBAR FOOTER ---
    st.sidebar.markdown("---")
    st.sidebar.caption("© 2026 MHF Civil Engineering")

if __name__ == "__main__":
    main()
