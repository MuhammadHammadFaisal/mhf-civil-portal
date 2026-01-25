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
            st.info("💡 **Diagram Logic:** The schematic below updates automatically as you add layers or change the water table.")

        st.divider()

        # -------------------------------------------------
        # 2. INPUTS (Side-by-Side with Visualizer)
        # -------------------------------------------------
        col_input, col_viz = st.columns([1, 1])

        with col_input:
            st.markdown("### A. Global Parameters")
            c1, c2, c3 = st.columns(3)
            with c1:
                water_depth = st.number_input("Water Table Depth (m)", value=2.0, step=0.5)
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
                    
                    # Logic: Only ask for relevant Unit Weight
                    layer_bot = depth_tracker + thickness
                    is_sat = layer_bot > (water_depth - hc)
                    
                    if is_sat:
                        g_sat = cols[2].number_input(f"γ_sat", value=20.0, key=f"gs{i}")
                        g_dry = 18.0 # Default
                    else:
                        g_sat = 20.0 # Default
                        cols[2].markdown("*(Dry)*")
                    
                    if not is_sat:
                        g_dry = cols[3].number_input(f"γ_dry", value=18.0, key=f"gd{i}")
                    else:
                        cols[3].markdown("*(Sat)*")

                    layers.append({
                        "type": soil_type, "H": thickness, 
                        "g_sat": g_sat, "g_dry": g_dry, 
                        "color": colors[soil_type]
                    })
                    depth_tracker += thickness
            
            total_depth = depth_tracker

        # -------------------------------------------------
        # 3. SOIL PROFILE VISUALIZER (The "Correct" Diagram)
        # -------------------------------------------------
        with col_viz:
            st.markdown("### Soil Profile Preview")
            
            # Create Plot
            fig, ax = plt.subplots(figsize=(6, 5))
            
            # 1. Draw Surcharge (q) Arrows
            if surcharge > 0:
                arrow_y_start = -0.5  # Slightly above ground
                arrow_y_end = 0       # Ground surface
                for x in np.linspace(0.5, 4.5, 8):
                    ax.arrow(x, arrow_y_start, 0, 0.4, head_width=0.15, head_length=0.1, fc='red', ec='red')
                ax.text(2.5, -0.6, f"q = {surcharge} kPa", ha='center', color='red', fontweight='bold')

            # 2. Draw Layers
            current_depth = 0
            for lay in layers:
                # Rectangle (x, y, width, height)
                # Note: y increases downwards in our logic, but matplotlib y increases upwards.
                # We will invert y-axis at the end.
                rect = patches.Rectangle((0, current_depth), 5, lay['H'], facecolor=lay['color'], edgecolor='black')
                ax.add_patch(rect)
                
                # Center Text (Layer Info)
                mid_y = current_depth + lay['H']/2
                label_text = f"{lay['type']}\n"
                
                # Check which gamma is active for display
                if mid_y > (water_depth - hc):
                    label_text += f"$\\gamma_{{sat}}={lay['g_sat']}$"
                else:
                    label_text += f"$\\gamma_{{dry}}={lay['g_dry']}$"
                
                ax.text(2.5, mid_y, label_text, ha='center', va='center', fontsize=9)
                
                # Height Dimension
                ax.text(-0.2, mid_y, f"{lay['H']}m", ha='right', va='center', fontsize=9)
                
                current_depth += lay['H']

            # 3. Draw Water Table
            ax.axhline(water_depth, color='blue', linestyle='--', linewidth=2)
            ax.text(5.1, water_depth, "WT ▽", color='blue', va='center')

            # 4. Capillary Rise
            if hc > 0:
                cap_top = water_depth - hc
                if cap_top < 0: cap_top = 0
                rect_cap = patches.Rectangle((0, cap_top), 5, water_depth - cap_top, hatch='///', fill=False, edgecolor='blue', alpha=0.3)
                ax.add_patch(rect_cap)
                ax.text(5.1, cap_top, f"Capillary\n({hc}m)", color='blue', va='center', fontsize=8)

            # Styling
            ax.set_xlim(-1, 6)
            ax.set_ylim(total_depth * 1.1, -1.5) # Invert Y-axis to show depth downwards
            ax.axis('off') # Turn off standard axis
            
            # Ground Line
            ax.plot([0, 5], [0, 0], 'k-', linewidth=2) 
            
            st.pyplot(fig)

        # -------------------------------------------------
        # 4. CALCULATION & RESULTS
        # -------------------------------------------------
        st.markdown("---")
        if st.button("Calculate Stress Profile", type="primary"):
            
            # Discretize Depths
            z_points = {0.0, total_depth}
            cur = 0
            for l in layers:
                cur += l['H']
                z_points.add(round(cur, 3))
            
            if 0 < water_depth < total_depth: z_points.add(water_depth)
            if hc > 0:
                ct = water_depth - hc
                if 0 < ct < total_depth: z_points.add(ct)
                
            sorted_z = sorted(list(z_points))
            
            results = []
            sigma_prev = surcharge
            z_prev = 0.0
            
            for i, z in enumerate(sorted_z):
                # Pore Pressure
                if z > water_depth:
                    u = (z - water_depth) * gamma_w
                elif z > (water_depth - hc):
                    u = -(water_depth - z) * gamma_w
                else:
                    u = 0.0
                
                # Total Stress
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
                    
                    # Gamma
                    gam = active_l['g_sat'] if z_mid > (water_depth - hc) else active_l['g_dry']
                    sigma = sigma_prev + (gam * dz)
                else:
                    sigma = surcharge

                # Excess Pore Pressure (Short Term Clay)
                u_excess = 0.0
                # Check if Clay
                check_d = 0
                is_clay = False
                for l in layers:
                    check_d += l['H']
                    if z <= check_d and z > (check_d - l['H']):
                        if l['type'] == 'Clay': is_clay = True
                        break
                
                if "Short Term" in analysis_mode and is_clay and z > water_depth:
                    u_excess = surcharge

                u_tot = u + u_excess
                sig_eff = sigma - u_tot
                
                results.append({"Depth (z)": z, "Total Stress (σ)": sigma, "Pore Pressure (u)": u_tot, "Eff. Stress (σ')": sig_eff})
                
                sigma_prev = sigma
                z_prev = z
            
            df = pd.DataFrame(results)
            
            # Display Results
            st.markdown("### Results")
            c_res1, c_res2 = st.columns([1, 2])
            
            with c_res1:
                st.dataframe(df.style.format("{:.2f}"))
            
            with c_res2:
                fig_res, ax_res = plt.subplots(figsize=(8, 6))
                ax_res.plot(df["Total Stress (σ)"], df["Depth (z)"], 'b-o', label=r"Total $\sigma$")
                ax_res.plot(df["Pore Pressure (u)"], df["Depth (z)"], 'r--x', label=r"Pore $u$")
                ax_res.plot(df["Eff. Stress (σ')"], df["Depth (z)"], 'k-s', linewidth=2, label=r"Effective $\sigma'$")
                
                ax_res.invert_yaxis()
                ax_res.set_xlabel("Stress (kPa)")
                ax_res.set_ylabel("Depth (m)")
                ax_res.grid(True, linestyle="--")
                ax_res.legend()
                ax_res.set_title("Stress Distribution")
                st.pyplot(fig_res)

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
