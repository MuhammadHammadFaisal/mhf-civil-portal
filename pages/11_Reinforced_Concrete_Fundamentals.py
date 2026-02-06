import streamlit as st
# IMPORT MODULES
from topics.concrete import axial_analysis
from topics.concrete import axial_design
from topics.concrete import bending_analysis
from topics.concrete import bending_design
from topics.concrete import combined_analysis
from topics.concrete import combined_design
from topics.concrete import shear_design

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
    icon_img = ""   # fallback emoji


# =========================================================
# APP CONFIG
# =========================================================
st.set_page_config(
    page_title="MHF Reinforced Concrete Fundamentals",
    layout="wide",
    page_icon=icon_img
)


def app():
    # CUSTOM CSS
    st.markdown("""
    <style>
    /* Main dropdown box */
    div[data-baseweb="select"] > div {
        background-color: #3b3f4d !important;
        border: 2px solid #5a5f70 !important; 
        color: white !important;
        border-radius: 8px !important;
    }

   /* Dropdown menu background */
    ul[data-baseweb="menu"] {
        background-color: #262730 !important;
        border: 1px solid #5a5f70 !important;
        padding: 10px !important;
    }

    /* Menu options */
    li[data-baseweb="option"] {
        color: white !important;
    }

    /* Hover state */
    li[data-baseweb="option"]:hover {
        background-color: #ff4b4b !important;
        color: white !important;
    }
    
    /* Fix the Arrow Icon color */
    div[data-baseweb="select"] span {
        color: white !important;
    }
    
    /* Fix the Arrow Icon color */
    div[data-baseweb="select"] svg {
        fill: white !important;
    }

    /* Image Styling */
    div[data-testid="stImage"] > img {
        border-radius: 15px;
        border: 2px solid #444;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

    # --- PROFESSIONAL HEADER SECTION ---
    # Adjusted column ratio to give the bigger logo enough space
    col_logo, col_text = st.columns([1, 5], vertical_alignment="center")

    with col_logo:
        # Increased logo width slightly to make it "a little big"
        st.image("assets/logo.png")

    with col_text:
        # Font size set to 55px (Professional look: smaller than logo, but distinct)
        st.markdown(
            """
            <div style="padding-left: 15px;">
                <h1 style='font-size: 55px; margin: 0; line-height: 1.0; font-weight: 700;'>Reinforced Concrete Fundamentals</h1>
            </div>
            """, 
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)

    # --- TOPIC SELECTION MENU ---
    topic = st.selectbox(
        "Select Calculation Module:", 
        [
            "Analysis of Axial Load",
            "Design of Axial Members",
            "Analysis of Bending (Flexure)",
            "Design of Bending (Flexure)",
            "Analysis of Combined Loading",
            "Design of Combined Loading",
            "Shear Design"
        ]
    )

    # --- ROUTING LOGIC ---
    if topic == "Analysis of Axial Load":
        axial_analysis.app()

    elif topic == "Design of Axial Members":
        axial_design.app()

    elif topic == "Analysis of Bending (Flexure)":
        bending_analysis.app()
        
    elif topic == "Design of Bending (Flexure)":
        bending_design.app()
        
    elif topic == "Analysis of Combined Loading":
        combined_analysis.app()
        
    elif topic == "Design of Combined Loading":
        combined_design.app()

    elif topic == "Shear Design":
        shear_design.app()

if __name__ == "__main__":
    app()
