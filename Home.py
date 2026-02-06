import streamlit as st
import os
from PIL import Image

# Helper function to make image square and resize
def prepare_icon(im, final_size=64):
    x, y = im.size
    size = max(x, y)

    # Create square transparent canvas
    new_im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    new_im.paste(im, ((size - x) // 2, (size - y) // 2))

    # Resize to favicon friendly size
    new_im = new_im.resize((final_size, final_size), Image.LANCZOS)

    return new_im


# Load and fix the image
try:
    icon_img = Image.open("assets/Sticker.png").convert("RGBA")
    icon_img = prepare_icon(icon_img, 64)   # <-- IMPORTANT
except:
    icon_img = "📊"   # fallback emoji


# =========================================================
# APP CONFIG
# =========================================================
st.set_page_config(
    page_title="MHF Soil Mechanics",
    layout="wide",
    page_icon=icon_img
)



# ==================================================
# CUSTOM CSS
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

/* --- 2. TEXT STYLING INSIDE CARDS --- */
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

/* --- 3. HIDE ICONS --- */
/* Hide the arrow icon inside the card links */
[data-testid="stPageLink-NavLink"] svg {
    display: none !important;
}

/* Hide the small chain/link icon next to Headers (Purpose, About, etc.) */
[data-testid="stHeaderAction"] {
    display: none !important;
}

/* --- 4. GENERAL LINK BUTTON STYLING --- */
[data-testid="stLinkButton"] > a {
    border-radius: 8px !important;
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
        st.image("assets/Sticker.png", use_container_width=True)

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

        for idx, (file, title) in enumerate(modules):
            with cols[idx % 3]:
                st.page_link(
                    f"pages/{file}",
                    label=title,
                    use_container_width=True
                )
                st.markdown("") 

    # --------------------------------------------------
    # PURPOSE
    # --------------------------------------------------

    st.markdown("")
    
    st.subheader("Purpose")

    st.markdown("""
    MHF Civil provides transparent numerical solutions to standard civil engineering problems.
    Each module follows established theory, clearly states assumptions, and presents intermediate
    steps to support learning, verification, and exam preparation.
    """)

    # --------------------------------------------------
    # FEEDBACK (Header format)
    # --------------------------------------------------
  
    st.markdown("")

    st.subheader("Feedback")

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
    
    st.subheader("About")

    st.markdown("""
    **Developed by Muhammad Hammad Faisal**  
    Final-Year Civil Engineering Student, METU
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
        © 2026 MHF Civil · Ankara, Turkey
    </div>
    """, unsafe_allow_html=True)

# ==================================================
if __name__ == "__main__":
    main()








