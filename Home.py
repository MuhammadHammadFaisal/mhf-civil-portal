import streamlit as st
import os  # <--- [NEW] Needed to scan folders

# 1. PAGE CONFIG
st.set_page_config(
    page_title="MHF Civil Portal", 
    page_icon="assets/logo.png", 
    layout="wide"
)

def get_active_modules():
    """Scans the 'pages' directory to find active files"""
    modules = []
    # Check if pages folder exists
    if os.path.exists("pages"):
        files = os.listdir("pages")
        for f in files:
            # We only want Python files, but not __init__.py
            if f.endswith(".py") and f != "__init__.py":
                # Clean the name: "01_Soil_Mechanics.py" -> "Soil Mechanics"
                clean_name = f.replace(".py", "").replace("_", " ").replace("-", " ")
                
                # Optional: Remove sorting numbers (like "01 " or "1.")
                parts = clean_name.split(" ", 1)
                if parts[0].isdigit():
                    clean_name = parts[1]
                    
                modules.append(clean_name.title()) # Make it Capital Case
    return sorted(modules)

def main():
    # --- SIDEBAR LOGO ---
    with st.sidebar:
        st.image("assets/logo.png", use_container_width=True)
        st.markdown("---") 
    
    # --- HEADER ---
    st.markdown("# MHF Civil Portal")
    st.caption("Deterministic Civil Engineering Computation Platform")
    st.markdown("---")
    
    # --- [NEW SECTION] AUTOMATIC MODULE CHECKER ---
    st.subheader("🚀 Active Workspaces")
    
    # Run the scanner
    available_modules = get_active_modules()

    if available_modules:
        # Create a grid layout (2 cards per row)
        cols = st.columns(2)
        for index, module_name in enumerate(available_modules):
            # The % 2 logic alternates between column 1 and column 2
            with cols[index % 2]:
                with st.container(border=True):
                    st.markdown(f"**{module_name}**")
                    st.caption("✅ Module Online")
    else:
        st.warning("No modules found in the 'pages/' folder yet.")
        
    st.markdown("---")

    # --- MISSION STATEMENT ---
    st.markdown("""
    ### Precision. Logic. Deterministic.
    
    MHF Civil is a focused engineering workspace built for **civil engineers who care about correctness**.
    No black-box guesses. No approximations without context.
    Just transparent, deterministic engineering calculations.
    """)
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

    st.link_button("Connect on LinkedIn", "https://www.linkedin.com/in/muhammad-hammad-20059a229")
    
    # --- FOOTER ---
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 12px;'>
        © 2026 MHF Civil. All rights reserved.<br>
        Version 1.2.0 · Ankara, Turkey
        </div>
        """, 
        unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()
