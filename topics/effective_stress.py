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
        # 1. INPUTS (Side-by-Side with Visualizer)
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
        # 2. SOIL PROFILE VISUALIZER
        # -------------------------------------------------
        with col_viz:
            st.markdown("### Soil Profile Preview")
            
            fig, ax = plt.subplots(figsize=(6, 5))
            
            # 1. Draw Layers
            current_depth = 0
            for lay in layers:
                rect = patches.Rectangle((0, current_depth), 5, lay['H'], facecolor=lay['color'], edgecolor='black')
                ax.add_patch(rect)
                
                mid_y = current_depth + lay['H']/2
                label = f"{lay['type']}"
                ax.text(2.5, mid_y, label, ha='center', va='center', fontweight='bold', fontsize=10)
                ax.text(-0.2, mid_y, f"{lay['H']}m", ha='right', va='center', fontsize=9)
                current_depth += lay['H']

            # 2. Draw Surcharge
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

            ax.set_xlim(-1, 6)
            ax.set_ylim(total_depth * 1.1, -1.5)
            ax.axis('off')
            ax.plot([0, 5], [0, 0], 'k-', linewidth=2) 
            
            st.pyplot(fig)

        # -------------------------------------------------
        # 3. CALCULATION & RESULTS
        # -------------------------------------------------
        st.markdown("---")
        if st.button("Calculate Stress Profiles", type="primary"):
            
            # --- CREATE Z-POINTS ---
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
            
            # --- CALCULATION ENGINE ---
            def calculate_profile(mode_name, load_q):
                results = []
                math_logs = []
                
                sigma_prev = load_q
                z_prev = 0.0
                
                for i, z in enumerate(sorted_z):
                    
                    # A. Pore Pressure
                    u_calc_text = "0"
                    if z > water_depth:
                        u_h = (z - water_depth) * gamma_w
                        u_calc_text = f"({z} - {water_depth}) \\times 9.81"
                    elif z > (water_depth - hc):
                        u_h = -(water_depth - z) * gamma_w
                        u_calc_text = f"-({water_depth} - {z}) \\times 9.81"
                    else:
                        u_h = 0.0
                    
                    # B. Total Stress
                    if i > 0:
                        dz = z - z_prev
                        z_mid = (z + z_prev)/2
                        
                        # Find Layer
                        d_search = 0
                        active_l = layers[-1]
                        for l in layers:
                            d_search += l['H']
                            if z_mid <= d_search:
                                active_l = l
                                break
                        
                        # Find Gamma
                        eff_wt_boundary = water_depth - hc
                        if z_mid > eff_wt_boundary:
                            gam = active_l['g_sat']
                            g_sym = "\\gamma_{sat}"
                        else:
                            gam = active_l['g_dry']
                            g_sym = "\\gamma_{dry}"
                            
                        sigma = sigma_prev + (gam * dz)
                        
                        # FIXED: Added $ signs around the math expression in the log
                        math_logs.append(f"**Interval {z_prev}m to {z}m:** {active_l['type']} (${g_sym}={gam}$)")
                        math_logs.append(f"$\\sigma_{{{z}}} = {sigma_prev:.2f} + ({gam} \\times {dz:.2f}) = {sigma:.2f}$")
                    else:
                        sigma = load_q
                        math_logs.append(f"**Surface (z=0):** Load = {load_q} kPa")

                    # C. Excess Pore Pressure
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
                    
                    if mode_name == "Short Term" and load_q > 0 and is_clay and z > water_depth:
                        u_excess = load_q
                        u_calc_text += f" + {load_q} (Excess)"

                    u_tot = u_h + u_excess
                    sig_eff = sigma - u_tot
                    
                    math_logs.append(f"**@ z={z}m:**")
                    math_logs.append(f"$u = {u_calc_text} = {u_tot:.2f}$")
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

            # --- RUN 3 SCENARIOS ---
            df_init, log_init = calculate_profile("Initial", 0.0)        
            df_long, log_long = calculate_profile("Long Term", surcharge) 
            df_short, log_short = calculate_profile("Short Term", surcharge)

            # --- PLOTTING HELPER ---
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

            # --- DISPLAY 3 COLUMNS ---
            st.markdown("### Results Comparison")
            c_init, c_long, c_short = st.columns(3)

            # 1. INITIAL
            with c_init:
                st.subheader("Initial (No Load)")
                st.caption(f"q = 0 kPa")
                st.dataframe(df_init.style.format("{:.2f}"))
                fig1, ax1 = plt.subplots(figsize=(5, 6))
                plot_results(df_init, "Initial Profile", ax1)
                st.pyplot(fig1)
                
                with st.expander("Show Math (Initial)"):
                    for line in log_init:
                        if line.startswith("**") or line == "---": st.markdown(line)
                        else: st.latex(line.replace("$", ""))

            # 2. LONG TERM
            with c_long:
                st.subheader("Long Term (Drained)")
                st.caption(f"q = {surcharge} kPa | Excess u = 0")
                st.dataframe(df_long.style.format("{:.2f}"))
                fig2, ax2 = plt.subplots(figsize=(5, 6))
                plot_results(df_long, "Long Term Profile", ax2)
                st.pyplot(fig2)

                with st.expander("Show Math (Long Term)"):
                    for line in log_long:
                        if line.startswith("**") or line == "---": st.markdown(line)
                        else: st.latex(line.replace("$", ""))

            # 3. SHORT TERM
            with c_short:
                st.subheader("Short Term")
                st.caption(f"q = {surcharge} kPa | Excess u in Clay")
                st.dataframe(df_short.style.format("{:.2f}"))
                fig3, ax3 = plt.subplots(figsize=(5, 6))
                plot_results(df_short, "Short Term Profile", ax3)
                st.pyplot(fig3)

                with st.expander("Show Math (Short Term)"):
                    for line in log_short:
                        if line.startswith("**") or line == "---": st.markdown(line)
                        else: st.latex(line.replace("$", ""))

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
