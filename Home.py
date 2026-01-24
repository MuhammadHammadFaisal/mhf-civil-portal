import streamlit as st
import os

# 1. PAGE CONFIG
st.set_page_config(
    page_title="MHF CIVIL CALC", 
    page_icon="assets/logo.png", 
    layout="wide"
)

def get_active_modules():
    """Scans 'pages/' directory for active modules."""
    active_modules = []
    if os.path.exists("pages"):
        files = os.listdir("pages")
        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                try:
                    with open(os.path.join("pages", f), "r", encoding="utf-8") as file_content:
                        content = file_content.read()
                        if "Module Under Construction" not in content:
                            clean_name = f.replace(".py", "").replace("_", " ").replace("-", " ")
                            parts = clean_name.split(" ", 1)
                            if parts[0].isdigit():
                                clean_name = parts[1]
                            active_modules.append(clean_name.title())
                except Exception:
                    pass 
    return sorted(active_modules)

def main():
    # --- [NEW] MAIN PAGE LOGO ---
    # This places the logo at the very top of your content
    col1, col2 = st.columns([1, 4]) # Create columns to control logo size/position
    with col1:
        st.image("assets/logo.png", width=250) # <--- Adjust width here if needed
    
    # --- HEADER ---
    st.markdown("# MHF Civil Portal")
    st.caption("Deterministic Civil Engineering Computation Platform")
    st.markdown("---")
    
    # --- AUTOMATIC DASHBOARD ---
    available_modules = get_active_modules()

    if available_modules:
        st.subheader("Active Course Calculator")
        cols = st.columns(2)
        for index, module_name in enumerate(available_modules):
            with cols[index % 2]:
                with st.container(border=True):
                    st.markdown(f"**{module_name}**")
                    st.caption("Online & Verified")
    
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
