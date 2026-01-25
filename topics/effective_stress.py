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
    # TAB 1 — STRESS PROFILE (Standard)
    # =====================================================
    with tab1:
        st.caption("Define soil layers, water table, and surcharge to calculate the stress profile.")

        # -------------------------------------------------
        # 1. INPUTS
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
                    
                    eff_wt = water_depth - hc
                    needs_dry = layer_top < eff_wt
                    needs_sat = layer_bot > eff_wt
                    
                    g_dry_input = 17.0
                    g_sat_input = 20.0
                    
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
        # 2. VISUALIZER
        # -------------------------------------------------
        with col_viz:
            st.markdown("### Soil Profile Preview")
            fig, ax = plt.subplots(figsize=(6, 5))
            
            current_depth = 0
            for lay in layers:
                rect = patches.Rectangle((0, current_depth), 5, lay['H'], facecolor=lay['color'], edgecolor='black')
                ax.add_patch(rect)
                mid_y = current_depth + lay['H']/2
                ax.text(2.5, mid_y, lay['type'], ha='center', va='center', fontweight='bold', fontsize=10)
                ax.text(-0.2, mid_y, f"{lay['H']}m", ha='right', va='center', fontsize=9)
                current_depth += lay['H']

            if surcharge > 0:
                for x in np.linspace(0.5, 4.5, 8):
                    ax.arrow(x, -0.5, 0, 0.4, head_width=0.15, head_length=0.1, fc='red', ec='red')
                ax.text(2.5, -0.6, f"q = {surcharge} kPa", ha='center', color='red', fontweight='bold', fontsize=9)

            ax.axhline(water_depth, color='blue', linestyle='--', linewidth=2)
            ax.text(5.1, water_depth, "WT ▽", color='blue', va='center', fontsize=9)

            if hc > 0:
                cap_top = max(0, water_depth - hc)
                rect_cap = patches.Rectangle((0, cap_top), 5, water_depth - cap_top, hatch='///', fill=False, edgecolor='blue', alpha=0.3)
                ax.add_patch(rect_cap)
                ax.text(5.1, cap_top, f"Capillary\n({hc}m)", color='blue', va='center', fontsize=8)

            ax.set_xlim(-1, 6)
            ax.set_ylim(total_depth * 1.1, -1.5)
            ax.axis('off')
            ax.plot([0, 5], [0, 0], 'k-', linewidth=2) 
            st.pyplot(fig)

        # -------------------------------------------------
        # 3. CALCULATE
        # -------------------------------------------------
        st.markdown("---")
        if st.button("Calculate Stress Profiles", type="primary"):
            
            z_points_set = {0.0, total_depth}
            cur = 0
            for l in layers:
                cur += l['H']
                z_points_set.add(round(cur, 3))
            
            if 0 < water_depth < total_depth: z_points_set.add(water_depth)
            
            cap_top = water_depth - hc
            if 0 < cap_top < total_depth: z_points_set.add(cap_top)
                
            for d in range(1, int(total_depth) + 1):
                z_points_set.add(float(d))

            sorted_z = sorted(list(z_points_set))
            
            def calculate_profile(mode_name, load_q):
                results = []
                math_logs = []
                sigma_prev = load_q
                z_prev = 0.0
                
                for i, z in enumerate(sorted_z):
                    
                    if z > water_depth:
                        u_h = (z - water_depth) * gamma_w
                        u_calc_text = f"({z} - {water_depth}) \\times 9.81"
                    elif z > (water_depth - hc):
                        u_h = -(water_depth - z) * gamma_w
                        u_calc_text = f"-({water_depth} - {z}) \\times 9.81"
                    else:
                        u_h = 0.0
                    
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
                            g_sym = "\\gamma_{sat}"
                        else:
                            gam = active_l['g_dry']
                            g_sym = "\\gamma_{dry}"
                            
                        sigma = sigma_prev + (gam * dz)
                        math_logs.append(f"**Interval {z_prev}m to {z}m:** {active_l['type']} (${g_sym}={gam}$)")
                        math_logs.append(f"$\\sigma_{{{z}}} = {sigma_prev:.2f} + ({gam} \\times {dz:.2f}) = {sigma:.2f}$")
                    else:
                        sigma = load_q
                        math_logs.append(f"**Surface (z=0):** Load = {load_q} kPa")

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
                    
                    u_calc_add = ""
                    if mode_name == "Short Term" and load_q > 0 and is_clay and z > water_depth:
                        u_excess = load_q
                        u_calc_add = f" + {load_q} (Excess)"

                    u_tot = u_h + u_excess
                    sig_eff = sigma - u_tot
                    
                    math_logs.append(f"**@ z={z}m:**")
                    math_logs.append(f"$u = {u_calc_text}{u_calc_add} = {u_tot:.2f}$")
                    math_logs.append(f"$\\sigma' = {sigma:.2f} - {u_tot:.2f} = \\mathbf{{{sig_eff:.2f}}}$")
                    math_logs.append("---")
                    
                    results.append({
                        "Depth (z)": z, 
                        "Total Stress (σ)": sigma, 
                        "Pore Pressure (u)": u_tot, 
                        "Eff. Stress (σ')": sig_eff
                    })
                    
                    sigma_prev = sigma
                    z_prev = z
                
                return pd.DataFrame(results), math_logs

            df_init, log_init = calculate_profile("Initial", 0.0)        
            df_long, log_long = calculate_profile("Long Term", surcharge) 
            df_short, log_short = calculate_profile("Short Term", surcharge)

            def plot_results(df, title, ax):
                ax.plot(df["Total Stress (σ)"], df["Depth (z)"], 'b-o', label=r"Total $\sigma$")
                ax.plot(df["Pore Pressure (u)"], df["Depth (z)"], 'r--x', label=r"Pore $u$")
                ax.plot(df["Eff. Stress (σ')"], df["Depth (z)"], 'k-s', linewidth=2, label=r"Effective $\sigma'$")
                
                cur_h = 0
                for l in layers:
                    cur_h += l['H']
                    ax.axhspan(cur_h - l['H'], cur_h, facecolor=l['color'], alpha=0.3)
                
                ax.axhline(water_depth, color='blue', linestyle='-.', alpha=0.5, label="WT")
                ax.invert_yaxis()
                ax.set_xlabel("Stress (kPa)")
                ax.set_ylabel("Depth (m)")
                ax.set_title(title)
                ax.grid(True, linestyle="--", alpha=0.6)
                ax.legend()

            st.markdown("### Results Comparison")
            c_init, c_long, c_short = st.columns(3)

            with c_init:
                st.subheader("Initial (No Load)")
                st.caption("q = 0 kPa")
                st.dataframe(df_init.style.format("{:.2f}"))
                fig1, ax1 = plt.subplots(figsize=(5, 6))
                plot_results(df_init, "Initial Profile", ax1)
                st.pyplot(fig1)
                with st.expander("Show Math"):
                    for line in log_init:
                        if line.startswith("**") or line == "---": st.markdown(line)
                        else: st.latex(line.replace("$", ""))

            with c_long:
                st.subheader("Long Term")
                st.caption(f"q = {surcharge} kPa | Δu = 0")
                st.dataframe(df_long.style.format("{:.2f}"))
                fig2, ax2 = plt.subplots(figsize=(5, 6))
                plot_results(df_long, "Long Term Profile", ax2)
                st.pyplot(fig2)
                with st.expander("Show Math"):
                    for line in log_long:
                        if line.startswith("**") or line == "---": st.markdown(line)
                        else: st.latex(line.replace("$", ""))

            with c_short:
                st.subheader("Short Term")
                st.caption(f"q = {surcharge} kPa | Excess u in Clay")
                st.dataframe(df_short.style.format("{:.2f}"))
                fig3, ax3 = plt.subplots(figsize=(5, 6))
                plot_results(df_short, "Short Term Profile", ax3)
                st.pyplot(fig3)
                with st.expander("Show Math"):
                    for line in log_short:
                        if line.startswith("**") or line == "---": st.markdown(line)
                        else: st.latex(line.replace("$", ""))

    # =====================================================
    # TAB 2 — HEAVE CHECK (REBUILT)
    # =====================================================
    with tab2:
        st.subheader("Heave & Piping Analysis")
        st.caption("Checks safety against bottom heave for excavations in Clay over Artesian Sand.")
        
        # -------------------------------------------------
        # 1. INPUTS
        # -------------------------------------------------
        col_h_input, col_h_viz = st.columns([1, 1.5])

        with col_h_input:
            st.markdown("#### Soil Parameters")
            h_clay = st.number_input("Total Clay Thickness (m)", value=8.0, step=0.5)
            d_exc = st.number_input("Excavation Depth (m)", value=5.0, step=0.5)
            g_clay = st.number_input("Clay Sat. Unit Weight (kN/m³)", value=19.0, step=0.1)
            h_art = st.number_input("Artesian Head Above Surface (m)", value=2.0, step=0.5)
            gamma_w = 9.81
            
            rem_clay = h_clay - d_exc
            st.info(f"Rem. Clay Thickness (Plug): **{rem_clay:.2f} m**")

        # -------------------------------------------------
        # 2. VISUALIZATION (THE "NOTEBOOK" STYLE)
        # -------------------------------------------------
        with col_h_viz:
            st.markdown("#### Cross-Section & Stress State")
            
            fig_h, ax_h = plt.subplots(figsize=(8, 5))
            
            # --- GEOMETRY ---
            # Ground Surface at y=0
            # Clay goes to y=h_clay
            # Sand is below h_clay
            
            # 1. Sand Layer (Bottom Base)
            ax_h.add_patch(patches.Rectangle((0, h_clay), 10, 4, facecolor='#E6D690', edgecolor='gray'))
            ax_h.text(5, h_clay + 2, "SAND (Artesian)", ha='center', fontweight='bold', alpha=0.5)

            # 2. Clay Layer (Full Width minus Excavation)
            # Left Bank
            ax_h.add_patch(patches.Rectangle((0, 0), 3, h_clay, facecolor='#B0A494', edgecolor='black'))
            # Right Bank
            ax_h.add_patch(patches.Rectangle((7, 0), 3, h_clay, facecolor='#B0A494', edgecolor='black'))
            # Bottom Plug (Below excavation)
            if rem_clay > 0:
                ax_h.add_patch(patches.Rectangle((3, d_exc), 4, rem_clay, facecolor='#8D6E63', edgecolor='black', hatch='.'))
                ax_h.text(5, d_exc + rem_clay/2, "Clay Plug", ha='center', va='center', color='white', fontweight='bold', fontsize=8)

            # 3. Excavation Void lines
            ax_h.plot([3, 3, 7, 7], [0, d_exc, d_exc, 0], 'k-', linewidth=2)
            
            # 4. Standpipe Piezometer (The "Sketch" style)
            # Pipe going into sand
            pipe_x = 1.5
            ax_h.plot([pipe_x, pipe_x], [-1, h_clay + 1], 'k-', linewidth=1.5) # Left wall
            ax_h.plot([pipe_x+0.2, pipe_x+0.2], [-1, h_clay + 1], 'k-', linewidth=1.5) # Right wall
            # Water level in pipe (Artesian Head)
            art_level_y = -h_art
            ax_h.plot([pipe_x, pipe_x+0.2], [art_level_y, art_level_y], 'b-', linewidth=2)
            # Triangle marker
            ax_h.plot([pipe_x+0.3], [art_level_y], marker='v', color='blue')
            ax_h.text(pipe_x+0.5, art_level_y, f"Piezometric Level\n(+{h_art}m)", color='blue', va='center', fontsize=8)

            # 5. Stress Profile Diagram (Right Side Overlay)
            # We will draw the U and Sigma lines corresponding to the interface
            # Origin x for stress graph = 8.5
            x_origin = 8.5
            # Depth of interface = h_clay
            
            # Values
            u_val = (h_clay + h_art) * gamma_w
            sig_val = rem_clay * g_clay
            
            # Draw Axes for Stress
            ax_h.plot([x_origin, x_origin], [0, h_clay+2], 'k-', linewidth=1) # Vertical axis
            ax_h.text(x_origin, -0.5, "Stress", ha='center')
            
            # Plot U (Linear increase from Piezometric Level)
            # U is 0 at -h_art, increases to u_val at h_clay
            # We represent magnitude as X-distance from origin
            scale = 1.5 / max(u_val, sig_val + 1) # Scaling factor for visualization
            
            # Draw U triangle
            ax_h.plot([x_origin, x_origin + u_val*scale], [h_clay, h_clay], 'r-', linewidth=2) # Base vector
            ax_h.plot([x_origin, x_origin + u_val*scale], [-h_art, h_clay], 'r--', linewidth=1) # Line from 0
            ax_h.text(x_origin + u_val*scale, h_clay, f" U = {u_val:.1f}", color='red', fontsize=8, ha='left', va='bottom')
            
            # Draw Sigma Rectangle (Weight of Plug)
            # Starts at d_exc, goes to h_clay. Value is 0 at top of plug? No, weight accumulates.
            # Sigma is 0 at d_exc, increases to sig_val at h_clay
            ax_h.plot([x_origin, x_origin + sig_val*scale], [h_clay, h_clay], 'b-', linewidth=2) # Base vector
            ax_h.plot([x_origin, x_origin + sig_val*scale], [d_exc, h_clay], 'b--', linewidth=1) # Line
            ax_h.text(x_origin + sig_val*scale, h_clay, f" W = {sig_val:.1f}", color='blue', fontsize=8, ha='left', va='top')

            # Failure Plane Line
            ax_h.axhline(h_clay, color='red', linestyle=':', linewidth=1)
            ax_h.text(0.5, h_clay-0.2, "Critical Interface", color='red', fontsize=8)

            ax_h.set_ylim(h_clay + 3, -h_art - 2)
            ax_h.set_xlim(0, 12)
            ax_h.axis('off')
            
            # Ground Line
            ax_h.plot([0, 10], [0, 0], 'k-', linewidth=1)
            
            st.pyplot(fig_h)

        # -------------------------------------------------
        # 3. CALCULATION
        # -------------------------------------------------
        if st.button("Calculate Factor of Safety", type="primary"):
            if rem_clay <= 0:
                st.error("Invalid: Excavation deeper than clay layer.")
            else:
                sigma_down = rem_clay * g_clay
                head_total = h_clay + h_art
                u_up = head_total * gamma_w
                fs = sigma_down / u_up
                
                c_res_l, c_res_r = st.columns([1, 1.5])
                
                with c_res_l:
                    if fs < 1.0:
                        st.error(f"**FS = {fs:.3f}** (UNSAFE)")
                    elif fs < 1.2:
                        st.warning(f"**FS = {fs:.3f}** (MARGINAL)")
                    else:
                        st.success(f"**FS = {fs:.3f}** (SAFE)")

                with c_res_r:
                    with st.expander("Show Detailed Math", expanded=True):
                        st.markdown("**1. Downward Stress (Weight of Plug)**")
                        st.latex(rf"\sigma_v = H_{{plug}} \times \gamma_{{clay}} = {rem_clay:.2f} \times {g_clay} = \mathbf{{{sigma_down:.2f} \, kPa}}")
                        
                        st.markdown("**2. Upward Pressure (Artesian)**")
                        st.latex(rf"u = (H_{{clay}} + h_{{art}}) \times \gamma_w = ({h_clay} + {h_art}) \times 9.81 = \mathbf{{{u_up:.2f} \, kPa}}")
                        
                        st.markdown("**3. Factor of Safety**")
                        st.latex(rf"FS = \frac{{\sigma_v}}{{u}} = \frac{{{sigma_down:.2f}}}{{{u_up:.2f}}} = \mathbf{{{fs:.3f}}}")

if __name__ == "__main__":
    app()
