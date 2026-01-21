import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def app():
    st.markdown("---")
    st.subheader("⬇️ Advanced Effective Stress & Heave Analysis")
    
    # TABS for distinct workflows
    tab1, tab2 = st.tabs(["📝 Stress Profile Calculator", "🛡️ Heave/Piping Check"])

    # ==================================================
    # TAB 1: STRESS PROFILE (Dynamic Layers + Capillary)
    # ==================================================
    with tab1:
        st.caption("Calculate Total Stress, Pore Pressure (including Capillary/Artesian), and Effective Stress.")
        
        # 1. GLOBAL SETTINGS
        col1, col2, col3 = st.columns(3)
        with col1:
            water_depth = st.number_input("Water Table Depth (m)", 0.0, step=0.1, value=2.0)
        with col2:
            hc = st.number_input("Capillary Rise (m)", 0.0, step=0.1, help="Height of water rising ABOVE the water table.")
        with col3:
            surcharge = st.number_input("Surcharge (q) [kPa]", 0.0, step=1.0)

        # 2. DYNAMIC LAYERS
        num_layers = st.number_input("How many Soil Layers?", min_value=1, max_value=10, value=2)
        layers = []
        
        st.markdown("### 🧱 Define Soil Layers")
        for i in range(int(num_layers)):
            with st.expander(f"Layer {i+1}", expanded=(i==0)):
                c1, c2, c3, c4 = st.columns(4)
                
                # Inputs with unique keys
                type_soil = c1.selectbox(f"Type", ["Sand", "Clay", "Gravel", "Silt"], key=f"type_{i}")
                thick = c2.number_input(f"Thickness (m)", 0.1, step=0.5, key=f"h_{i}")
                gamma_sat = c3.number_input(f"Sat. Unit Wt (γ_sat)", 18.0, step=0.1, key=f"gs_{i}")
                gamma_dry = c4.number_input(f"Dry Unit Wt (γ_dry)", 16.0, step=0.1, key=f"gd_{i}")
                
                is_artesian = st.checkbox(f"Is Layer {i+1} Artesian (Confined)?", key=f"art_{i}")
                artesian_head = 0.0
                if is_artesian:
                    artesian_head = st.number_input(f"Piezometric Head for Layer {i+1} (m above surface)", value=0.0, key=f"head_{i}")

                layers.append({
                    "id": i+1,
                    "type": type_soil,
                    "H": thick,
                    "g_sat": gamma_sat,
                    "g_dry": gamma_dry,
                    "artesian": is_artesian,
                    "art_head": artesian_head
                })

        # 3. CALCULATION ENGINE
        if st.button("🚀 Calculate Stress Profile", type="primary"):
            results = []
            # Start at surface
            current_z = 0.0
            sigma = surcharge
            
            # Add surface point
            results.append({"z": 0.0, "sigma": sigma, "u": 0.0, "sigma_p": sigma})
            
            gamma_w = 9.81
            
            for lay in layers:
                H = lay['H']
                # Determine "Effective" Unit Weight for Total Stress Calculation
                # Simplified: If fully above WT+Capillary -> Dry. If submerged/capillary -> Sat.
                # (For high precision, we define zones, but here we check the midpoint of layer for simplicity or split logic)
                
                # SPLIT LAYER LOGIC (To handle WT or Capillary line crossing a layer)
                # For this code, we assume the user splits layers at WT interface for perfect accuracy, 
                # OR we calculate average unit weight. Let's do accurate Top/Bottom check.
                
                z_top = current_z
                z_bot = current_z + H
                
                # Determine Pore Pressure at Bottom
                u_bot = 0.0
                
                # ARTESIAN CASE
                if lay['artesian']:
                    # u = gamma_w * (distance from bottom to piezometric line)
                    # Piezometric line is at +artesian_head above surface (z=0)
                    # Depth of bottom is z_bot. 
                    # Pressure head = (artesian_head - (-z_bot)) = artesian_head + z_bot
                    h_pressure = lay['art_head'] + z_bot
                    u_bot = h_pressure * gamma_w
                else:
                    # HYDROSTATIC + CAPILLARY CASE
                    # Case 1: Below Water Table
                    if z_bot > water_depth:
                        u_bot = (z_bot - water_depth) * gamma_w
                    
                    # Case 2: In Capillary Zone (Between WT and WT - hc)
                    elif z_bot > (water_depth - hc):
                        # Suction (Negative Pressure)
                        # Height above WT = water_depth - z_bot
                        u_bot = - (water_depth - z_bot) * gamma_w
                        
                    # Case 3: Dry Zone
                    else:
                        u_bot = 0.0

                # Determine Gamma to use for Total Stress (Simplified Check)
                # If layer is mostly below water or in capillary -> Use Saturated
                # If layer is mostly dry -> Use Dry
                # NOTE: For "Exact" questions, students usually split layers at WT.
                # We will use Gamma_Sat if any part is wetted, or prompt user. 
                # Smart Check:
                if z_bot > (water_depth - hc):
                    gamma_use = lay['g_sat']
                    state = "Wet/Sat"
                else:
                    gamma_use = lay['g_dry']
                    state = "Dry"

                delta_sigma = gamma_use * H
                sigma += delta_sigma
                sigma_p = sigma - u_bot
                
                current_z += H
                
                results.append({
                    "z": current_z,
                    "sigma": sigma,
                    "u": u_bot,
                    "sigma_p": sigma_p,
                    "state": state
                })

            # --- DISPLAY ---
            st.markdown("### 📊 Calculation Results")
            df = pd.DataFrame(results)
            st.dataframe(df.style.format("{:.2f}"))
            
            # Plot
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.plot(df['sigma'], df['z'], 'b-o', label="Total Stress")
            ax.plot(df['u'], df['z'], 'r--x', label="Pore Pressure")
            ax.plot(df['sigma_p'], df['z'], 'k-', linewidth=3, label="Effective Stress")
            ax.invert_yaxis()
            ax.set_ylabel("Depth (m)")
            ax.set_xlabel("Stress (kPa)")
            ax.grid(True)
            ax.legend()
            st.pyplot(fig)

 # ==================================================
    # TAB 2: HEAVE & PIPING CHECK
    # ==================================================
    with tab2:
        st.subheader("🛡️ Excavation Safety (Heave Check)")
        st.markdown(r"**Principle:** Preventing bottom 'burst' when excavating Clay over an Artesian Sand layer.")

        # SCENARIO SELECTOR
        scenario = st.radio("Select Solving Goal:", 
                            ["Calculate Factor of Safety (FS)", 
                             "Find Max Depth of Excavation", 
                             "Required Pumping (Drawdown)"], 
                            horizontal=True)
        
        col1, col2 = st.columns(2)
        with col1:
            h_clay_total = st.number_input("Total Thickness of Clay Layer (m)", 5.0, step=0.1)
            gamma_clay = st.number_input("Unit Wt of Clay (γ_sat) [kN/m³]", 20.0, step=0.1)
        with col2:
            artesian_head_surface = st.number_input("Piezometric Head (m above surface)", 1.0, step=0.1, 
                                                   help="Height of water in a standpipe relative to the ground surface.")
            # Artesian Pressure at Interface
            h_p_interface = h_clay_total + artesian_head_surface
            u_artesian = h_p_interface * 9.81
            st.metric("Artesian Pressure (at interface)", f"{u_artesian:.2f} kPa")

        st.divider()

        # --- 1. CALCULATE FACTOR OF SAFETY ---
        if "Factor of Safety" in scenario:
            current_exc = st.number_input("Current Excavation Depth (m)", 2.0, step=0.5)
            remaining_clay = h_clay_total - current_exc
            
            if st.button("Calculate FS"):
                downward_wt = remaining_clay * gamma_clay
                fs_calc = downward_wt / u_artesian
                
                st.markdown(f"### Result: FS = {fs_calc:.3f}")
                st.latex(rf"FS = \frac{{\text{{Downward Weight}}}}{{\text{{Artesian Pressure}}}} = \frac{{{remaining_clay:.2f} \times {gamma_clay}}}{{{u_artesian:.2f}}}")
                
                if fs_calc < 1.0:
                    st.error("❌ FAILURE: The bottom will heave/burst!")
                elif fs_calc < 1.2:
                    st.warning("⚠️ CRITICAL: Factor of safety is very low.")
                else:
                    st.success("✅ SAFE: The excavation is stable.")

        # --- 2. FIND MAX EXCAVATION DEPTH ---
        elif "Max Depth" in scenario:
            fs_req = st.number_input("Required Factor of Safety", 1.2, step=0.1)
            
            if st.button("Calculate Max Depth"):
                # Downward = Upward * FS
                # (H_total - X) * Gamma = u_artesian * FS
                # X = H_total - (FS * u_artesian / Gamma)
                max_x = h_clay_total - (fs_req * u_artesian / gamma_clay)
                
                if max_x < 0:
                    st.error("Artesian pressure is too high. You cannot excavate at all without pumping.")
                else:
                    st.success(f"✅ Max Safe Excavation Depth: **{max_x:.2f} m**")
                    st.latex(rf"H_{{exc}} = H_{{total}} - \frac{{FS \times u_{{artesian}}}}{{\gamma_{{clay}}}}")

        # --- 3. REQUIRED PUMPING ---
        else:
            planned_x = st.number_input("Planned Excavation Depth (m)", 4.0)
            fs_target = st.number_input("Target Factor of Safety", 1.2)
            
            if st.button("Calculate Required Drawdown"):
                remaining_t = h_clay_total - planned_x
                allowable_u = (remaining_t * gamma_clay) / fs_target
                allowable_head = allowable_u / 9.81 # Head relative to interface
                
                # Current head relative to interface is h_p_interface
                drawdown_needed = h_p_interface - allowable_head
                
                st.markdown("### Analysis")
                st.write(f"Remaining Clay: {remaining_t:.2f} m")
                st.write(f"Allowable Artesian Pressure: {allowable_u:.2f} kPa")
                
                if drawdown_needed > 0:
                    st.error(f"⚠️ Lower the Artesian Head by **{drawdown_needed:.2f} meters** via pumping.")
                else:
                    st.success("✅ Safe as is. No pumping required.")
