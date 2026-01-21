import streamlit as st

# 1. PAGE CONFIG (Must be the first command)
st.set_page_config(
    page_title="MHF Civil Portal", 
    page_icon="profile.png", 
    layout="wide"
)

# 2. THE BRANDING & BIO
def main():
    st.title("🏗️ MHF Civil Portal")
    st.caption("Advanced Civil Engineering Question Solver | Developed by Muhammad Hammad Faisal")
    st.markdown("---")

    # Welcome Message
    st.markdown("""
    ### **Precision. Logic. Deterministic.**
    Welcome to the official digital workspace of **MHF Civil**. 
    
    👈 **Select a Module from the Sidebar** to begin solving.
    """)

    # --- ABOUT THE DEVELOPER ---
    st.markdown("---")
    st.subheader("👨‍💻 About MHF Civil")
    
    dev_col1, dev_col2 = st.columns([1, 3])
    
    with dev_col1:
        # Ensure this filename matches exactly what you uploaded
        st.image("profile.png", width=150)
    
    with dev_col2:
        st.markdown("""
        **Muhammad Hammad Faisal** *Final Year Civil Engineering Student (METU) | Founder, MHF Civil*
        
        This portal was developed to bridge the gap between theoretical soil mechanics and practical application.
        """)
        st.link_button("🤝 Connect on LinkedIn", "https://www.linkedin.com/in/muhammad-hammad-20059a229/") 

    # --- FOOTER ---
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 12px;'>
        © 2026 MHF Civil Engineering Group. All rights reserved.<br>
        Version 1.1.0 | Ankara, Turkey
        </div>
        """, 
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
