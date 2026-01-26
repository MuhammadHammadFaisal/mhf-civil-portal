import streamlit as st
import os

# --- 1. CONFIG MUST BE FIRST ---
st.set_page_config(
    page_title="MHF CIVIL CALC", 
    page_icon="assets/logo.png", 
    layout="wide"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
[data-testid="stPageLink-NavLink"] {
    background-color: #198754 !important;
    border: 2px solid #198754 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    text-align: center !important;
    color: white !important;
    text-decoration: none !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease !important;
}
[data-testid="stPageLink-NavLink"]:hover {
    background-color: #146c43 !important;
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 12px rgba(20, 108, 67, 0.4) !important;
    border-color: #146c43 !important;
}
[data-testid="stPageLink-NavLink"] p {
    color: white !important;
    font-size: 18px !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)

def get_active_modules():
    active_modules = []
    if os.path.exists("pages"):
        files = os.listdir("pages")
        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                clean_name = f.replace(".py", "").replace("_", " ").title()
                # Remove sorting numbers if present (e.g. "06 ")
                parts = clean_name.split(" ", 1)
                if parts[0].isdigit(): clean_name = parts[1]
                active_modules.append((f, clean_name))
    return sorted(active_modules, key=lambda x: x[1])

def main():
    try:
        c1, c2 = st.columns([1, 2], vertical_alignment="center")
    except:
        c1, c2 = st.columns([1, 2])
        
    with c1:
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", use_container_width=True)
        else:
            st.info("ℹ️ Add 'logo.png' to assets folder")

    with c2:
        st.markdown("""
            <div style="padding-left: 10px;">
                <h1 style='font-size: 50px; margin: 0; line-height: 1.1;'>MHF Civil Calc</h1>
                <p style='color: #666; font-size: 20px; font-weight: 300;'>
                    Deterministic Civil Engineering Platform
                </p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    
    modules = get_active_modules()
    if modules:
        st.subheader("Active Modules")
        cols = st.columns(2)
        for idx, (fname, mname) in enumerate(modules):
            with cols[idx % 2]:
                st.page_link(f"pages/{fname}", label=f"{mname}\n✅ Verified", use_container_width=True)

if __name__ == "__main__":
    main()
