import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def app():
    st.markdown("---")
    st.subheader("Advanced Effective Stress Analysis")
    
    # TABS for distinct workflows
    tab1, tab2 = st.tabs(["Stress Profile Calculator", "Heaving Check"])

    # ==================================================
    # TAB 1: STRESS PROFILE (Visual + Detailed Math)
    # ==================================================
    with tab1:
        st.caption("Define soil layers and water conditions to generate stress profiles and detailed calculations.")
        
        # --- 1. GLOBAL INPUTS ---
        col1, col2, col3 = st.columns(3)
        with col1:
            water_depth = st.number_input("Water Table Depth (m)", 0.0, step=0.1, value=2.0)
        with col2:
            hc = st.number_input("Capillary Rise (m)", 0.0, step=0.1, value=0.0, help="Height of water rising ABOVE the water table.")
        with col3:
            surcharge = st.number_input("Surcharge (q) [kPa]", 0.0, step=1.0, value=10.0)

        # --- 2. LAYER DEFINITION ---
        num_layers = st.number_input("Number of Layers", 1, 5, 2)
        layers = []
        
        # Colors: Sand (Yellowish), Clay (Grayish)
        colors = {'Sand': '#E6D690', 'Clay': '#B0A494'}
        
        st.markdown("### Soil Stratigraphy")
        for i in range(int(num_layers)):
            with st.expander(f"Layer {i+1}", expanded=True):
                c1, c2, c3, c4 = st.columns(4)
                
                # UPDATED: Only Sand and Clay options
                type_soil = c1.selectbox(f"Type", ["Sand", "Clay"], key=f"t{i}")
                
                thick = c2.number_input(f"Thickness (m)", 0.1, step=0.5, value=3.0, key=f"h{i}")
                gamma_sat = c3.number_input(f"γ_sat (kN/m³)", 0.1, step=0.1, value=20.0, key=f"gs{i}")
                gamma_dry = c4.number_input(f"γ_dry (kN/m³)", 0.1, step=0.1, value=17.0, key=f"gd{i}")
                
                layers.append({
                    "id": i, "type": type_soil, "H": thick, 
                    "g_sat": gamma_sat, "g_dry": gamma_dry, 
                    "color": colors.get(type_soil, '#E6D690')
                })

        # Calculate Total Depth dynamically based on inputs
        total_depth = sum([l['H'] for l in layers])

        # --- 3. INPUT DIAGRAM (SCHEMATIC) ---
        st.markdown("### 1. Input Visualization")
        
        fig_sch, ax_sch = plt.subplots(figsize=(8, 5))
        current_depth = 0
        
        # Draw Surcharge
        if surcharge > 0:
            for x in np.linspace(0, 4, 10):
                ax_sch.arrow(x, -0.2, 0, 0.2, head_width=0.1, head_length=0.1, fc='red', ec='red')
            ax_sch.text(2, -0.4, f"q = {surcharge} kPa", ha='center', color='red', fontweight='bold')

        # Draw Layers
        for lay in layers:
            # Rectangle (x, y, width, height) - y is positive down for logic, but we plot inverted
            rect = patches.Rectangle((0, current_depth), 5, lay['H'], facecolor=lay['color'], edgecolor='black', alpha=0.6)
            ax_sch.add_patch(rect)
            
            # Labels
            mid_y = current_depth + lay['H']/2
            ax_sch.text(2.5, mid_y, f"{lay['type']}\n$\\gamma_{{sat}}={lay['g_sat']}$\n$\\gamma_{{dry}}={lay['g_dry']}$", 
                        ha='center', va='center', fontsize=9, fontweight='bold')
            
            # Dimension Line
            ax_sch.annotate("", xy=(-0.2, current_depth), xytext=(-0.2, current_depth + lay['H']),
                            arrowprops=dict(arrowstyle='<->', color='black'))
            ax_sch.text(-0.3, mid_y, f"{lay['H']}m", va='center', ha='right')
            
            current_depth += lay['H']

        # Draw Water Table
        ax_sch.axhline(y=water_depth, color='blue', linestyle='--', linewidth=2)
        ax_sch.text(5.1, water_depth, "WT ▽", color='blue', va='center')
        
        # Draw Capillary Rise
        if hc > 0:
            cap_top = water_depth - hc
            if cap_top < 0: cap_top = 0 # Don't go above surface
            
            rect_cap = patches.Rectangle((0, cap_top), 5, water_depth - cap_top, hatch='///', fill=False, edgecolor='blue', alpha=0.3)
            ax_sch.add_patch(rect_cap)
            ax_sch.text(5.1, cap_top, f"Capillary\nRise ({hc}m)", color='blue', va='center', fontsize=8)

        ax_sch.set_ylim(total_depth + 1, -1.5) # Invert Y axis, extra space for surcharge
        ax_sch.set_xlim(-1, 6)
        ax_sch.axis('off')
        st.pyplot(fig_sch)

        # --- 4. CALCULATION LOGIC ---
        if st.button("Calculate Stress Profile", type="primary"):
            
            # Collect Critical Depths (Boundaries, WT, Capillary)
            z_points = {0.0, total_depth} 
            
            # Add Layer Boundaries
            running_z = 0
            for l in layers:
                running_z += l['H']
                z_points.add(round(running_z, 3))
            
            # Add Water Table & Capillary
            if 0 <= water_depth <= total_depth: z_points.add(water_depth)
            
            cap_top = water_depth - hc
            if 0 <= cap_top <= total_depth: z_points.add(cap_top)
            
            # Sort Depths
            sorted_z = sorted(list(z_points))
            
            results = []
            calc_steps = []
            
            gamma_w = 9.81
            sigma_prev = surcharge
            z_prev = 0.0
            
            st.markdown("### 2. Detailed Calculations")
            
            # Loop through depth intervals
            for i, z in enumerate(sorted_z):
                
                # A. PORE PRESSURE (u)
                if z > water_depth:
                    # Hydrostatic
                    u = (z - water_depth) * gamma_w
                    u_tex = f"({z} - {water_depth}) \\times 9.81"
                elif z > (water_depth - hc) and z <= water_depth:
                    # Capillary (Negative)
                    u = -(water_depth - z) * gamma_w
                    u_tex = f"-({water_depth} - {z}) \\times 9.81"
                else:
                    # Dry
                    u = 0.0
                    u_tex = "0"
                
                # B. TOTAL STRESS (sigma)
                if i == 0:
                    sigma = surcharge
                    calc_steps.append(f"**At Surface (z=0):** $\\sigma = q = {surcharge}$ kPa")
                else:
                    dz = z - z_prev
                    
                    # Find which layer we are in (using midpoint of interval)
                    z_mid = (z + z_prev) / 2
                    
                    # Find layer properties
                    active_layer = None
                    cur_l_bottom = 0
                    for l in layers:
                        cur_l_bottom += l['H']
                        if z_mid <= cur_l_bottom:
                            active_layer = l
                            break
                    
                    # Safety check
                    if active_layer is None: active_layer = layers[-1]

                    # Determine Gamma to use
                    # Logic: If in Capillary zone or below WT -> use Saturated Unit Weight
                    # Else -> use Dry Unit Weight
                    if z_mid > (water_depth - hc):
                        gamma_used = active_layer['g_sat']
                        g_sym = "\\gamma_{sat}"
                    else:
                        gamma_used = active_layer['g_dry']
                        g_sym = "\\gamma_{dry}"
                        
                    d_sigma = dz * gamma_used
                    sigma = sigma_prev + d_sigma
                    
                    # Log Calculation
                    calc_steps.append(f"**Interval {z_prev}m to {z}m:** Layer is {active_layer['type']} ({g_sym}={gamma_used})")
                    calc_steps.append(f"$\\Delta \\sigma = {gamma_used} \\times {dz:.2f} = {d_sigma:.2f}$")
                    calc_steps.append(f"$\\sigma_{{{z}}} = {sigma_prev:.2f} + {d_sigma:.2f} = \\mathbf{{{sigma:.2f}}}$")
                
                # C. EFFECTIVE STRESS
                sigma_p = sigma - u
                
                # Store Data
                results.append({
                    "Depth (z)": z,
                    "Total Stress (σ)": sigma,
                    "Pore Pressure (u)": u,
                    "Eff. Stress (σ')": sigma_p
                })
                
                # Add Point Calculation Log
                calc_steps.append(f"**At Depth z={z}m:**")
                calc_steps.append(f"$u = {u_tex} = {u:.2f}$")
                calc_steps.append(f"$\\sigma' = \\sigma - u = {sigma:.2f} - ({u:.2f}) = \\mathbf{{{sigma_p:.2f}}}$")
                calc_steps.append("---")
                
                # Update for next loop
                sigma_prev = sigma
                z_prev = z

            # --- DISPLAY CALCULATIONS ---
            with st.expander("Show Step-by-Step Math", expanded=True):
                for line in calc_steps:
                    if line == "---": st.markdown(line)
                    elif line.startswith("**"): st.markdown(line)
                    else: st.latex(line.replace("$", ""))

            # --- 5. OUTPUT GRAPH ---
            st.markdown("### 3. Stress Profile Graph")
            df = pd.DataFrame(results)
            
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Plot Lines
            ax.plot(df["Total Stress (σ)"], df["Depth (z)"], 'b-o', label=r"Total Stress $\sigma$")
            ax.plot(df["Pore Pressure (u)"], df["Depth (z)"], 'r--x', label=r"Pore Pressure $u$")
            ax.plot(df["Eff. Stress (σ')"], df["Depth (z)"], 'k-s', linewidth=2, label=r"Effective Stress $\sigma'$")
            
            # Styling
            ax.invert_yaxis()
            ax.set_ylabel("Depth (m)")
            ax.set_xlabel("Stress (kPa)")
            ax.grid(True, which='both', linestyle='--', alpha=0.7)
            ax.legend()
            ax.set_title("Variation of Stresses with Depth")
            
            # Add Horizontal lines for Layers
            cur_h = 0
            for l in layers:
                cur_h += l['H']
                ax.axhline(cur_h, color='gray', linestyle=':', alpha=0.5)

            st.pyplot(fig)
            
            # Data Table
            st.dataframe(df.style.format("{:.2f}"))

    # ==================================================
    # TAB 2: HEAVE CHECK (Preserved)
    # ==================================================
    with tab2:
        st.subheader("Detailed Heave Analysis (Clay over Sand)")
        st.caption("Checking for bottom heave in an excavation caused by artesian pressure from a lower layer.")
        
        col1, col2 = st.columns(2)
        with col1:
            h_clay_total = st.number_input("Total Thickness of Clay Layer (m)", 5.0, step=0.1)
            gamma_clay = st.number_input("Unit Wt of Clay (γ_sat) [kN/m³]", 20.0, step=0.1)
        with col2:
            artesian_head_surface = st.number_input("Piezometric Head (m above surface)", 1.0, step=0.1)
            gamma_w = 9.81
            
            h_p_interface = h_clay_total + artesian_head_surface
            u_artesian = h_p_interface * gamma_w
            st.info(f"Artesian Pressure at Bottom: {u_artesian:.2f} kPa")

        current_exc = st.number_input("Current Excavation Depth (m)", 2.0, step=0.5)
        
        if st.button("Check Safety"):
            remaining_clay = h_clay_total - current_exc
            downward_wt = remaining_clay * gamma_clay
            fs_calc = downward_wt / u_artesian
            
            st.latex(rf"FS = \frac{{\sigma_{{down}}}}{{u_{{up}}}} = \frac{{{remaining_clay:.2f} \times {gamma_clay}}}{{{u_artesian:.2f}}} = \mathbf{{{fs_calc:.3f}}}")
            
            if fs_calc < 1.0: st.error("UNSAFE: Bottom Heave will occur!")
            else: st.success("SAFE against Heave.")
