import streamlit as st

# ==========================================
# 1. HELPER FUNCTIONS & PAGES
# ==========================================

def home_dashboard():
    """The Main Home Page"""
    st.title("🏗️ MHF Civil Portal")
    st.caption("Deterministic Civil Engineering Computation Platform | METU")
    st.markdown("---")
    
    # Professional Dashboard Layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🚀 Active Workspaces")
        # Active Module Card
        with st.container(border=True):
            c1, c2 = st.columns([1, 5])
            with c1: st.header("🪨")
            with c2:
                st.markdown("**Soil Mechanics (CE 363)**")
                st.caption("Classify soils, calculate flow, and determine effective stress.")
                st.success("● Status: Online")

    with col2:
        st.subheader("Updates")
        st.code("""
v1.2: Added 1D Seepage
v1.1: Fixed Permeability
v1.0: Portal Launch
        """, language="text")
        
        st.info("Developed by Hammad (METU Civil Dept)")

def construction_page(module_name):
    """Placeholder for missing courses"""
    st.title(f"🔒 {module_name}")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        # Professional "Blueprint" style placeholder
        st.warning("Module Under Construction")
        st.caption("This engineering module is currently in the development queue.")
    
    with col2:
        st.write("### Development Roadmap")
        st.write(f"**Target Release:** Fall 2026")
        st.write("**Priority:** Low")
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
    # We use dividers ("---") to visually separate the years
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
        "✅ CE 363: Soil Mechanics",  # Added checkmark to show it's active
        "CE 366: Foundation Eng.",
        "CE 383: Structural Analysis"
    ]

    # The Selection Widget
    selection = st.sidebar.radio("Go to:", menu_options, label_visibility="collapsed")

    # --- ROUTER LOGIC ---
    
    # 1. Home Page
    if "Home" in selection:
        home_dashboard()

    # 2. Active Module (Soil Mechanics)
    elif "Soil Mechanics" in selection:
        # THIS IS WHERE WE LOAD YOUR SOIL CODE
        # Ensure your soil mechanics file is named 'topics/flow_water.py' or similar
        # and has a function called app(). 
        # For now, I will try to import it, or you can paste the code here.
        try:
            # Adjust this import to match your file name!
            from topics import flow_water 
            flow_water.app()
        except ImportError:
            st.error("⚠️ Error: Could not load Soil Mechanics module. Make sure the file exists.")

    # 3. Separators (If user clicks the dashed lines)
    elif "---" in selection:
        st.sidebar.warning("Please select a course below the header.")
        home_dashboard() # Default to home

    # 4. Under Construction Pages (Everything else)
    else:
        construction_page(selection)

    # --- SIDEBAR FOOTER ---
    st.sidebar.markdown("---")
    st.sidebar.caption("© 2026 MHF Civil Engineering")

if __name__ == "__main__":
    main()
