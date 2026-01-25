def app():


    # --- PROFESSIONAL HEADER ---
    # 1. Use a tighter column ratio [1, 4] 
    #    This reserves 20% width for logo area, 80% for text area.
    try:
        col_logo, col_text = st.columns([1, 4], vertical_alignment="center")
    except TypeError:
        col_logo, col_text = st.columns([1, 4])

    with col_logo:
        # 2. FIXED WIDTH: Set width=180 or 200. 
        #    This prevents the logo from becoming huge on wide monitors.
        st.image("assets/logo.png", width=200) 

    with col_text:
        # 3. TEXT ALIGNMENT: Reduced padding-left to bring text closer to logo.
        st.markdown(
            """
            <div style="padding-left: 0px;">
                <h1 style='font-size: 42px; margin-bottom: 0px; line-height: 1.1;'>Soil Mechanics</h1>
                <p style='color: #666; font-size: 16px; font-weight: 300; margin-top: 5px;'>
                    Phase Relationships, Effective Stress & Flow Analysis
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )

    st.markdown("---")

    # --- TOPIC SELECTION MENU ---
    topic = st.selectbox(
        "Select Calculation Module:", 
        [
            "Phase Relationships",
            "Effective Stress",
            "Flow of Water in Soils"
        ]
    )

    # --- ROUTER LOGIC ---
    if topic == "Phase Relationships":
        soil_phase.app()

    elif topic == "Effective Stress":
        effective_stress.app()

    elif topic == "Flow of Water in Soils":
        flow_water.app()
