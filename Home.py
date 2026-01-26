import streamlit as st
import os

# ==================================================
# GLOBAL APP VERSION (CACHE BUSTING SOURCE OF TRUTH)
# ==================================================
APP_VERSION = "1.2.0"

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="MHF CIVIL CALC",
    page_icon="assets/logo.png",
    layout="wide"
)

# ==================================================
# CUSTOM CSS: PRO GREEN BUTTONS
# ==================================================
st.markdown("""
<style>
[data-testid="stPageLink-NavLink"] {
    background-color: #198754 !important;
    border: 2px solid #198754 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    text-align: center !important;
    box-shadow: 0 4px 6px rgba(0,0,0,0.2) !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
}

[data-testid="stPageLink-NavLink"]:hover {
    background-color: #146c43 !important;
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 12px rgba(20, 108, 67, 0.4) !important;
    border-color: #146c43 !important;
}

[data-testid="stPageLink-NavLink"] p {
    color: white !important;
    font-size: 16px !important;
    font-weight: 400 !important;
    line-height: 1.5 !important;
    margin: 0 !important;
    white-space: pre-wrap !important;
}

[data-testid="stPageLink-NavLink"] p::first-line {
    font-weight: 800 !important;
    font-size: 20px !important;
    line-height: 1.8 !important;
}
</style>
""", unsafe_allow_html=True)

# ==================================================
# MODULE DISCOVERY
# ==================================================
def get_active_modules():
    active_modules = []

    if os.path.exists("pages"):
        for f in os.listdir("pages"):
            if f.endswith(".py") and f != "__init__.py":
                try:
                    with open(os.path.join("pages", f), "r", encoding="utf-8") as file:
                        content = file.read()
                        if "Module Under Construction" not in content:
                            clean_name = (
                                f.replace(".py", "")
                                 .replace("_", " ")
                                 .replace("-", " ")
                            )
                            parts = clean_name.split(" ", 1)
                            if parts[0].isdigit():
                                clean_name = parts[1]
                            active_modules.append((f, clean_name.title()))
                except Exception:
                    pass

    return sorted(active_modules, key=lambda x: x[1])

# ==================================================
# MAIN APP
# ==================================================
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

    # --- DASHBOARD ---
    modules_list = get_active_modules()

    if modules_list:
        st.subheader("Active Course Calculators")

        cols = st.columns(4)
        for idx, (file_name, module_title) in enumerate(modules_list):
            with cols[idx % 2]:
                st.page_link(
                    f"pages/{file_name}",
                    label=f"{module_title}\nOnline & Verified",
                    use_container_width=True
                )

    # --- MISSION ---
    st.markdown("---")
    st.markdown("""
    ### Precision. Logic. Deterministic.

    MHF Civil is a focused engineering workspace built for **civil engineers who care about correctness**.
    No black-box guesses. No approximations without context.
    Just transparent, deterministic engineering calculations.
    """)

    # --- ABOUT ---
    st.markdown("---")
    st.subheader("About MHF Civil")

    st.markdown("""
    ### Muhammad Hammad Faisal  
    **Final Year Civil Engineering Student (METU)**  
    Founder — MHF Civil

    Engineering results should be **reproducible, transparent, and mathematically defensible**.
    """)

    st.link_button(
        "Connect on LinkedIn",
        "https://www.linkedin.com/in/muhammad-hammad-20059a229"
    )

    # --- FOOTER ---
    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center; color: #666; font-size: 12px;'>
        © 2026 MHF Civil. All rights reserved.<br>
        Version {APP_VERSION} · Ankara, Turkey
        </div>
        """,
        unsafe_allow_html=True
    )

# ==================================================
# ENTRY POINT
# ==================================================
if __name__ == "__main__":
    main()
