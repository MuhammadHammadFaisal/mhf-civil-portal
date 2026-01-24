import streamlit as st
import os

# 1. PAGE CONFIG
st.set_page_config(
    page_title="MHF Civil Portal", 
    page_icon="assets/logo.png", 
    layout="wide"
)

def get_active_modules():
    """
    Scans 'pages/' directory.
    excludes any file containing 'Module Under Construction'.
    """
    active_modules = []
    
    if os.path.exists("pages"):
        files = os.listdir("pages")
        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                try:
                    # Open the file and check for the "Under Construction" flag
                    with open(os.path.join("pages", f), "r", encoding="utf-8") as file_content:
                        content = file_content.read()
                        
                        # IF the file does NOT contain this phrase, add it to the list
                        if "Module Under Construction" not in content:
                            # Clean the name: "soil_mechanics.py" -> "Soil Mechanics"
                            clean_name = f.replace(".py", "").replace("_", " ").replace("-", " ")
                            # Remove leading numbers if present (e.g., "01 ")
                            parts = clean_name.split(" ", 1)
                            if parts[0].isdigit():
                                clean_name = parts[1]
                            
                            active_modules.append(clean_name.title())
                except Exception:
                    pass # Skip if file can't be read

    return sorted(active_modules)

def main():
    # --- SIDEBAR LOGO ---
    with st.sidebar:
        st.image("assets/logo.png", use_container_width=True)
        st.markdown("---") 
    
    # --- HEADER ---
    st.markdown("# MHF Civil Portal")
    st.caption("Deterministic Civil Engineering Computation Platform")
    st.markdown("---")
    
    # --- AUTOMATIC DASHBOARD ---
    # Only shows completed modules
    available_modules = get_active_modules()

    if available_modules:
        st.subheader("🚀 Active Workspaces")
        cols = st.columns(2)
        for index, module_name in enumerate(available_modules):
            with cols[index % 2]:
                with st.container(border=True):
                    st.markdown(f"**{module_name}**")
                    st.caption("✅ Online & Verified")
    
    # (Note: If no modules are ready, this section effectively hides itself or shows nothing, which is cleaner)

    # --- MISSION STATEMENT ---
    st.markdown("---")
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
