import streamlit as st
import os

# 1. PAGE CONFIG
st.set_page_config(
    page_title="MHF CIVIL CALC", 
    page_icon="assets/logo.png", 
    layout="wide"
)

# --- CUSTOM CSS: PRO GREEN BUTTONS ---
st.markdown("""
<style>
/* 1. The Button Container (Green Box) */
[data-testid="stPageLink-NavLink"] {
    background-color: #198754 !important;   /* Solid Green */
    border: 2px solid #198754 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    text-align: center !important;          /* FORCE CENTER ALIGNMENT */
    box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}

/* 2. Hover Effect */
[data-testid="stPageLink-NavLink"]:hover {
    background-color: #146c43 !important;   /* Darker Green */
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 12px rgba(20, 108, 67, 0.4) !important;
    border-color: #146c43 !important;
}

/* 3. Text Styling - Base Settings (Normal Weight) */
[data-testid="stPageLink-NavLink"] p {
    color: white !important;
    font-size: 16px !important;
    font-weight: 400 !important;      /* UNBOLD EVERYTHING by default */
    line-height: 1.5 !important;
    margin: 0 !important;
    white-space: pre-wrap !important; /* Respect new lines */
}

/* 4. TITLE STYLING (First Line Only) */
/* This makes "Soil Mechanics" Bold and Big, while "Online" stays normal */
[data-testid="stPageLink-NavLink"] p::first-line {
    font-weight: 800 !important;      /* BOLD Title */
    font-size: 20px !important;       /* LARGER Title */
    line-height: 1.8 !important;      /* More space below title */
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
        
        cols = st.columns(4)
        
        for index, (file_name, module_title) in enumerate(modules_list):
            with cols[index % 2]:
                # The \n creates the line break.
                # CSS ::first-line handles the bolding of the top part.
                st.page_link(
                    f"pages/{file_name}", 
                    label=f"{module_title}\n Beta Release \n (Validation Pending)", 
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
# --- FEEDBACK SECTION ---
    with st.expander("💬 Feedback & Support"):
        st.write("Encountered a calculation error, found a bug, or have a suggestion? Help improve MHF Civil.")
        
        # Single option layout
        st.info("**Submit Feedback & Bug Reports**")
        st.caption("Use the form below to report issues, request new features, or share your thoughts.")
        
        # Replace the link below with your actual Google Form link
        st.link_button(
            "Open Feedback Form", 
            "https://docs.google.com/forms/d/e/1FAIpQLSfKtE2MK_2JZxEK4SzyjEhjdb8PKEC8-dN5az82MaIoPZzMsg/viewform?usp=header", 
            use_container_width=True
        )
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







