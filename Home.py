import streamlit as st
import os

# 1. PAGE CONFIG
st.set_page_config(
    page_title="MHF CIVIL CALC", 
    page_icon="assets/logo.png", 
    layout="wide"
)

def get_active_modules():
    """
    Scans 'pages/' directory for active modules.
    Returns a list of tuples: (filename, display_name)
    """
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
                            # Append tuple: (filename, Title Case Name)
                            active_modules.append((f, clean_name.title()))
                except Exception:
                    pass 
    return sorted(active_modules, key=lambda x: x[1])

def main():
    # --- HERO SECTION ---
    # Tight layout [1, 2] ratio with vertical centering
    try:
        col_logo, col_text = st.columns([1, 2], vertical_alignment="center")
    except TypeError:
        col_logo, col_text = st.columns([1, 2])

    with col_logo:
        st.image("assets/logo.png", use_container_width=True) 

    with col_text:
        # Pushes text slightly down to align with logo center
        st.markdown(
            """
            <div style="padding-top: 10px; padding-left: 10px;">
                <h1 style='font-size: 55px; margin-bottom: 0px; line-height: 1.1;'>MHF Civil Calc</h1>
                <p style='color: #666; font-size: 20px; font-weight: 300; margin-top: 8px;'>
                    Deterministic Civil Engineering Computation Platform
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )

    st.markdown("---")
    
    # --- AUTOMATIC DASHBOARD (UPDATED) ---
    modules_list = get_active_modules()

    if modules_list:
        st.subheader("Active Course Calculators")
        cols = st.columns(2)
        
        # We iterate through (filename, title) tuples
        for index, (file_name, module_title) in enumerate(modules_list):
            with cols[index % 2]:
                with st.container(border=True):
                    
                    # 1. Module Title
                    st.markdown(f"### {module_title}")
                    
                    # 2. Professional "Online" Badge (Green Pill Style)
                    # This HTML creates a subtle green background with dark green text
                    st.markdown(
                        """
                        <div style="margin-bottom: 15px;">
                            <span style='background-color: #d1e7dd; color: #0f5132; padding: 4px 10px; border-radius: 15px; font-size: 12px; font-weight: 600; letter-spacing: 0.5px;'>
                                ✅ ONLINE & VERIFIED
                            </span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # 3. Clickable Redirect Button
                    # This creates a full-width button that links to the page
                    st.page_link(
                        f"pages/{file_name}", 
                        label="Launch Calculator", 
                        icon="🚀", 
                        use_container_width=True
                    )
    
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
