import streamlit as st
import os
import base64

# 1. PAGE CONFIG
st.set_page_config(
    page_title="MHF Civil Portal", 
    page_icon="assets/logo.png", 
    layout="wide"
)

# --- HELPER: CONVERT IMAGE TO BASE64 ---
# This ensures the image loads even when using custom HTML
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

# --- GET ACTIVE MODULES FUNCTION ---
def get_active_modules():
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
    # 1. LOAD THE LOGO AS BASE64
    logo_path = "assets/logo.png"
    logo_base64 = get_base64_of_bin_file(logo_path)

    # 2. INJECT CSS & LOGO HTML
    # We inject the image directly into the sidebar using HTML, not st.image
    if logo_base64:
        st.markdown(
            f"""
            <style>
                /* Push the default navigation down */
                [data-testid="stSidebarNav"] {{
                    padding-top: 200px; /* Adjust this if logo is taller/shorter */
                }}
                
                /* Create a container for the logo */
                .sidebar-logo-container {{
                    position: absolute;
                    top: 20px;
                    left: 20px;
                    width: 260px; /* Adjust width to fit sidebar */
                    z-index: 999;
                }}
            </style>
            
            <div data-testid="stSidebar" class="css-1d391kg">
                <div class="sidebar-logo-container">
                    <img src="data:image/png;base64,{logo_base64}" width="100%">
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.error(f"⚠️ Could not find logo at {logo_path}")

    # --- MAIN PAGE CONTENT ---
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
                    st.caption("✅ Online & Verified")
    
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
