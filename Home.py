import streamlit as st
import os

# 1. PAGE CONFIG
st.set_page_config(
    page_title="MHF CIVIL CALC", 
    page_icon="assets/logo.png", 
    layout="wide"
)

# --- CUSTOM CSS FOR GREEN CLICKABLE CARDS ---
st.markdown("""
<style>
/* 1. Target the Page Link Card */
div[data-testid="stPageLink-NavLink"] {
    background-color: #F0FDF4;   /* Light Green Background */
    border: 1px solid #22c55e;   /* Green Border */
    border-radius: 12px;         /* Rounded Corners */
    padding: 15px 20px;          /* Padding */
    transition: all 0.3s ease;   /* Smooth Animation */
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

/* 2. Hover Effect (Darker Green + Lift) */
div[data-testid="stPageLink-NavLink"]:hover {
    background-color: #DCFCE7;   /* Slightly Darker Green */
    transform: translateY(-2px); /* Lift Up */
    border-color: #16a34a;       /* Darker Border */
    box-shadow: 0 6px 12px rgba(34, 197, 94, 0.2);
}

/* 3. Force Text Color to Dark Green */
div[data-testid="stPageLink-NavLink"] * {
    color: #14532d !important;   /* Dark Green Text */
    font-weight: 600 !important;
    text-decoration: none !important;
}
</style>
""", unsafe_allow_html=True)

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
                            active_modules.append((f, clean_name.title()))
                except Exception:
                    pass 
    return sorted(active_modules, key=lambda x: x[1])

def main():
    # --- HERO SECTION ---
    try:
        col_logo, col_text = st.columns([1, 2], vertical_alignment="center")
    except TypeError:
        col_logo, col_text = st.columns([1, 2])

    with col_logo:
        st.image("assets/logo.png", use_container_width=True) 

    with col_text:
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
    
    # --- AUTOMATIC DASHBOARD ---
    modules_list = get_active_modules()

    if modules_list:
        st.subheader("Active Course Calculators")
        
        cols = st.columns(2)
        
        for index, (file_name, module_title) in enumerate(modules_list):
            with cols[index % 2]:
                # FIXED: Removed 'icon=""' to prevent the crash
                st.page_link(
                    f"pages/{file_name}", 
                    label=f"{module_title}\n✅ Online & Verified", 
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
