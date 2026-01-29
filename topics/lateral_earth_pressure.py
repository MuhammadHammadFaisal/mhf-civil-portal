import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# =========================================================
# APP CONFIG
# =========================================================
# st.set_page_config(page_title="Lateral Earth Pressure", layout="wide") 
GAMMA_W = 9.81

def app():
    st.title("Lateral Earth Pressure Calculator 🧱")
    st.markdown("---")
    
    tab_rankine, tab_coulomb = st.tabs(["1. Rankine's Theory (Wall Profile)", "2. Coulomb's Wedge Theory"])

    # =========================================================================
    # TAB 1: RANKINE'S THEORY
    # =========================================================================
    with tab_rankine:
        st.header("Rankine Analysis")
        st.info("Configure the wall and soil layers on the left, then click Calculate.")

        # --- LAYOUT: INPUTS (Left) | VISUALIZATION (Right) ---
        col_input, col_viz = st.columns([0.4, 0.6], gap="medium")

        # -------------------------------------------------
        # 1. INPUT PANEL (LEFT COLUMN)
        # -------------------------------------------------
        with col_input:
            st.subheader("1. Wall Geometry")
            wall_height = st.number_input("Total Wall Height (m)", 1.0, 30.0, 9.0, step=0.5)
            excavation_depth = st.number_input("Excavation Depth (Left) (m)", 0.0, wall_height, 4.5, step=0.5)

            st.markdown("---")
            st.subheader("2. Soil Properties")

            # --- Helper for Layer Inputs ---
            def render_layers_input(prefix, label, default_layers):
                st.markdown(f"**{label}**")
                num = st.number_input(f"No. of Layers ({prefix})", 1, 5, len(default_layers), key=f"{prefix}_num")
                layers = []
                current_z = 0.0
                for i in range(int(num)):
                    with st.expander(f"Layer {i+1} ({prefix})", expanded=False):
                        h = st.number_input(f"H (m)", 0.1, 20.0, default_layers[i]['H'] if i < len(default_layers) else 3.0, key=f"{prefix}_h_{i}")
                        gamma = st.number_input(f"γ (kN/m³)", 10.0, 25.0, default_layers[i]['g'] if i < len(default_layers) else 18.0, key=f"{prefix}_g_{i}")
                        phi = st.number_input(f"ϕ' (deg)", 0.0, 45.0, default_layers[i]['p'] if i < len(default_layers) else 30.0, key=f"{prefix}_p_{i}")
                        c = st.number_input(f"c' (kPa)", 0.0, 50.0, default_layers[i]['c'] if i < len(default_layers) else 0.0, key=f"{prefix}_c_{i}")
                        
                        layers.append({"id": i+1, "H": h, "gamma": gamma, "phi": phi, "c": c, "top": current_z, "bottom": current_z + h})
                        current_z += h
                return layers

            # Left Side Inputs
            st.caption("⬅️ Left Side (Passive / Excavation)")
            left_wt = st.number_input("Left WT Depth (m)", 0.0, 20.0, 1.5, help="Depth from the excavated surface")
            def_left = [{'H': 1.5, 'g': 18.0, 'p': 38.0, 'c': 0.0}, {'H': 3.0, 'g': 20.0, 'p': 28.0, 'c': 10.0}]
            left_layers = render_layers_input("L", "Passive Layers", def_left)

            st.markdown("---")
            
            # Right Side Inputs
            st.caption("➡️ Right Side (Active / Backfill)")
            right_q = st.number_input("Surcharge q (kPa)", 0.0, 100.0, 50.0)
            right_wt = st.number_input("Right WT Depth (m)", 0.0, 20.0, 6.0, help="Depth from the top of the wall")
            def_right = [{'H': 6.0, 'g': 18.0, 'p': 38.0, 'c': 0.0}, {'H': 3.0, 'g': 20.0, 'p': 28.0, 'c': 10.0}]
            right_layers = render_layers_input("R", "Active Layers", def_right)

            st.markdown("---")
            
            # --- CALCULATION TRIGGER ---
            calc_trigger = st.button("Calculate Pressure Profile", type="primary", use_container_width=True)

        # -------------------------------------------------
        # CALCULATION LOGIC
        # -------------------------------------------------
        def calculate_stress(z_local, layers, wt_depth, surcharge, mode="Active"):
            # Identify layer
            active_layer = layers[-1]
            for l in layers:
                if z_local < l['bottom']: 
                    active_layer = l
                    break
                if z_local == l['bottom']: 
                    active_layer = l
                    break
            
            # Vertical Stress
            sig_v = surcharge
            for l in layers:
                if z_local > l['bottom']:
                    sig_v += l['H'] * l['gamma']
                else:
                    sig_v += (z_local - l['top']) * l['gamma']
                    break
            
            # Pore Pressure
            u = 0.0
            if z_local > wt_depth:
                u = (z_local - wt_depth) * GAMMA_W
            
            sig_v_eff = sig_v - u
            
            # Coefficients
            phi_r = np.radians(active_layer['phi'])
            c_val = active_layer['c']
            
            if mode == "Active":
                K = (1 - np.sin(phi_r)) / (1 + np.sin(phi_r))
                sig_lat_eff = (sig_v_eff * K) - (2 * c_val * np.sqrt(K))
            else: # Passive
                K = (1 + np.sin(phi_r)) / (1 - np.sin(phi_r))
                sig_lat_eff = (sig_v_eff * K) + (2 * c_val * np.sqrt(K))
                
            if sig_lat_eff < 0: sig_lat_eff = 0
            
            sig_lat_tot = sig_lat_eff + u
            
            return sig_lat_tot, u, K, active_layer['id']

        # -------------------------------------------------
        # 2. VISUALIZATION PANEL (RIGHT COLUMN)
        # -------------------------------------------------
        with col_viz:
            if calc_trigger:
                st.subheader("Pressure Diagrams")
                
                # --- PLOT GENERATION ---
                fig, ax = plt.subplots(figsize=(8, 10)) # Taller figure
                
                wall_width = 1.0
                rect_wall = patches.Rectangle((-wall_width/2, 0), wall_width, wall_height, facecolor='lightgrey', edgecolor='black', hatch='//')
                ax.add_patch(rect_wall)
                
                Y_top = wall_height
                Y_exc = wall_height - excavation_depth 
                
                # Draw Soil Layers (Right)
                current_y = Y_top
                for l in right_layers:
                    h = l['H']
                    rect = patches.Rectangle((wall_width/2, current_y - h), 6, h, facecolor='#E6D690' if l['id']%2!=0 else '#C1B088', edgecolor='gray', alpha=0.5)
                    ax.add_patch(rect)
                    ax.text(wall_width/2 + 3, current_y - h/2, f"Backfill Layer {l['id']}\n$\\gamma={l['gamma']}$", ha='center', va='center', fontsize=9)
                    current_y -= h

                # Draw Soil Layers (Left)
                current_y = Y_exc
                for l in left_layers:
                    h = l['H']
                    rect = patches.Rectangle((-wall_width/2 - 6, current_y - h), 6, h, facecolor='#A4C2A5' if l['id']%2!=0 else '#86A388', edgecolor='gray', alpha=0.5)
                    ax.add_patch(rect)
                    ax.text(-wall_width/2 - 3, current_y - h/2, f"Passive Layer {l['id']}\n$\\gamma={l['gamma']}$", ha='center', va='center', fontsize=9)
                    current_y -= h
                    
                # Surcharge
                if right_q > 0:
                    for x in np.linspace(wall_width/2 + 0.5, wall_width/2 + 5.5, 6):
                        ax.arrow(x, Y_top + 1.0, 0, -0.8, head_width=0.2, fc='red', ec='red')
                    ax.text(wall_width/2 + 3, Y_top + 1.2, f"q = {right_q} kPa", color='red', ha='center', fontweight='bold')

                # Water Tables
                wt_elev_r = Y_top - right_wt
                ax.plot([wall_width/2, wall_width/2 + 6], [wt_elev_r, wt_elev_r], 'b--', linewidth=2)
                ax.text(wall_width/2 + 5.5, wt_elev_r, "▽ WT", color='blue', ha='center', va='bottom', fontsize=10, fontweight='bold')
                
                wt_elev_l = Y_exc - left_wt
                ax.plot([-wall_width/2 - 6, -wall_width/2], [wt_elev_l, wt_elev_l], 'b--', linewidth=2)
                ax.text(-wall_width/2 - 5.5, wt_elev_l, "▽ WT", color='blue', ha='center', va='bottom', fontsize=10, fontweight='bold')

                # Ground Lines
                ax.plot([wall_width/2, wall_width/2 + 6], [Y_top, Y_top], 'k-', linewidth=2) 
                ax.plot([-wall_width/2 - 6, -wall_width/2], [Y_exc, Y_exc], 'k-', linewidth=2) 

                # --- PRESSURE PROFILES ---
                # Right Side
                y_steps = np.linspace(0, wall_height, 100)
                p_right = []
                for y_depth in y_steps:
                    sig, _, _, _ = calculate_stress(y_depth, right_layers, right_wt, right_q, "Active")
                    p_right.append(sig)
                
                scale = 0.05 
                ax.plot([wall_width/2 + p * scale for p in p_right], [Y_top - y for y in y_steps], 'r-', linewidth=2, label="Active Pressure")
                ax.fill_betweenx([Y_top - y for y in y_steps], wall_width/2, [wall_width/2 + p * scale for p in p_right], color='red', alpha=0.3)

                # Left Side
                y_steps_l = np.linspace(0, wall_height - excavation_depth, 100)
                p_left = []
                for y_depth in y_steps_l:
                    sig, _, _, _ = calculate_stress(y_depth, left_layers, left_wt, 0, "Passive")
                    p_left.append(sig)
                    
                ax.plot([-wall_width/2 - p * scale for p in p_left], [Y_exc - y for y in y_steps_l], 'g-', linewidth=2, label="Passive Pressure")
                ax.fill_betweenx([Y_exc - y for y in y_steps_l], -wall_width/2, [-wall_width/2 - p * scale for p in p_left], color='green', alpha=0.3)

                # Final Plot Settings
                ax.set_xlim(-8, 8)
                ax.set_ylim(-2, wall_height + 3)
                ax.set_aspect('equal')
                ax.axis('off')
                ax.legend(loc='lower center', ncol=2)
                st.pyplot(fig)

            else:
                # Placeholder when not calculated
                st.info("Waiting for calculation...")
                st.write("Adjust inputs on the left and press **Calculate**.")

        # -------------------------------------------------
        # 3. RESULTS TABLE (Full Width Below)
        # -------------------------------------------------
        if calc_trigger:
            st.markdown("---")
            st.subheader("Calculated Stress Table (1m Intervals)")
            
            table_data = []
            for z in range(0, int(wall_height) + 1):
                row = {"Global Depth (m)": float(z)}
                
                # Active
                r_sig, r_u, r_K, r_L = calculate_stress(float(z), right_layers, right_wt, right_q, "Active")
                row["[R] Layer"] = r_L
                row["[R] Total Lat. Stress (kPa)"] = r_sig
                row["[R] Ka"] = r_K
                
                # Passive
                local_z_left = z - excavation_depth
                if local_z_left >= 0:
                    l_sig, l_u, l_K, l_L = calculate_stress(local_z_left, left_layers, left_wt, 0, "Passive")
                    row["[L] Layer"] = l_L
                    row["[L] Total Lat. Stress (kPa)"] = l_sig
                    row["[L] Kp"] = l_K
                else:
                    row["[L] Layer"] = "-"
                    row["[L] Total Lat. Stress (kPa)"] = 0.0
                    row["[L] Kp"] = 0.0
                
                table_data.append(row)
                
            df = pd.DataFrame(table_data)
            
            # Safe Formatting
            st.dataframe(df.style.format({
                "Global Depth (m)": "{:.1f}",
                "[R] Total Lat. Stress (kPa)": "{:.2f}",
                "[R] Ka": "{:.3f}",
                "[L] Total Lat. Stress (kPa)": "{:.2f}",
                "[L] Kp": "{:.3f}"
            }))

    # =========================================================================
    # TAB 2: COULOMB'S WEDGE THEORY
    # =========================================================================
    with tab_coulomb:
        st.header("Coulomb's Wedge Theory")
        st.info("Simplified calculation for a single soil layer with wall friction.")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Soil & Wall")
            phi_c = st.number_input("Friction Angle ($\phi'$) [deg]", 20.0, 45.0, 30.0)
            delta = st.number_input("Wall Friction ($\delta$) [deg]", 0.0, 30.0, 15.0)
            gamma_c = st.number_input("Unit Weight ($\gamma$) [kN/m³]", 10.0, 25.0, 18.0)
        
        with c2:
            st.subheader("Geometry")
            H_c = st.number_input("Wall Height ($H$) [m]", 1.0, 20.0, 5.0)
            alpha = st.number_input("Wall Batter ($\alpha$) [deg]", 0.0, 30.0, 0.0)
            beta_c = st.number_input("Backfill Slope ($\beta$) [deg]", 0.0, 30.0, 0.0)
        
        if st.button("Calculate Coulomb Force"):
            phi_r = np.radians(phi_c)
            del_r = np.radians(delta)
            alp_r = np.radians(alpha)
            bet_r = np.radians(beta_c)

            term1 = np.sqrt(np.sin(phi_r + del_r) * np.sin(phi_r - bet_r))
            term2 = np.sqrt(np.cos(alp_r + del_r) * np.cos(alp_r - bet_r))
            denom = (np.cos(alp_r)**2) * np.cos(alp_r + del_r) * (1 + (term1/term2))**2
            Ka_c = (np.cos(phi_r - alp_r)**2) / denom
            
            Pa = 0.5 * gamma_c * (H_c**2) * Ka_c
            
            st.success("Calculation Complete")
            c_res1, c_res2 = st.columns(2)
            c_res1.metric("Coulomb Coefficient ($K_a$)", f"{Ka_c:.3f}")
            c_res2.metric("Total Active Force ($P_a$)", f"{Pa:.2f} kN/m")

if __name__ == "__main__":
    app()
