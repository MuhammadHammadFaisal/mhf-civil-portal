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
# MINIMAL ACADEMIC CSS
# ==================================================
st.markdown("""
<style>

/* Module Cards */
[data-testid="stPageLink-NavLink"] {
    background-color: #f8f9fa !important;
    border: 1px solid #dee2e6 !important;
    border-radius: 10px !important;
    padding: 18px !important;
    text-align: left !important;
    box-shadow: none !important;
    transition: background-color 0.15s ease !important;
}

[data-testid="stPageLink-NavLink"]:hover {
    background-color: #eef4f1 !important;
    border-color: #ced4da !important;
}

/* Module Title */
[data-testid="stPageLink-NavLink"] p {
    color: #212529 !important;
    font-size: 17px !important;
    font-weight: 600 !important;
    margin: 0 !important;
    line-height: 1.4 !important;
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

    # --------------------------------------------------
    # HEADER
    # --------------------------------------------------
    col_logo, col_text = st.columns([1, 3], vertical_alignment="center")

    with col_logo:
        st.image("assets/logo.png", use_container_width=True)

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

    # --------------------------------------------------
    # MODULES SECTION
    # --------------------------------------------------
    st.subheader("Course Modules")
    st.markdown("")

    modules = get_active_modules()

    if modules:
        cols = st.columns(3)

        for i, (file, title) in enumerate(modules):
            with cols[i % 3]:
                st.page_link(
                    f"pages/{file}",
                    label=title,
                    use_container_width=True
                )
                st.markdown(
                    "<div style='color:#666; font-size:13px; margin-top:-6px; margin-bottom:22px;'>"
                    
                    "</div>",
                    unsafe_allow_html=True
                )

    # --------------------------------------------------
    # PURPOSE / MISSION
    # --------------------------------------------------
    st.markdown("---")
    st.markdown("""
    ### Purpose

    MHF Civil provides transparent numerical solutions to standard civil engineering problems.
    Each module follows established theory, clearly states assumptions, and presents intermediate
    steps to support learning, verification, and exam preparation.
    """)

    # --------------------------------------------------
    # FEEDBACK
    # --------------------------------------------------
    st.markdown("---")
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
    st.markdown("---")
    st.subheader("About")

    st.markdown("""
    **Developed by Muhammad Hammad Faisal**  
    Final-Year Civil Engineering Student, Middle East Technical University (METU)
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

# ==================================================
if __name__ == "__main__":
    main()

