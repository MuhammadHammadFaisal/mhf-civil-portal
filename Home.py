import streamlit as st

# 1. PAGE CONFIG
st.set_page_config(
    page_title="MHF Civil Portal", 
    page_icon="assets/logo.png", 
    layout="wide"
)

def main():
    # --- LOGO AT THE TOP ---
    # We use a container with a special sidebar method to ensure it renders first
    with st.sidebar:
        # This empty container pushes the logo to the top
        st.image("assets/logo.png", use_container_width=True)
        st.markdown("---") # Optional divider
    
    # --- HOME PAGE CONTENT ---
    st.markdown("# MHF Civil Portal")
    st.caption("Deterministic Civil Engineering Computation Platform")
    st.markdown("---")
    
    # Welcome Message
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
    **engineering results should be reproducible, transparent, and mathematically defensible.**
    """)

    st.link_button("Connect on LinkedIn", "https://www.linkedin.com/in/muhammad-hammad-20059a229/")
    
    # --- FOOTER ---
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 12px;'>
        © 2026 MHF Civil. All rights reserved.<br>
        Version 1.1.0 · Ankara, Turkey
        </div>
        """, 
        unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()
