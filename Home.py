import streamlit as st
import os

# ==================================================
# PAGE CONFIGURATION
# ==================================================
st.set_page_config(
    page_title="MHF Civil Calc",
    page_icon="assets/logo.png",
    layout="wide"
)

# ==================================================
# CUSTOM CSS (Updated)
# ==================================================
st.markdown("""
<style>

/* --- 1. CARD CONTAINER --- */
[data-testid="stPageLink-NavLink"] {
    background-color: #f8f9fa !important;
    border: 1px solid #dee2e6 !important;
    border-radius: 10px !important;
    padding: 18px !important;
    box-shadow: none !important;
    transition: background-color 0.15s ease !important;
    
    /* Flexbox settings to center everything */
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}

/* Hover Effect */
[data-testid="stPageLink-NavLink"]:hover {
    background-color: #eef4f1 !important;
    border-color: #ced4da !important;
}

/* --- 2. TEXT STYLING --- */
[data-testid="stPageLink-NavLink"] p {
    color: #212529 !important;
    font-size: 17px !important;
    font-weight: 600 !important;
    margin: 0 !important;
    line-height: 1.4 !important;
    
    /* Force text to center */
    text-align: center !important;
    width: 100% !important;
}

/* --- 3. HIDE THE ICON/ARROW ON LINKS --- */
[data-testid="stPageLink-NavLink"] svg {
    display: none !important;
}

/* --- 4. EXPANDER / DROPDOWN STYLING --- */
/* Style the outer box of the expander */
[data-testid="stExpander"] details {
    background-color: #f8f9fa !important;  /* Match Card Color */
    border: 1px solid #dee2e6 !important;  /* Match Card Border */
    border-radius: 10px !important;        /* Rounded Corners */
    color: #212529 !important;             /* Dark Text Color */
}

/* Style the clickable header (Summary) */
[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: #212529 !important;
    padding: 15px !important;              /* Add padding */
}

/* Hover effect for the expander */
[data-testid="stExpander"] summary:hover {
    background-color: #eef4f1 !important;
    color: #000 !important;
    border-radius: 10px !important;
}

/* Fix the content inside the expander */
[data-testid="stExpander"] div[role="group"] {
    padding: 15px !important;
    color: #212529 !important;             /* Ensure text inside is readable */
}

/* Make the SVG arrow in the expander dark so it's visible on light bg */
[data-testid="stExpander"] svg {
    fill: #212529 !important;
}

</style>
""", unsafe_allow_html=True)

# ==================================================
# SCAN ACTIVE MODULES
# ==================================================
def get_active_modules():
    modules = []
    if os.path.exists("pages"):
        for file in os.listdir("pages"):
            if file.endswith(".py") and file != "__init__.py":
                try:
                    with open(os.path.join("pages", file), "r", encoding="utf-8") as f:
                        content = f.read()
                        if "Module Under Construction" not in content:
                            name = file.replace(".py", "").replace("_", " ").replace("-", " ")
                            parts = name.split(" ", 1)
                            if parts[0].isdigit():
                                name = parts[1]
                            modules.append((file, name.title()))
                except Exception:
                    pass
    return sorted(modules, key=lambda x: x[1])

# ==================================================
# MAIN APPLICATION
# ==================================================
def main():
    col_logo, col_text = st.columns([1, 3], vertical_alignment="center")

    with col_logo:
        # Comment this out if you don't have the image file yet
        # st.image("assets/logo.png", use_container_width=True)
        st.write("") 

    with col_text:
        st.markdown("""
        <h1 style="font-size:46px; margin-bottom:6px;">MHF Civil Calc</h1>
        <p style="color:#555; font-size:18px; line-height:1.5; max-width:700px;">
            Civil Engineering Calculation Workspace
        </p>
        <p style="color:#777; font-size:14px; max-width:700px;">
            Verified numerical solvers aligned with standard undergraduate civil engineering coursework.
        </p>
        """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("") 

    # --------------------------------------------------
    # MODULES
    # --------------------------------------------------
    st.subheader("Course Modules")
    st.markdown("")

    modules = get_active_modules()

    if modules:
        cols = st.columns(3)
        for i, (file, title) in enumerate(modules):
            with cols[i % 3]:
                st.page_link(f"pages/{file}", label=title, use_container_width=True)
                st.markdown("") 

    # --------------------------------------------------
    # PURPOSE
    # --------------------------------------------------
    st.markdown("")
    st.markdown("")
    
    st.markdown("""
    ### Purpose
    MHF Civil provides transparent numerical solutions to standard civil engineering problems.
    Each module follows established theory, clearly states assumptions, and presents intermediate
    steps to support learning, verification, and exam preparation.
    """)

    # --------------------------------------------------
    # FEEDBACK (The Dropdown)
    # --------------------------------------------------
    st.markdown("")
    st.markdown("")

    # This expander will now look like a card
    with st.expander("Report an Issue or Suggest an Improvement"):
        st.write(
            "If you identify an incorrect result, unclear assumption, or missing topic, "
            "your feedback helps improve the reliability of this platform."
        )
        st.link_button(
            "Open Feedback Form",
            "https://docs.google.com/forms/d/e/1FAIpQLSfKtE2MK_2JZxEK4SzyjEhjdb8PKEC8-dN5az82MaIoPZzMsg/viewform",
            use_container_width=True
        )

    # --------------------------------------------------
    # ABOUT
    # --------------------------------------------------
    st.markdown("")
    st.markdown("")
    
    st.subheader("About")

    st.markdown("""
    **Developed by Muhammad Hammad Faisal** Final-Year Civil Engineering Student, Middle East Technical University (METU)
    """)

    st.link_button(
        "LinkedIn Profile",
        "https://www.linkedin.com/in/muhammad-hammad-20059a229"
    )

    # --------------------------------------------------
    # FOOTER
    # --------------------------------------------------
    st.markdown("---") 
    st.markdown("""
    <div style="text-align:center; color:#777; font-size:12px;">
        © 2026 MHF Civil · Version 1.2.0 · Ankara, Turkey
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
