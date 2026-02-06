# ... (Previous imports)

def render_inputs(section_type, goal):
    data = {}
    
    # [System Properties code remains the same...]
    
    st.markdown("---")
    st.markdown(f"### 3. Problem Variables")

    # === SINGLY REINFORCED ===
    if section_type == "Singly Reinforced":
        
        # SCENARIO 1: You have the beam, finding strength
        if goal == "Find Moment Capacity (Mr)":
            st.info("👇 **INPUT:** Enter the steel provided.")
            data['As'] = st.number_input("Tension Steel Area (As) [mm²]", value=1257.0)
            st.caption("The code will calculate **Moment Capacity (Mr)**.")
            
        # SCENARIO 2: You have the load, designing the beam
        elif goal == "Design Steel Area (As)":
            st.info("👇 **INPUT:** Enter the external load (Demand).")
            data['Md_target'] = st.number_input("Design Moment (Md) [kNm]", value=250.0)
            st.caption("The code will calculate required **Steel Area (As)**.")
            
        # SCENARIO 3: You have load + steel, finding geometry
        elif goal == "Find Minimum Depth (d)":
            st.info("👇 **INPUT:** Enter the external load (Demand).")
            data['Md_target'] = st.number_input("Design Moment (Md) [kNm]", value=250.0)
            data['rho'] = st.slider("Target Steel Ratio (ρ)", 0.005, 0.020, 0.010)
            st.caption("The code will calculate required **Depth (d)**.")

    # [Doubly/Multi sections follow same logic...]

    return data
