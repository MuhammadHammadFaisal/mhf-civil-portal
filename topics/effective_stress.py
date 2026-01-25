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
        # 1. GLOBAL INPUTS
        # -------------------------------------------------
        st.info("💡 **Comparison Mode:** Both Long Term (Drained) and Short Term (Undrained) conditions will be calculated side-by-side.")
        
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
        # 3. SOIL PROFILE VISUALIZER
        # -------------------------------------------------
        with col_viz:
            st.markdown("### Soil Profile Preview")
            
            fig, ax = plt.subplots(figsize=(6, 5))
            
            # Draw Surcharge
            if surcharge > 0:
                for x in np.linspace(0.5, 4.5, 8):
                    ax.arrow(x, -0.5, 0, 0.4, head_width=0.15, head_length=0.1, fc='red', ec='red')
                ax.text(2.5, -0.6, f"q = {surcharge} kPa", ha='center', color='red', fontweight='bold')

            # Draw Layers
            current_depth = 0
            for lay in layers:
                rect = patches.Rectangle((0, current_depth), 5, lay['H'], facecolor=lay['color'], edgecolor='black')
                ax.add_patch(rect)
                
                mid_y = current_depth + lay['H']/2
                
                # Dynamic Labeling based on what inputs were active
                l_top = current_depth
                l_bot = current_depth + lay['H']
                eff_wt = water_depth - hc
                
                label = f"{lay['type']}\n"
                if l_top < eff_wt and l_bot > eff_wt: # Crossing
                    label += f"$\\gamma_{{d}}={lay['g_dry']}$ / $\\gamma_{{s}}={lay['g_sat']}$"
                elif l_bot <= eff_wt: # Fully Dry
                    label += f"$\\gamma_{{dry}}={lay['g_dry']}$"
                else: # Fully Sat
                    label += f"$\\gamma_{{sat}}={lay['g_sat']}$"

                ax.text(2.5, mid_y, label, ha='center', va='center', fontsize=8)
                ax.text(-0.2, mid_y, f"{lay['H']}m", ha='right', va='center', fontsize=9)
                current_depth += lay['H']

            # Draw Water Table
            ax.axhline(water_depth, color='blue', linestyle='--', linewidth=2)
            ax.text(5.1, water_depth, "WT ▽", color='blue', va='center')

            # Draw Capillary Rise
            if hc > 0:
                cap_top = water_depth - hc
                if cap_top < 0: cap_top = 0
                rect_cap = patches.Rectangle((0, cap_top), 5, water_depth - cap_top, hatch='///', fill=False, edgecolor='blue', alpha=0.3)
                ax.add_patch(rect_cap)
                ax.text(5.1, cap_top, f"Capillary\n({hc}m)", color='blue', va='center', fontsize=8)

            ax.set_xlim(-1, 6)
            ax.set_ylim(total_depth * 1.1, -1.5)
            ax.axis('off')
            ax.plot([0, 5], [0, 0], 'k-', linewidth=2) 
            
            st.pyplot(fig)

        # -------------------------------------------------
        # 4. CALCULATION & RESULTS
        # -------------------------------------------------
        st.markdown("---")
        if st.button("Calculate Stress Profiles", type="primary"):
            
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
                    
                    # --- A. Pore Pressure (u_hydro) ---
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
            st.markdown("### Results: Long Term vs Short Term")
            
            # Create two main columns for the layout
            col_res_L, col_res_R = st.columns(2)

            # === LEFT: LONG TERM ===
            with col_res_L:
                st.subheader("Long Term (Drained)")
                st.caption("Excess Pore Pressure = 0")
                
                # Table
                st.dataframe(df_long.style.format("{:.2f}"))
                
                # Plot
                fig_L, ax_L = plt.subplots(figsize=(6, 5))
                ax_L.plot(df_long["Total Stress (σ)"], df_long["Depth (z)"], 'b-o', label=r"Total $\sigma$")
                ax_L.plot(df_long["Pore Pressure (u)"], df_long["Depth (z)"], 'r--x', label=r"Pore $u$")
                ax_L.plot(df_long["Eff. Stress (σ')"], df_long["Depth (z)"], 'k-s', linewidth=2, label=r"Effective $\sigma'$")
                
                ax_L.axhline(water_depth, color='blue', linestyle='-.', alpha=0.5, label="WT")
                
                # Draw Layers BG
                cur_h = 0
                for l in layers:
                    cur_h += l['H']
                    ax_L.axhspan(cur_h - l['H'], cur_h, facecolor=l['color'], alpha=0.3)

                ax_L.invert_yaxis()
                ax_L.set_xlabel("Stress (kPa)")
                ax_L.set_ylabel("Depth (m)")
                ax_L.set_title("Long Term Profile")
                ax_L.grid(True, linestyle="--", alpha=0.6)
                ax_L.legend()
                st.pyplot(fig_L)

            # === RIGHT: SHORT TERM ===
            with col_res_R:
                st.subheader("Short Term (Undrained)")
                st.caption(f"Excess Pore Pressure in Clay = q ({surcharge} kPa)")
                
                # Table
                st.dataframe(df_short.style.format("{:.2f}"))
                
                # Plot
                fig_S, ax_S = plt.subplots(figsize=(6, 5))
                ax_S.plot(df_short["Total Stress (σ)"], df_short["Depth (z)"], 'b-o', label=r"Total $\sigma$")
                ax_S.plot(df_short["Pore Pressure (u)"], df_short["Depth (z)"], 'r--x', label=r"Pore $u$")
                ax_S.plot(df_short["Eff. Stress (σ')"], df_short["Depth (z)"], 'k-s', linewidth=2, label=r"Effective $\sigma'$")
                
                ax_S.axhline(water_depth, color='blue', linestyle='-.', alpha=0.5, label="WT")
                
                # Draw Layers BG
                cur_h = 0
                for l in layers:
                    cur_h += l['H']
                    ax_S.axhspan(cur_h - l['H'], cur_h, facecolor=l['color'], alpha=0.3)

                ax_S.invert_yaxis()
                ax_S.set_xlabel("Stress (kPa)")
                ax_S.set_ylabel("Depth (m)")
                ax_S.set_title("Short Term Profile")
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
