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
        st.caption("Define soil layers and water conditions to generate stress profiles.")
        
        # --- 1. ANALYSIS SETTINGS ---
        col_set1, col_set2 = st.columns(2)
        with col_set1:
            analysis_mode = st.radio(
                "Analysis State:", 
                ["Long Term (Drained)", "Short Term (Undrained - Immediate)"],
                help="Short Term: Surcharge creates excess pore pressure in CLAY layers only."
            )
        
        with col_set2:
            st.info("💡 **Short Term:** For Clays, excess pore pressure (Δu) = Surcharge (q).\n\n💡 **Long Term:** Excess pore pressure dissipates (Δu = 0).")

        st.divider()

        # --- 2. GLOBAL INPUTS ---
        col1, col2, col3 = st.columns(3)
        with col1:
            water_depth = st.number_input("Water Table Depth (m)", 0.0, step=0.1, value=2.0)
        with col2:
            hc = st.number_input("Capillary Rise (m)", 0.0, step=0.1, value=0.0)
        with col3:
            surcharge = st.number_input("Surcharge (q) [kPa]", 0.0, step=1.0, value=80.0)

        # --- 3. SMART LAYER DEFINITION ---
        num_layers = st.number_input("Number of Layers", 1, 5, 2)
        layers = []
        colors = {'Sand': '#E6D690', 'Clay': '#B0A494'}
        
        st.markdown("### Soil Stratigraphy")
        
        current_depth_tracker = 0.0
        
        for i in range(int(num_layers)):
            with st.expander(f"Layer {i+1} (Top: {current_depth_tracker}m)", expanded=True):
                c1, c2, c3, c4 = st.columns(4)
                
                type_soil = c1.selectbox(f"Type", ["Sand", "Clay"], key=f"t{i}")
                thick = c2.number_input(f"Thickness (m)", 0.1, step=0.5, value=5.0, key=f"h{i}")
                
                layer_top = current_depth_tracker
                layer_bot = current_depth_tracker + thick
                
                is_above_wt = layer_bot <= water_depth
                is_below_wt = layer_top >= water_depth
                is_crossing_wt = (layer_top < water_depth) and (layer_bot > water_depth)
                is_in_capillary = (layer_bot > (water_depth - hc)) and (layer_bot <= water_depth)
                
                gamma_sat = 0.0
                gamma_dry = 0.0
                
                need_sat = is_below_wt or is_crossing_wt or is_in_capillary
                need_dry = is_above_wt or is_crossing_wt
                
                if need_sat:
                    gamma_sat = c3.number_input(f"γ_sat (kN/m³)", 0.1, step=0.1, value=20.0, key=f"gs{i}")
                else:
                    c3.markdown(f"*(Layer is Dry)*")
                    gamma_sat = 20.0
                
                if need_dry:
                    gamma_dry = c4.number_input(f"γ_dry (kN/m³)", 0.1, step=0.1, value=17.0, key=f"gd{i}")
                else:
                    c4.markdown(f"*(Layer Submerged)*")
                    gamma_dry = 17.0

                layers.append({
                    "id": i, "type": type_soil, "H": thick, 
                    "g_sat": gamma_sat, "g_dry": gamma_dry, 
                    "color": colors.get(type_soil, '#E6D690')
                })
                
                current_depth_tracker += thick

        total_depth = current_depth_tracker

        # --- 4. INPUT VISUALIZATION (COMPACT SIZE) ---
        st.markdown("### 1. Input Visualization")
        
        if total_depth > 0:
            # COMPACT SIZE: Reduced to (6, 3) to match your preference
            fig, ax = plt.subplots(figsize=(5, 3.5))
            ax.set_xlim(-1.5, 2.5) 
            ax.set_ylim(0, max(1.5, 1 + e + 0.3)) 
            ax.axis('off')
            if surcharge > 0:
                for x in np.linspace(0, 4, 10):
                    ax_sch.arrow(x, -0.2, 0, 0.2, head_width=0.1, head_length=0.1, fc='red', ec='red')
                # Smaller font for compactness
                ax_sch.text(2, -0.5, f"q = {surcharge} kPa", ha='center', color='red', fontweight='bold', fontsize=8)

            for lay in layers:
                rect = patches.Rectangle((0, cur_d), 5, lay['H'], facecolor=lay['color'], edgecolor='black', alpha=0.6)
                ax_sch.add_patch(rect)
                mid_y = cur_d + lay['H']/2
                
                # Compact labels
                ax_sch.text(2.5, mid_y, lay['type'], ha='center', va='center', fontweight='bold', fontsize=9)
                ax_sch.annotate("", xy=(-0.2, cur_d), xytext=(-0.2, cur_d + lay['H']), arrowprops=dict(arrowstyle='<->'))
                ax_sch.text(-0.3, mid_y, f"{lay['H']}m", va='center', ha='right', fontsize=8)
                cur_d += lay['H']

            ax_sch.axhline(y=water_depth, color='blue', linestyle='--', linewidth=2)
            ax_sch.text(5.1, water_depth, "WT ▽", color='blue', va='center', fontsize=8)

            if hc > 0:
                c_top = max(0, water_depth - hc)
                rect_cap = patches.Rectangle((0, c_top), 5, water_depth - c_top, hatch='///', fill=False, edgecolor='blue', alpha=0.3)
                ax_sch.add_patch(rect_cap)
                ax_sch.text(5.1, c_top, f"Capillary\n({hc}m)", color='blue', va='center', fontsize=7)

            ax_sch.set_ylim(total_depth * 1.1, -1.5)
            ax_sch.set_xlim(-1, 6)
            ax_sch.axis('off')
            st.pyplot(fig_sch)

        # --- 5. CALCULATION LOGIC ---
        if st.button("Calculate Stress Profile", type="primary"):
            
            z_points = {0.0, total_depth} 
            
            run_z = 0
            for l in layers:
                run_z += l['H']
                z_points.add(round(run_z, 3))
            
            if 0 <= water_depth <= total_depth: z_points.add(water_depth)
            
            cap_top = water_depth - hc
            if 0 <= cap_top <= total_depth: z_points.add(cap_top)
            
            sorted_z = sorted(list(z_points))
            
            results = []
            calc_steps = []
            
            gamma_w = 9.81
            sigma_prev = surcharge
            z_prev = 0.0
            
            st.markdown("### 2. Detailed Calculations")
            
            for i, z in enumerate(sorted_z):
                
                # A. PORE PRESSURE
                if z > water_depth:
                    u_hydro = (z - water_depth) * gamma_w
                elif z > (water_depth - hc) and z <= water_depth:
                    u_hydro = -(water_depth - z) * gamma_w
                else:
                    u_hydro = 0.0
                
                # B. TOTAL STRESS
                if i == 0:
                    sigma = surcharge
                else:
                    dz = z - z_prev
                    z_mid = (z + z_prev) / 2
                    
                    active_layer = None
                    cur_l_bot = 0
                    for l in layers:
                        cur_l_bot += l['H']
                        if z_mid <= cur_l_bot:
                            active_layer = l
                            break
                    if active_layer is None: active_layer = layers[-1]

                    if z_mid > (water_depth - hc):
                        gamma_used = active_layer['g_sat']
                    else:
                        gamma_used = active_layer['g_dry']
                        
                    d_sigma = dz * gamma_used
                    sigma = sigma_prev + d_sigma
                    
                    calc_steps.append(f"**Interval {z_prev}m to {z}m:** {active_layer['type']} ($\gamma={gamma_used}$)")
                    calc_steps.append(f"$\\sigma_{{{z}}} = {sigma_prev:.2f} + ({gamma_used} \\times {dz:.2f}) = {sigma:.2f}$")

                # C. EXCESS PORE PRESSURE
                u_excess = 0.0
                
                active_layer_at_point = None
                r_z = 0
                for l in layers:
                    r_z += l['H']
                    if z <= r_z and z > (r_z - l['H']): 
                        active_layer_at_point = l
                        break
                
                if active_layer_at_point is None: active_layer_at_point = layers[-1]

                is_clay = active_layer_at_point['type'] == 'Clay'
                is_sat_zone = z > water_depth
                
                if "Short Term" in analysis_mode and is_clay and is_sat_zone:
                    u_excess = surcharge
                    calc_steps.append(f"*Short Term Clay Effect at z={z}: $\\Delta u = q = {surcharge}$*")

                u_total = u_hydro + u_excess
                sigma_p = sigma - u_total
                
                results.append({
                    "Depth (z)": z,
                    "Total Stress (σ)": sigma,
                    "u_hydro": u_hydro,
                    "u_excess": u_excess,
                    "Total Pore Pressure (u)": u_total,
                    "Eff. Stress (σ')": sigma_p
                })
                
                sigma_prev = sigma
                z_prev = z

            # --- OUTPUTS ---
            with st.expander("Show Calculation Log"):
                for line in calc_steps:
                    st.markdown(line)

            df = pd.DataFrame(results)
            
            # --- GRAPH ---
            st.markdown("### 3. Stress Profile Graph")
            fig, ax = plt.subplots(figsize=(8, 6))
            
            cur_h = 0
            for l in layers:
                cur_h += l['H']
                ax.axhspan(cur_h - l['H'], cur_h, facecolor=l['color'], alpha=0.3)
                ax.text(df['Total Stress (σ)'].max()*0.8, cur_h - l['H']/2, l['type'], ha='center', fontsize=9, alpha=0.5)

            ax.plot(df["Total Stress (σ)"], df["Depth (z)"], 'b-o', label=r"Total $\sigma$")
            ax.plot(df["Total Pore Pressure (u)"], df["Depth (z)"], 'r--x', label=r"Pore $u$")
            ax.plot(df["Eff. Stress (σ')"], df["Depth (z)"], 'k-s', linewidth=2, label=r"Effective $\sigma'$")
            
            ax.axhline(water_depth, color='blue', linestyle='-.', label="Water Table")
            
            ax.invert_yaxis()
            ax.set_xlabel("Stress (kPa)")
            ax.set_ylabel("Depth (m)")
            ax.grid(True, alpha=0.5)
            ax.legend()
            
            col_res1, col_res2 = st.columns([1, 2])
            with col_res1:
                st.dataframe(df[["Depth (z)", "Total Stress (σ)", "Total Pore Pressure (u)", "Eff. Stress (σ')"]].style.format("{:.2f}"))
            with col_res2:
                st.pyplot(fig)

    # ==================================================
    # TAB 2: HEAVE CHECK
    # ==================================================
    with tab2:
        st.subheader("Heave & Piping Analysis")
        st.info("Calculates safety against bottom heave for excavations in Clay over Artesian Sand.")
        
        c1, c2 = st.columns(2)
        with col1:
            h_clay_total = st.number_input("Total Thickness of Clay Layer (m)", 5.0, step=0.1)
            gamma_clay = st.number_input("Clay Unit Wt (kN/m³)", 20.0)
        with col2:
            artesian_head = st.number_input("Artesian Head above Surface (m)", 2.0)
            exc_depth = st.number_input("Excavation Depth (m)", 3.0)
        
        if st.button("Check Heave Safety"):
            remaining_clay = h_clay_total - exc_depth
            if remaining_clay <= 0:
                st.error("Excavation is deeper than clay layer!")
            else:
                sigma_down = remaining_clay * gamma_clay
                u_up = (h_clay_total + artesian_head) * 9.81
                fs = sigma_down / u_up
                
                st.latex(rf"FS = \frac{{\sigma_{{down}}}}{{u_{{up}}}} = \frac{{{remaining_clay:.2f} \times {gamma_c}}}{{{u_up:.2f}}} = \mathbf{{{fs:.3f}}}")
                
                if fs < 1.0: st.error("UNSAFE: Bottom Heave Predicted!")
                elif fs < 1.2: st.warning("Marginal Safety.")
                else: st.success("Safe.")
