import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def app():
    st.markdown("---")
    st.subheader("Advanced Effective Stress & Heave Analysis")
    
    # TABS for distinct workflows
    tab1, tab2 = st.tabs(["Stress Profile Calculator", "Heaving Check"])

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
        
        st.markdown("### Define Soil Layers")
        for i in range(int(num_layers)):
            with st.expander(f"Layer {i+1}", expanded=(i==0)):
                c1, c2, c3, c4 = st.columns(4)
                
                # Inputs with unique keys
                type_soil = c1.selectbox(f"Type", ["Sand", "Clay", "Gravel", "Silt"], key=f"type_{i}")
                thick = c2.number_input(f"Thickness (m)", 0.1, step=0.5, value=4.0, key=f"h_{i}")
                gamma_sat = c3.number_input(f"Sat. Unit Wt (kN/m³)", 18.0, step=0.1, key=f"gs_{i}")
                gamma_dry = c4.number_input(f"Dry Unit Wt (kN/m³)", 16.0, step=0.1, key=f"gd_{i}")
                
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
        if st.button("Calculate Stress Profile", type="primary"):
            results = []
            # Start at surface
            current_z = 0.0
            sigma = surcharge
            
            # Add surface point
            results.append({"z": 0.0, "sigma": sigma, "u": 0.0, "sigma_p": sigma})
            
            gamma_w = 9.81
            
            # --- Calculation Logic ---
            for lay in layers:
                H = lay['H']
                z_top = current_z
                z_bot = current_z + H
                
                # We interpret the layer as a single block for simplicity in this visualizer,
                # but to be accurate with WT crossing a layer, we check the midpoint or bottom state.
                
                # 1. Total Stress Calc (Sigma)
                # Determine dominant unit weight based on Water Table location vs Layer
                # If layer is completely above WT-hc: Dry
                # If layer is completely below WT-hc: Sat
                # If split: Weighted Average (simplified) or split into sub-layers (advanced).
                # here we use a simplified check based on the middle of the layer
                z_mid = (z_top + z_bot) / 2
                
                if z_mid > (water_depth - hc):
                    gamma_use = lay['g_sat']
                else:
                    gamma_use = lay['g_dry']

                delta_sigma = gamma_use * H
                sigma += delta_sigma
                
                # 2. Pore Pressure Calc (u) at BOTTOM of layer
                if lay['artesian']:
                    # u = gamma_w * height of piezo line above point z_bot
                    # piezo line is at -art_head (above surface). Point is at z_bot.
                    # Total pressure head = artesian_head + z_bot
                    u_bot = (lay['art_head'] + z_bot) * gamma_w
                else:
                    # Hydrostatic
                    if z_bot > water_depth:
                        u_bot = (z_bot - water_depth) * gamma_w
                    # Capillary (Suction)
                    elif z_bot > (water_depth - hc):
                        u_bot = - (water_depth - z_bot) * gamma_w
                    # Dry
                    else:
                        u_bot = 0.0
                
                sigma_p = sigma - u_bot
                
                current_z += H
                
                results.append({
                    "z": current_z,
                    "sigma": sigma,
                    "u": u_bot,
                    "sigma_p": sigma_p
                })

            # --- DISPLAY RESULTS ---
            st.markdown("### Calculation Results")
            df = pd.DataFrame(results)
            
            col_res1, col_res2 = st.columns([1, 2])
            
            with col_res1:
                st.dataframe(df.style.format("{:.2f}"))
            
            with col_res2:
                # --- MATPLOTLIB PLOT ---
                fig, ax = plt.subplots(figsize=(8, 6))
                
                # Draw Soil Layers (Background patches)
                prev_z = 0
                colors = {'Sand': '#E6D690', 'Clay': '#B0A494', 'Gravel': '#A69F8B', 'Silt': '#D9CBA3'}
                
                for lay in layers:
                    this_z = prev_z + lay['H']
                    c = colors.get(lay['type'], 'white')
                    # Draw rectangle spanning the width of the graph
                    # We calculate max stress to know width
                    max_stress = df[['sigma', 'u', 'sigma_p']].max().max()
                    # Add a bit of padding
                    x_limit = max_stress * 1.1
                    
                    rect = patches.Rectangle((0, prev_z), x_limit, lay['H'], linewidth=0, facecolor=c, alpha=0.3)
                    ax.add_patch(rect)
                    
                    # Add Label for Layer
                    ax.text(x_limit*0.05, prev_z + lay['H']/2, lay['type'], fontsize=9, color='black', alpha=0.7)
                    prev_z = this_z

                # Draw WT Line
                ax.axhline(y=water_depth, color='blue', linestyle='-.', linewidth=1, label="Water Table")
                ax.text(df['sigma'].max(), water_depth, " WT ▽", color='blue', va='bottom', ha='right')

                # Plot Stresses
                ax.plot(df['sigma'], df['z'], 'b-o', label=r"Total Stress ($\sigma$)")
                ax.plot(df['u'], df['z'], 'r--x', label=r"Pore Water Pressure ($u$)")
                ax.plot(df['sigma_p'], df['z'], 'k-', linewidth=2.5, label=r"Effective Stress ($\sigma'$)")
                
                ax.invert_yaxis()
                ax.set_ylabel("Depth (m)")
                ax.set_xlabel("Stress (kPa)")
                ax.set_title("Stress Profile with Stratigraphy")
                ax.grid(True, alpha=0.5)
                ax.legend(loc='lower left')
                
                st.pyplot(fig)

    # ==================================================
    # TAB 2: HEAVE & PIPING CHECK
    # ==================================================
    with tab2:
        st.subheader("Detailed Heave Analysis (Clay over Sand)")
        st.caption("Checking for bottom heave in an excavation caused by artesian pressure from a lower layer.")
        
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

        # Helper Variables for Drawing
        draw_exc_depth = 0.0
        draw_rem_clay = 0.0
        draw_fs_status = "Calc"

        # --- 1. CALCULATE FACTOR OF SAFETY ---
        if "Factor of Safety" in scenario:
            current_exc = st.number_input("Current Excavation Depth (m)", 2.0, step=0.5)
            remaining_clay = h_clay_total - current_exc
            
            draw_exc_depth = current_exc
            draw_rem_clay = remaining_clay

            if st.button("Calculate Step-by-Step FS"):
                downward_wt = remaining_clay * gamma_clay
                fs_calc = downward_wt / u_artesian
                
                if fs_calc < 1.0: draw_fs_status = "UNSAFE"
                else: draw_fs_status = f"SAFE (FS={fs_calc:.2f})"
                
                with st.expander("View Detailed Calculation", expanded=True):
                    st.markdown("**Step 2: Downward Force (Remaining Clay Weight)**")
                    st.latex(rf"T_{{remaining}} = H_{{total}} - H_{{exc}} = {h_clay_total:.2f} - {current_exc:.2f} = {remaining_clay:.2f} \, \text{{m}}")
                    st.latex(rf"\sigma_{{down}} = T_{{remaining}} \times \gamma_{{clay}} = {remaining_clay:.2f} \times {gamma_clay:.1f} = {downward_wt:.2f} \, \text{{kPa}}")
                    
                    st.markdown("**Step 3: Factor of Safety**")
                    st.latex(rf"FS = \frac{{\sigma_{{down}}}}{{u_{{artesian}}}} = \frac{{{downward_wt:.2f}}}{{{u_artesian:.2f}}} = \mathbf{{{fs_calc:.3f}}}")
                
                if fs_calc < 1.0: st.error("FAILURE: Bottom will heave.")
                else: st.success(f"Safe! FS = {fs_calc:.3f}")

        # --- 2. FIND MAX EXCAVATION DEPTH ---
        elif "Max Depth" in scenario:
            fs_req = st.number_input("Required Factor of Safety", 1.2, step=0.1)
            
            if st.button("Derive Max Depth"):
                required_downward = fs_req * u_artesian
                min_thickness = required_downward / gamma_clay
                max_x = h_clay_total - min_thickness
                
                draw_exc_depth = max_x
                draw_rem_clay = min_thickness
                draw_fs_status = f"Limit (FS={fs_req})"
                
                with st.expander("View Detailed Derivation", expanded=True):
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
            
            if st.button("Calculate Pumping Requirements"):
                remaining_t = h_clay_total - planned_x
                sigma_down = remaining_t * gamma_clay
                allowable_u = sigma_down / fs_target
                allowable_hp = allowable_u / 9.81
                drawdown = h_p_interface - allowable_hp
                
                draw_exc_depth = planned_x
                draw_rem_clay = remaining_t
                draw_fs_status = f"Pumped (FS={fs_target})"

                with st.expander("View Pumping Logic", expanded=True):
                    st.markdown("**Step 2: Current Downward Pressure**")
                    st.latex(rf"\sigma_{{down}} = ({h_clay_total:.2f} - {planned_x:.2f}) \times {gamma_clay} = {sigma_down:.2f} \, \text{{kPa}}")
                    
                    st.markdown("**Step 3: Allowable Artesian Pressure for Target FS**")
                    st.latex(rf"u_{{allow}} = \frac{{\sigma_{{down}}}}{{FS}} = \frac{{{sigma_down:.2f}}}{{{fs_target:.1f}}} = {allowable_u:.2f} \, \text{{kPa}}")
                    
                    st.markdown("**Step 4: Required Water Level Drop**")
                    st.latex(rf"\text{{Drawdown}} = h_{{p(current)}} - \frac{{u_{{allow}}}}{{\gamma_w}} = {h_p_interface:.2f} - {allowable_hp:.2f} = \mathbf{{{drawdown:.2f} \, \text{{m}}}}")

        # --- DRAW VISUALIZER (Only if calculated) ---
        if draw_rem_clay > 0 or draw_exc_depth > 0:
            st.markdown("### Visual Representation")
            
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            
            # Limits
            total_h = h_clay_total + 2 # Add some space for sand below
            ax2.set_xlim(-1, 5)
            ax2.set_ylim(-2, total_h + artesian_head_surface + 1)
            ax2.axis('off')
            
            # 1. Draw Sand Layer (Bottom)
            ax2.add_patch(patches.Rectangle((-1, -2), 6, 2, facecolor='#E6D690', edgecolor='gray'))
            ax2.text(2, -1, "Permeable Sand Layer (Artesian)", ha='center')
            
            # 2. Draw Clay Layer (Remaining Plug)
            # The interface is at y=0. The top of clay is at y=h_clay_total.
            # Excavation removes top part.
            
            # Full Clay Block outline (Ghost)
            ax2.add_patch(patches.Rectangle((0, 0), 4, h_clay_total, fill=False, linestyle='--', edgecolor='gray'))
            
            # Remaining Plug
            ax2.add_patch(patches.Rectangle((0, 0), 4, draw_rem_clay, facecolor='#B0A494', edgecolor='black'))
            ax2.text(2, draw_rem_clay/2, f"Clay Plug\n{draw_rem_clay:.2f}m", ha='center', va='center', fontweight='bold')
            
            # Excavated Area
            ax2.text(2, draw_rem_clay + draw_exc_depth/2, f"Excavation\n{draw_exc_depth:.2f}m", ha='center', color='red')
            
            # 3. Draw Piezometric Line (Artesian Head)
            piezo_y = h_clay_total + artesian_head_surface
            ax2.axhline(y=piezo_y, color='blue', linestyle='-.', linewidth=2)
            ax2.text(4.2, piezo_y, f"Piezometric Level\n(+{artesian_head_surface}m)", color='blue', va='center')
            
            # 4. Forces Arrows
            # Upward Force (U)
            ax2.arrow(1, -0.5, 0, 1.5, head_width=0.1, head_length=0.2, fc='red', ec='red')
            ax2.text(0.8, -0.8, "U (Uplift)", color='red', ha='center')
            
            # Downward Force (W)
            ax2.arrow(3, draw_rem_clay + 0.5, 0, -1.5, head_width=0.1, head_length=0.2, fc='green', ec='green')
            ax2.text(3.2, draw_rem_clay + 0.8, "W (Weight)", color='green', ha='center')
            
            # Status Label
            ax2.text(2, total_h + 1, f"Status: {draw_fs_status}", ha='center', fontsize=12, bbox=dict(facecolor='white', edgecolor='black'))

            st.pyplot(fig2)
