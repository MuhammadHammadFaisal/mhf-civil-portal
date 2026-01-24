import streamlit as st

# Import your existing module
# Note: Ensure your soil mechanics file is named 'soil_mechanics.py' in the same folder 
# OR inside a folder named 'pages' or 'modules'. 
# If it is inside pages/01_Soil... you might need to adjust the import or just paste the logic here.
# For this example, I assume you will paste your Soil Logic where indicated.

def construction_page(course_name):
    """The professional placeholder for missing modules"""
    st.title(f"🚧 {course_name}")
    st.warning("This module is currently under active development.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://img.freepik.com/free-vector/under-construction-warning-sign-vector_53876-166418.jpg?w=740", width=150)
    with col2:
        st.write(f"**Status:** Planned for Q4 2026")
        st.write(f"**Developer:** Hammad (METU)")
        st.progress(0.1, text="Development Progress: 10%")
        st.info("Priority is given to CE363 (Soil Mechanics). Check back later for updates.")

def main():
    st.set_page_config(page_title="MHF Civil Portal", page_icon="🏗️", layout="wide")

    # --- SIDEBAR NAVIGATION TREE ---
    st.sidebar.title("🏗️ MHF Civil Portal")
    st.sidebar.caption("Deterministic Engineering Calculator")
    st.sidebar.markdown("---")

    # 1. Select Year Level
    year_level = st.sidebar.selectbox(
        "Select Year Level:",
        ["2nd Year (Sophomore)", "3rd Year (Junior)", "4th Year (Senior)"]
    )

    # 2. Dynamic Course List based on Year (METU Curriculum)
    if "2nd Year" in year_level:
        course = st.sidebar.radio(
            "Select Course:",
            [
                "🔒 CE 221: Statics",
                "🔒 CE 224: Strength of Materials",
                "🔒 CE 241: Materials Science",
                "🔒 CE 282: Fluid Mechanics"
            ]
        )
    
    elif "3rd Year" in year_level:
        course = st.sidebar.radio(
            "Select Course:",
            [
                "✅ CE 363: Soil Mechanics",  # <--- The only active one
                "🔒 CE 305: Hydromechanics",
                "🔒 CE 353: Transportation Eng.",
                "🔒 CE 366: Foundation Eng.",
                "🔒 CE 383: Structural Analysis"
            ]
        )
        
    else: # 4th Year
        course = st.sidebar.radio(
            "Select Course:",
            [
                "🔒 CE 4XX: Capstone Design",
                "🔒 CE 4XX: Electives"
            ]
        )

    # --- MAIN PAGE ROUTER ---
    
    if "Soil Mechanics" in course:
        # === LOAD YOUR ACTIVE MODULE HERE ===
        # You can import your soil_mechanics.app() here
        # Or paste the Soil Mechanics code block directly here.
        import pages.Soil_Mechanics as sm  # Example import if using pages folder
        sm.app() # Assuming your soil file has an app() function
        
    else:
        # === LOAD CONSTRUCTION PAGE ===
        construction_page(course)

if __name__ == "__main__":
    main()
