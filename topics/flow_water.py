# =================================================================
    # TAB 1: 1D SEEPAGE (The "Diagram" Problem)
    # =================================================================
    with tab1:
        st.caption("Determine Effective Stress at Point A. (Datum is at the Bottom of Soil)")
        
        col_setup, col_plot = st.columns([1, 1.2])
        
        with col_setup:
            st.markdown("### 1. Problem Setup")
            
            # 1. Soil Height (z)
            val_z = st.number_input("Soil Specimen Height (z) [m]", 0.1, step=0.5, value=4.0)
            
            # 2. Top Water (y)
            val_y = st.number_input("Water Height above Soil (y) [m]", 0.0, step=0.5, value=2.0)
            
            # 3. Bottom Head (x)
            val_x = st.number_input("Piezometer Head at Bottom (x) [m]", 0.0, step=0.5, value=7.5,
                                   help="This is the total head at the bottom boundary, measured from the Datum.")

            # 4. Soil Properties
            gamma_sat = st.number_input("Saturated Unit Weight (γ_sat) [kN/m³]", 18.0, step=0.1)
            gamma_w = 9.81

            # 5. Point A
            val_A = st.slider("Height of Point 'A' from Datum [m]", 0.0, val_z, val_z/2)

            # --- MOVE BUTTON HERE ---
            # Placing the button inside col_setup ensures it stays near the inputs
            calculate_btn = st.button("Calculate Effective Stress", use_container_width=True)

        # --- DYNAMIC MATPLOTLIB DIAGRAM ---
        with col_plot:
            # ... (Keep your existing Matplotlib code here) ...
            # Ensure the fig and ax logic remains exactly as you wrote it
            fig, ax = plt.subplots(figsize=(7, 8))
            # [Your drawing code goes here]
            st.pyplot(fig)

        # --- CALCULATION LOGIC ---
        # This can stay outside the columns or inside col_setup, 
        # but triggered by the button we defined above
        if calculate_btn:
            # 1. Identify Heads
            H_top = val_z + val_y  
            H_bot = val_x          
            
            # 2. Flow Analysis
            h_loss = H_top - H_bot
            
            if h_loss > 0:
                flow_type = "Downward"
                effect_msg = "Downward Flow increases Effective Stress (+i·z·γw)"
            elif h_loss < 0:
                flow_type = "Upward"
                effect_msg = "Upward Flow decreases Effective Stress (-i·z·γw)"
            else:
                flow_type = "No Flow"
                effect_msg = "Hydrostatic Condition"

            # 3. Calculations
            i = abs(h_loss) / val_z  
            sigma_total = (val_y * gamma_w) + ((val_z - val_A) * gamma_sat)
            H_A = H_bot + (val_A / val_z) * (H_top - H_bot)
            h_p_A = H_A - val_A
            u_val = h_p_A * gamma_w
            sigma_prime = sigma_total - u_val
            
            # --- DISPLAY RESULTS BELOW BOTH COLUMNS ---
            st.markdown("---")
            st.success(f"**Flow Condition:** {flow_type} ({effect_msg})")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Total Stress (σ)", f"{sigma_total:.2f} kPa")
            with c2:
                st.metric("Pore Pressure (u)", f"{u_val:.2f} kPa")
            with c3:
                st.metric("Effective Stress (σ')", f"{sigma_prime:.2f} kPa")
            
            # ... [Rest of your expander logic] ...
