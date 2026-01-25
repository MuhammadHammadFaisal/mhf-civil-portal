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
    # --- HERO SECTION ---
    # FIX: Use a ratio [1, 3] instead of fixed pixels. 
    # This gives the logo 25% of the width and text 75%, allowing natural scaling.
    col_logo, col_text = st.columns([1, 3])

    with col_logo:
        # FIX: use_container_width=True lets the browser handle sharpness
        st.image("assets/logo.png", use_container_width=True) 

    with col_text:
        # Aligned visually with the logo center
        st.markdown(
            """
            <div style='display: flex; flex-direction: column; justify-content: center; height: 100%;'>
                <h1 style='margin-bottom: 0px; font-size: 48px;'>MHF Civil Calc</h1>
                <p style='color: #888; font-size: 20px; font-weight: 300; margin-top: 5px;'>
                    Deterministic Civil Engineering Computation Platform
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )

    st.markdown("---")
    
    # --- AUTOMATIC DASHBOARD ---
    available_modules = get_active_modules()

    if available_modules:
        st.subheader("Active Course Calculators")
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
    **Engineering results should be reproducible, transparent, and mathematically defensible.**
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
