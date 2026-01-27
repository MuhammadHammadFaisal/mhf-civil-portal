import streamlit as st
import os

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="MHF CIVIL CALC",
    page_icon="assets/logo.png",
    layout="wide"
)

# --------------------------------------------------
# CUSTOM CSS
# --------------------------------------------------
st.markdown("""
<style>

/* NAV BUTTON STYLE */
[data-testid="stPageLink-NavLink"] {
    background-color: #198754 !important;
    border: 2px solid #198754 !important;
    border-radius: 12px !important;
    padding: 18px !important;
    text-align: center !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.15) !important;
    transition: all 0.2s ease !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}

[data-testid="stPageLink-NavLink"]:hover {
    background-color: #146c43 !important;
    transform: translateY(-3px) !important;
    box-shadow: 0 10px 16px rgba(20, 108, 67, 0.35) !important;
    border-color: #146c43 !important;
}

/* BUTTON TEXT */
[data-testid="stPageLink-NavLink"] p {
    color: white !important;
    font-size: 16px !important;
    font-weight: 400 !important;
    line-height: 1.5 !important;
    margin: 0 !important;
}

/* FIRST LINE = TITLE */
[data-testid="stPageLink-NavLink"] p::first-line {
    font-weight: 800 !important;
    font-size: 20px !important;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# MODULE SCANNER
# --------------------------------------------------
def get_active_modules():
    active_modules = []

    if os.path.exists("pages"):
        for f in os.listdir("pages"):
            if f.endswith(".py") and f != "__init__.py":
                try:
                    with open(os.path.join("pages", f), "r", encoding="utf-8") as file:
                        content = file.read()
                        if "Module Under Construction" not in content:
                            name = f.replace(".py", "").replace("_", " ").replace("-", " ")
                            parts = name.split(" ", 1)
                            if parts[0].isdigit():
                                name = parts[1]
                            active_modules.append((f, name.title()))
                except Exception:
                    pass

    return sorted(active_modules, key=lambda x: x[1])

# --------------------------------------------------
# MAIN APP
# --------------------------------------------------
def main():

    # HERO
    col_logo, col_text = st.columns([1, 2], vertical_alignment="center")

    with col_logo:
        st.image("assets/logo.png", use_container_width=True)

    with col_text:
        st.markdown("""
        <div style="padding-top:10px;">
            <h1 style="font-size:52px; margin-bottom:4px;">MHF Civil Calc</h1>
            <p style="color:#666; font-size:19px; font-weight:300; line-height:1.5;">
                Deterministic, theory-based civil engineering calculations —
                designed for students who value correctness over guesswork.
            </p>
            <p style="color:#999; font-size:14px; margin-top:6px;">
                No AI approximations · No black-box results · Fully reproducible
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("")

    # MODULE DASHBOARD
    modules = get_active_modules()

    if modules:
        st.subheader("Available Course Calculators")
        st.markdown("")

        cols = st.columns(4)

        for i, (file, title) in enumerate(modules):
            with cols[i % 4]:
                st.page_link(
                    f"pages/{file}",
                    label=title,
                    use_container_width=True
                )
                st.markdown(
                    "<div style='text-align:center; color:#888; font-size:12px; margin-top:-8px; margin-bottom:24px;'>"
                    "Deterministic · Theory-Based</div>",
                    unsafe_allow_html=True
                )

    # MISSION
    st.markdown("---")
    st.markdown("""
    ### Precision · Logic · Determinism

    MHF Civil is built to ensure students obtain **correct civil engineering solutions**.
    Every calculator follows standard theory, explicitly states assumptions,
    and produces results that can be verified—unlike probabilistic AI outputs
    that may appear confident but be technically incorrect.
    """)

    # FEEDBACK
    st.markdown("---")
    with st.expander("Report an Issue / Suggest an Improvement"):
        st.write("Help improve calculation accuracy, report bugs, or request new modules.")
        st.link_button(
            "Open Feedback Form",
            "https://docs.google.com/forms/d/e/1FAIpQLSfKtE2MK_2JZxEK4SzyjEhjdb8PKEC8-dN5az82MaIoPZzMsg/viewform",
            use_container_width=True
        )

    # ABOUT
    st.markdown("---")
    st.subheader("About")
    st.markdown("""
    **Developed by Muhammad Hammad Faisal**  
    Final-Year Civil Engineering Student — METU
    """)

    st.link_button(
        "Connect on LinkedIn",
        "https://www.linkedin.com/in/muhammad-hammad-20059a229"
    )

    # FOOTER
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; color:#777; font-size:12px;">
        © 2026 MHF Civil · Version 1.2.0 · Ankara, Turkey
    </div>
    """, unsafe_allow_html=True)

# --------------------------------------------------
if __name__ == "__main__":
    main()
