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
        st.subheader("🛡️ Detailed Heave Analysis")
        
        # Solving Goal
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
            artesian_head_surface = st.number_input("Piezometric Head (m above surface)", 1.0, step=0.1)
            gamma_w = 9.81
            
            # --- SHOWING THE ARTESIAN PRESSURE CALCULATION ---
            st.markdown("**Step 1: Calculate Artesian Pressure**")
            h_p_interface = h_clay_total + artesian_head_surface
            u_artesian = h_p_interface * gamma_w
            
            st.latex(rf"h_{{p}} = H_{{clay}} + h_{{piezo}} = {h_clay_total:.2f} + {artesian_head_surface:.2f} = {h_p_interface:.2f} \, \text{{m}}")
            st.latex(rf"u_{{artesian}} = h_{{p}} \times \gamma_w = {h_p_interface:.2f} \times 9.81 = \mathbf{{{u_artesian:.2f} \, \text{{kPa}}}}")

        st.divider()

        # --- 1. CALCULATE FACTOR OF SAFETY ---
        if "Factor of Safety" in scenario:
            current_exc = st.number_input("Current Excavation Depth (m)", 2.0, step=0.5)
            remaining_clay = h_clay_total - current_exc
            
            if st.button("🚀 Calculate Step-by-Step FS"):
                downward_wt = remaining_clay * gamma_clay
                fs_calc = downward_wt / u_artesian
                
                with st.expander("📝 View Detailed Calculation", expanded=True):
                    st.markdown("**Step 2: Downward Force (Remaining Clay Weight)**")
                    st.latex(rf"T_{{remaining}} = H_{{total}} - H_{{exc}} = {h_clay_total:.2f} - {current_exc:.2f} = {remaining_clay:.2f} \, \text{{m}}")
                    st.latex(rf"\sigma_{{down}} = T_{{remaining}} \times \gamma_{{clay}} = {remaining_clay:.2f} \times {gamma_clay:.1f} = {downward_wt:.2f} \, \text{{kPa}}")
                    
                    st.markdown("**Step 3: Factor of Safety**")
                    st.latex(rf"FS = \frac{{\sigma_{{down}}}}{{u_{{artesian}}}} = \frac{{{downward_wt:.2f}}}{{{u_artesian:.2f}}} = \mathbf{{{fs_calc:.3f}}}")
                
                if fs_calc < 1.0: st.error("❌ FAILURE: Bottom will heave.")
                else: st.success(f"✅ Safe! FS = {fs_calc:.3f}")

        # --- 2. FIND MAX EXCAVATION DEPTH ---
        elif "Max Depth" in scenario:
            fs_req = st.number_input("Required Factor of Safety", 1.2, step=0.1)
            
            if st.button("🚀 Derive Max Depth"):
                # Calculation: (H - X) * G = FS * U  => X = H - (FS * U / G)
                required_downward = fs_req * u_artesian
                min_thickness = required_downward / gamma_clay
                max_x = h_clay_total - min_thickness
                
                with st.expander("📝 View Detailed Derivation", expanded=True):
                    st.markdown("**Step 2: Required Downward Resistance**")
                    st.latex(rf"\sigma_{{req}} = FS \times u_{{artesian}} = {fs_req:.1f} \times {u_artesian:.2f} = {required_downward:.2f} \, \text{{kPa}}")
                    
                    st.markdown("**Step 3: Minimum Clay Thickness Needed**")
                    st.latex(rf"T_{{min}} = \frac{{\sigma_{{req}}}}{{\gamma_{{clay}}}} = \frac{{{required_downward:.2f}}}{{{gamma_clay:.1f}}} = {min_thickness:.2f} \, \text{{m}}")
                    
                    st.markdown("**Step 4: Max Excavation Depth**")
                    st.latex(rf"H_{{exc}} = H_{{total}} - T_{{min}} = {h_clay_total:.2f} - {min_thickness:.2f} = \mathbf{{{max_x:.2f} \, \text{{m}}}}")

        # --- 3. REQUIRED PUMPING ---
        else:
            planned_x = st.number_input("Planned Excavation Depth (m)", 4.0)
            fs_target = st.number_input("Target Factor of Safety", 1.2)
            
            if st.button("🚀 Calculate Pumping Requirements"):
                remaining_t = h_clay_total - planned_x
                sigma_down = remaining_t * gamma_clay
                allowable_u = sigma_down / fs_target
                allowable_hp = allowable_u / 9.81
                drawdown = h_p_interface - allowable_hp
                
                with st.expander("📝 View Pumping Logic", expanded=True):
                    st.markdown("**Step 2: Current Downward Pressure**")
                    st.latex(rf"\sigma_{{down}} = ({h_clay_total:.2f} - {planned_x:.2f}) \times {gamma_clay} = {sigma_down:.2f} \, \text{{kPa}}")
                    
                    st.markdown("**Step 3: Allowable Artesian Pressure for Target FS**")
                    st.latex(rf"u_{{allow}} = \frac{{\sigma_{{down}}}}{{FS}} = \frac{{{sigma_down:.2f}}}{{{fs_target:.1f}}} = {allowable_u:.2f} \, \text{{kPa}}")
                    
                    st.markdown("**Step 4: Required Water Level Drop**")
                    st.latex(rf"\text{{Drawdown}} = h_{{p(current)}} - \frac{{u_{{allow}}}}{{\gamma_w}} = {h_p_interface:.2f} - {allowable_hp:.2f} = \mathbf{{{drawdown:.2f} \, \text{{m}}}}")
