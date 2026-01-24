import streamlit as st
import os
import base64

# 1. PAGE CONFIG
st.set_page_config(
    page_title="MHF Civil Portal", 
    page_icon="assets/logo.png", 
    layout="wide"
)

# --- HELPER: CONVERT IMAGE TO CODE ---
# This allows us to paint the logo into the CSS background
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

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
    # --- [FIX] LOGO AT THE TOP ---
    # We convert the image to text and inject it into the sidebar's CSS
    logo_file = "assets/logo.png"
    img_base64 = get_base64_of_bin_file(logo_file)

    if img_base64:
        st.markdown(
            f"""
            <style>
            /* 1. Target the sidebar navigation block */
            [data-testid="stSidebarNav"] {{
                background-image: url("data:image/png;base64,{img_base64}");
                background-repeat: no-repeat;
                background-position: 20px 20px; /* 20px from top/left */
                background-size: 280px auto;    /* Adjust width to fit */
                padding-top: 160px;             /* Push the links down */
            }}
            /* 2. Hide the default Streamlit anchor at top (optional) */
            [data-testid="stSidebarNav"]::before {{
                content: "";
                margin-top: 20px;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )

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
