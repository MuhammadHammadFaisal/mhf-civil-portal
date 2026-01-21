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
        st.markdown(r"**Principle:** When excavating in Clay overlying Sand (Artesian), checking if the bottom will 'heave' or burst.")
        
        # SCENARIO SELECTOR
        scenario = st.radio("Select Problem Type:", ["Scenario A: Max Depth of Excavation?", "Scenario B: Reduce Water Table?"], horizontal=True)
        
        col1, col2 = st.columns(2)
        with col1:
            h_clay = st.number_input("Total Thickness of Clay Layer (m)", 5.0, step=0.5)
            gamma_clay = st.number_input("Unit Wt of Clay (γ_sat) [kN/m³]", 20.0, step=0.1)
        with col2:
            h_sand_head = st.number_input("Pressure Head in Sand Layer (m)", 0.0, help="Height of water in piezometer tube above the sand/clay interface.")
            # OR define by Water Table
            st.caption("Or define by Water Table:")
            wt_depth = st.number_input("Depth of Water Table from Surface (m)", 1.0, step=0.1, key="wt_heave")

        st.markdown("---")
        
        # --- SOLVER A: MAX EXCAVATION DEPTH ---
        if "Scenario A" in scenario:
            st.write("### 🚧 Finding Max Excavation Depth")
            fs = st.number_input("Desired Factor of Safety (FS)", value=1.1, step=0.1)
            
            # Logic: Downward Weight > Upward Pressure * FS
            # Let X be excavation depth. Remaining clay = H_clay - X
            # Downward = (H_clay - X) * Gamma_Clay
            # Upward = Gamma_w * (Pressure Head relative to bottom of clay)
            # Wait! We need to know the Artesian head relative to WHERE? 
            # Usually problem gives WT depth.
            # Upward Pressure at Clay/Sand Interface = (H_clay - WT_depth) * 9.81
            
            if st.button("Calculate Max Depth"):
                # U_uplift at interface
                # Head = Distance from WT to Bottom of Clay
                h_pressure = h_clay - wt_depth
                u_uplift = h_pressure * 9.81
                
                # Formula: (H_clay - X) * Gamma_Clay = FS * u_uplift
                # H_clay*G - X*G = FS * U
                # H_clay*G - FS*U = X*G
                # X = (H_clay*G - FS*U) / G
                
                max_excavation = ( (h_clay * gamma_clay) - (fs * u_uplift) ) / gamma_clay
                
                if max_excavation < 0:
                    st.error("Impossible! The pressure is already too high to excavate even 1cm.")
                else:
                    st.success(f"✅ Max Safe Excavation Depth: **{max_excavation:.2f} m**")
                    st.latex(rf"H_{{exc}} = \frac{{H_{{clay}}\gamma_{{clay}} - (FS \times u_{{uplift}})}}{{\gamma_{{clay}}}}")

        # --- SOLVER B: REDUCE WATER TABLE ---
        else:
            st.write("### 💧 Required Pumping (Lowering Water Table)")
            target_exc = st.number_input("Planned Excavation Depth (m)", 4.0)
            fs_req = st.number_input("Required Factor of Safety", 1.2)
            
            if st.button("Calculate Drawdown"):
                # Remaining Clay Thickness
                T = h_clay - target_exc
                # Downward Stress
                sigma_down = T * gamma_clay
                
                # Allowable Uplift Pressure for FS
                # sigma_down / u_allow = FS  -> u_allow = sigma_down / FS
                u_allow = sigma_down / fs_req
                
                # Allowable Head (h_allow)
                # u = h_allow * 9.81 -> h_allow = u / 9.81
                h_allow = u_allow / 9.81
                
                # Current Head (Assuming WT is at wt_depth)
                # Current Head at bottom = H_clay - wt_depth
                h_current = h_clay - wt_depth
                
                # Difference
                drop_needed = h_current - h_allow
                
                st.markdown(f"**Analysis:**")
                st.latex(rf"\sigma_{{down}} = {T:.2f} \text{{m}} \times {gamma_clay} = {sigma_down:.2f} \text{{ kPa}}")
                st.latex(rf"u_{{max}} = \frac{{{sigma_down:.2f}}}{{{fs_req}}} = {u_allow:.2f} \text{{ kPa}}")
                
                if drop_needed > 0:
                    st.error(f"⚠️ You must lower the water table by **{drop_needed:.2f} meters**.")
                else:
                    st.success("✅ Safe! No water table lowering required.")
