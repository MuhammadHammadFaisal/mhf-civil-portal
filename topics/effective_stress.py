import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# =========================================================
# APP CONFIG
# =========================================================
st.set_page_config(
    page_title="Advanced Soil Stress Analysis",
    layout="wide",
)

# =========================================================
# MAIN APP
# =========================================================
def app():
    st.title("Advanced Effective Stress Analysis")
    st.markdown("---")

    tab1, tab2 = st.tabs(["Stress Profile Calculator", "Heave Check"])

    # =====================================================
    # TAB 1 — STRESS PROFILE
    # =====================================================
    with tab1:
        st.caption("Define soil layers, water table, and surcharge to calculate the stress profile.")

        # -------------------------------------------------
        # 1. ANALYSIS SETTINGS & GLOBAL INPUTS
        # -------------------------------------------------
        col_glob1, col_glob2 = st.columns(2)
        with col_glob1:
            analysis_mode = st.radio(
                "Analysis Condition:", 
                ["Long Term (Drained)", "Short Term (Undrained)"],
                help="Short Term: Surcharge creates excess pore pressure in CLAY layers."
            )
        
        with col_glob2:
            st.info("💡 **Interactive Diagram:** The graph below now overlays the **Initial Total Stress ($\sigma_v$)** profile on top of the soil layers.")

        st.divider()

        # -------------------------------------------------
        # 2. INPUTS (Side-by-Side with Visualizer)
        # -------------------------------------------------
        col_input, col_viz = st.columns([1.1, 1])

        with col_input:
            st.markdown("### A. Global Parameters")
            c1, c2, c3 = st.columns(3)
            with c1:
                water_depth = st.number_input("Water Table Depth (m)", value=3.0, step=0.5)
            with c2:
                hc = st.number_input("Capillary Rise (m)", value=0.0, step=0.1)
            with c3:
                surcharge = st.number_input("Surcharge q (kPa)", value=50.0, step=5.0)
                gamma_w = 9.81

            st.markdown("### B. Stratigraphy")
            num_layers = st.number_input("Number of Layers", 1, 5, 2)
            layers = []
            colors = {"Sand": "#E6D690", "Clay": "#B0A494"}
            
            depth_tracker = 0.0

            for i in range(int(num_layers)):
                with st.expander(f"Layer {i+1} (Top at {depth_tracker:.1f}m)", expanded=True):
                    cols = st.columns(4)
                    soil_type = cols[0].selectbox(f"Type", ["Sand", "Clay"], key=f"t{i}")
                    thickness = cols[1].number_input(f"Height (m)", 0.1, 20.0, 4.0, step=0.5, key=f"h{i}")
                    
                    layer_top = depth_tracker
                    layer_bot = depth_tracker + thickness
                    
                    # --- LOGIC TO DETERMINE REQUIRED INPUTS ---
                    eff_wt = water_depth - hc
                    
                    # 1. Is any part of layer DRY? (Above eff_wt)
                    needs_dry = layer_top < eff_wt
                    
                    # 2. Is any part of layer WET? (Below eff_wt)
                    needs_sat = layer_bot > eff_wt
                    
                    # 3. Default Values
                    g_dry_input = 17.0
                    g_sat_input = 20.0
                    
                    # --- RENDER INPUTS ---
                    if needs_sat:
                        g_sat_input = cols[2].number_input(f"γ_sat", value=20.0, key=f"gs{i}")
                    else:
                        cols[2].text_input(f"γ_sat", value="N/A", disabled=True, key=f"gs_dis_{i}")

                    if needs_dry:
                        g_dry_input = cols[3].number_input(f"γ_dry", value=17.0, key=f"gd{i}")
                    else:
                        cols[3].text_input(f"γ_dry", value="N/A", disabled=True, key=f"gd_dis_{i}")

                    layers.append({
                        "type": soil_type, "H": thickness, 
                        "g_sat": g_sat_input, "g_dry": g_dry_input, 
                        "color": colors[soil_type]
                    })
                    depth_tracker += thickness
            
            total_depth = depth_tracker

        # -------------------------------------------------
        # 3. SOIL PROFILE VISUALIZER + INITIAL STRESS
        # -------------------------------------------------
        with col_viz:
            st.markdown("### Soil Profile & Initial Stress")
            
            fig, ax = plt.subplots(figsize=(6, 5))
            
            # --- PRE-CALCULATE INITIAL STRESS POINTS FOR PLOTTING ---
            stress_z = [0.0]
            stress_val = [surcharge]
            current_sigma = surcharge
            current_d = 0.0
            
            # 1. Draw Layers & Accumulate Stress
            for lay in layers:
                # Background Layer
                rect = patches.Rectangle((0, current_d), 1, lay['H'], facecolor=lay['color'], edgecolor='black', alpha=0.7, transform=ax.get_yaxis_transform())
                # Note: We use transformation to mix axes types later, but simple rect is easiest on primary axis
                # Let's stick to standard plotting
                ax.add_patch(patches.Rectangle((0, current_d), 5, lay['H'], facecolor=lay['color'], edgecolor='gray', alpha=0.5))
                
                # Label
                mid_y = current_d + lay['H']/2
                l_top = current_d
                l_bot = current_d + lay['H']
                eff_wt = water_depth - hc
                
                label = f"{lay['type']}"
                ax.text(0.5, mid_y, label, ha='left', va='center', fontsize=9, fontweight='bold', color='#333')
                
                # Height Marker
                ax.text(-0.1, mid_y, f"{lay['H']}m", ha='right', va='center', fontsize=8)
                
                # --- STRESS CALCULATION FOR PREVIEW ---
                # We need to split if it crosses WT to draw the stress line correctly (slope change)
                if l_top < eff_wt and l_bot > eff_wt:
                    # Split Layer
                    h_dry = eff_wt - l_top
                    h_sat = l_bot - eff_wt
                    
                    # Part 1 (Dry)
                    current_sigma += lay['g_dry'] * h_dry
                    stress_z.append(eff_wt)
                    stress_val.append(current_sigma)
                    
                    # Part 2 (Sat)
                    current_sigma += lay['g_sat'] * h_sat
                    stress_z.append(l_bot)
                    stress_val.append(current_sigma)
                else:
                    # Single Phase
                    gamma = lay['g_sat'] if l_top >= eff_wt else lay['g_dry']
                    current_sigma += gamma * lay['H']
                    stress_z.append(l_bot)
                    stress_val.append(current_sigma)

                current_d += lay['H']

            # 2. Draw Surcharge Visuals
            if surcharge > 0:
                for x in np.linspace(0.5, 4.5, 8):
                    ax.arrow(x, -0.5, 0, 0.4, head_width=0.15, head_length=0.1, fc='red', ec='red')
                ax.text(2.5, -0.6, f"q = {surcharge} kPa", ha='center', color='red', fontweight='bold', fontsize=9)

            # 3. Draw Water Table
            ax.axhline(water_depth, color='blue', linestyle='--', linewidth=2)
            ax.text(5.1, water_depth, "WT ▽", color='blue', va='center', fontsize=9)

            # 4. Capillary Rise
            if hc > 0:
                cap_top = max(0, water_depth - hc)
                rect_cap = patches.Rectangle((0, cap_top), 5, water_depth - cap_top, hatch='///', fill=False, edgecolor='blue', alpha=0.3)
                ax.add_patch(rect_cap)
                ax.text(5.1, cap_top, f"Capillary\n({hc}m)", color='blue', va='center', fontsize=8)

            # --- 5. OVERLAY STRESS GRAPH (TWIN AXIS) ---
            ax_stress = ax.twiny() # Create top X-axis for Stress
            ax_stress.plot(stress_val, stress_z, color='red', linewidth=2, marker='o', markersize=4, label="Total Stress (σ)")
            
            # Formatting Twin Axis
            ax_stress.set_xlabel(r"Initial Total Stress $\sigma_v$ (kPa)", color='red', fontsize=9)
            ax_stress.tick_params(axis='x', labelcolor='red', labelsize=8)
            ax_stress.spines['top'].set_color('red')
            
            # Ensure 0 is visible
            xmax = max(stress_val) * 1.2
            ax_stress.set_xlim(0, xmax)

            # Primary Axis Formatting
            ax.set_ylim(total_depth * 1.1, -1.5)
            ax.set_xlim(0, 6)
            ax.set_xticks([]) # Hide bottom X axis
            ax.set_ylabel("Depth (m)")
            
            # Ground Line
            ax.plot([0, 5], [0, 0], 'k-', linewidth=2) 
            
            st.pyplot(fig)

        # -------------------------------------------------
        # 4. CALCULATION & RESULTS
        # -------------------------------------------------
        st.markdown("---")
        if st.button("Calculate Stress Profile", type="primary"):
            
            # --- 1. CREATE Z-POINTS (Discretization) ---
            z_points_set = {0.0, total_depth}
            cur = 0
            for l in layers:
                cur += l['H']
                z_points_set.add(round(cur, 3))
            
            if 0 < water_depth < total_depth: z_points_set.add(water_depth)
            
            cap_top = water_depth - hc
            if 0 < cap_top < total_depth: z_points_set.add(cap_top)
                
            # Add Regular 1m Intervals
            for d in range(1, int(total_depth) + 1):
                z_points_set.add(float(d))

            sorted_z = sorted(list(z_points_set))
            
            # --- 2. CALCULATION FUNCTION ---
            def calculate_profile(mode_name):
                results = []
                sigma_prev = surcharge
                z_prev = 0.0
                
                for i, z in enumerate(sorted_z):
                    
                    # --- A. Pore Pressure (u) ---
                    if z > water_depth:
                        u_h = (z - water_depth) * gamma_w
                    elif z > (water_depth - hc):
                        u_h = -(water_depth - z) * gamma_w
                    else:
                        u_h = 0.0
                    
                    # --- B. Total Stress (Sigma) ---
                    if i > 0:
                        dz = z - z_prev
                        z_mid = (z + z_prev)/2
                        
                        d_search = 0
                        active_l = layers[-1]
                        for l in layers:
                            d_search += l['H']
                            if z_mid <= d_search:
                                active_l = l
                                break
                        
                        eff_wt_boundary = water_depth - hc
                        if z_mid > eff_wt_boundary:
                            gam = active_l['g_sat']
                        else:
                            gam = active_l['g_dry']
                            
                        sigma = sigma_prev + (gam * dz)
                    else:
                        sigma = surcharge

                    # --- C. Excess Pore Pressure (Undrained Clay) ---
                    u_excess = 0.0
                    check_z = z
                    if i > 0 and z == total_depth: check_z = z - 0.01 
                    
                    d_check = 0
                    is_clay = False
                    for l in layers:
                        d_check += l['H']
                        if check_z <= d_check:
                            if l['type'] == 'Clay': is_clay = True
                            break
                    
                    if mode_name == "Short Term" and is_clay and z > water_depth:
                        u_excess = surcharge

                    u_tot = u_h + u_excess
                    sig_eff = sigma - u_tot
                    
                    results.append({
                        "Depth (z)": z, 
                        "Total Stress (σ)": sigma, 
                        "Pore Pressure (u)": u_tot, 
                        "Eff. Stress (σ')": sig_eff
                    })
                    
                    sigma_prev = sigma
                    z_prev = z
                
                return pd.DataFrame(results)

            # --- 3. RUN CALCULATIONS ---
            df_long = calculate_profile("Long Term")
            df_short = calculate_profile("Short Term")

            # --- 4. DISPLAY SIDE-BY-SIDE ---
            st.markdown("### Results Comparison")
            
            col_res_L, col_res_R = st.columns(2)

            # === LEFT: LONG TERM ===
            with col_res_L:
                st.subheader("Long Term (Drained)")
                st.caption("Excess Pore Pressure = 0")
                st.dataframe(df_long.style.format("{:.2f}"))
                
                fig_L, ax_L = plt.subplots(figsize=(6, 5))
                ax_L.plot(df_long["Total Stress (σ)"], df_long["Depth (z)"], 'b-o', label=r"Total $\sigma$")
                ax_L.plot(df_long["Pore Pressure (u)"], df_long["Depth (z)"], 'r--x', label=r"Pore $u$")
                ax_L.plot(df_long["Eff. Stress (σ')"], df_long["Depth (z)"], 'k-s', linewidth=2, label=r"Effective $\sigma'$")
                ax_L.axhline(water_depth, color='blue', linestyle='-.', alpha=0.5, label="WT")
                
                cur_h = 0
                for l in layers:
                    cur_h += l['H']
                    ax_L.axhspan(cur_h - l['H'], cur_h, facecolor=l['color'], alpha=0.3)

                ax_L.invert_yaxis()
                ax_L.set_xlabel("Stress (kPa)")
                ax_L.set_ylabel("Depth (m)")
                ax_L.grid(True, linestyle="--", alpha=0.6)
                ax_L.legend()
                st.pyplot(fig_L)

            # === RIGHT: SHORT TERM ===
            with col_res_R:
                st.subheader("Short Term (Undrained)")
                st.caption(f"Excess Pore Pressure in Clay = q ({surcharge} kPa)")
                st.dataframe(df_short.style.format("{:.2f}"))
                
                fig_S, ax_S = plt.subplots(figsize=(6, 5))
                ax_S.plot(df_short["Total Stress (σ)"], df_short["Depth (z)"], 'b-o', label=r"Total $\sigma$")
                ax_S.plot(df_short["Pore Pressure (u)"], df_short["Depth (z)"], 'r--x', label=r"Pore $u$")
                ax_S.plot(df_short["Eff. Stress (σ')"], df_short["Depth (z)"], 'k-s', linewidth=2, label=r"Effective $\sigma'$")
                ax_S.axhline(water_depth, color='blue', linestyle='-.', alpha=0.5, label="WT")
                
                cur_h = 0
                for l in layers:
                    cur_h += l['H']
                    ax_S.axhspan(cur_h - l['H'], cur_h, facecolor=l['color'], alpha=0.3)

                ax_S.invert_yaxis()
                ax_S.set_xlabel("Stress (kPa)")
                ax_S.set_ylabel("Depth (m)")
                ax_S.grid(True, linestyle="--", alpha=0.6)
                ax_S.legend()
                st.pyplot(fig_S)

    # =====================================================
    # TAB 2 — HEAVE CHECK
    # =====================================================
    with tab2:
        st.subheader("Bottom Heave Check")
        c1, c2 = st.columns(2)
        with c1:
            h_clay = st.number_input("Clay Thickness (m)", value=5.0)
            g_clay = st.number_input("Clay Unit Weight", value=20.0)
        with c2:
            h_art = st.number_input("Artesian Head (m)", value=2.0)
            d_exc = st.number_input("Excavation Depth (m)", value=3.0)
            
        if st.button("Calculate FS"):
            rem = h_clay - d_exc
            if rem <= 0:
                st.error("Invalid Geometry")
            else:
                s_down = rem * g_clay
                u_up = (h_clay + h_art) * 9.81
                fs = s_down / u_up
                st.latex(rf"FS = \frac{{{s_down:.2f}}}{{{u_up:.2f}}} = \mathbf{{{fs:.2f}}}")
                if fs < 1.0: st.error("Unsafe")
                else: st.success("Safe")

if __name__ == "__main__":
    app()
