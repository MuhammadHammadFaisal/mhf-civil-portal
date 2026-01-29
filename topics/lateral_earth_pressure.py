import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# =========================================================
# HELPER FUNCTIONS
# =========================================================
GAMMA_W = 9.81

def render_layers_input(prefix, label, default_layers):
    """Renders the input fields for soil layers."""
    st.markdown(f"**{label}**")
    num = st.number_input(f"No. of Layers ({prefix})", 1, 5, len(default_layers), key=f"{prefix}_num")
    layers = []
    current_z = 0.0
    
    for i in range(int(num)):
        with st.expander(f"Layer {i+1} ({prefix})", expanded=False):
            def_h = default_layers[i]['H'] if i < len(default_layers) else 3.0
            type_key = f"{prefix}_type_{i}"
            soil_type = st.selectbox("Soil Type", ["Sand", "Clay", "Custom"], key=type_key)
            
            if soil_type == "Sand":
                d_g, d_p, d_c = 18.0, 35.0, 0.0
            elif soil_type == "Clay":
                d_g, d_p, d_c = 20.0, 25.0, 20.0
            else:
                d_g = default_layers[i]['g'] if i < len(default_layers) else 19.0
                d_p = default_layers[i]['p'] if i < len(default_layers) else 30.0
                d_c = default_layers[i]['c'] if i < len(default_layers) else 5.0

            h = st.number_input(f"H (m)", 0.1, 20.0, def_h, key=f"{prefix}_h_{i}")
            c1, c2 = st.columns(2)
            gamma = c1.number_input(f"γ (kN/m³)", 10.0, 25.0, d_g, key=f"{prefix}_g_{i}_{soil_type}")
            phi = c2.number_input(f"ϕ' (deg)", 0.0, 45.0, d_p, key=f"{prefix}_p_{i}_{soil_type}")
            c = st.number_input(f"c' (kPa)", 0.0, 100.0, d_c, key=f"{prefix}_c_{i}_{soil_type}")
            
            layers.append({"id": i+1, "H": h, "gamma": gamma, "phi": phi, "c": c, "top": current_z, "bottom": current_z + h, "type": soil_type})
            current_z += h
    return layers

def calculate_stress(z_local, layers, wt_depth, surcharge, mode="Active"):
    """Calculates lateral stress at a specific depth (Rankine)."""
    active_layer = layers[-1]
    for l in layers:
        if z_local < l['bottom']: active_layer = l; break
        if z_local == l['bottom']: active_layer = l; break
    
    sig_v = surcharge
    for l in layers:
        if z_local > l['bottom']: sig_v += l['H'] * l['gamma']
        else: sig_v += (z_local - l['top']) * l['gamma']; break
    
    u = (z_local - wt_depth) * GAMMA_W if z_local > wt_depth else 0.0
    sig_v_eff = sig_v - u
    
    phi_r = np.radians(active_layer['phi'])
    c_val = active_layer['c']
    
    if mode == "Active":
        K = (1 - np.sin(phi_r)) / (1 + np.sin(phi_r))
        sig_lat_eff = (sig_v_eff * K) - (2 * c_val * np.sqrt(K))
    else: 
        K = (1 + np.sin(phi_r)) / (1 - np.sin(phi_r))
        sig_lat_eff = (sig_v_eff * K) + (2 * c_val * np.sqrt(K))
        
    if sig_lat_eff < 0: sig_lat_eff = 0
    sig_lat_tot = sig_lat_eff + u
    return sig_lat_tot, u, K, active_layer['id']

# =========================================================
# MAIN APP
# =========================================================
def app():
    st.title("Lateral Earth Pressure Calculator 🧱")
    st.markdown("---")
    
    tab_rankine, tab_coulomb = st.tabs(["1. Rankine's Theory (Wall Profile)", "2. Coulomb's Wedge Theory"])

    # ---------------------------------------------------------
    # TAB 1: RANKINE (Standard)
    # ---------------------------------------------------------
    with tab_rankine:
        st.header("Rankine Analysis")
        st.info("Configure the wall and soil layers on the left.")
        col_input, col_viz = st.columns([0.4, 0.6], gap="medium")

        with col_input:
            st.subheader("1. Wall Geometry")
            wall_height = st.number_input("Total Wall Height (m)", 1.0, 30.0, 9.0, step=0.5)
            excavation_depth = st.number_input("Excavation Depth (Left) (m)", 0.0, wall_height, 4.5, step=0.5)
            st.markdown("---")
            st.subheader("2. Soil Properties")
            st.caption("⬅️ Left Side (Passive)")
            left_wt = st.number_input("Left WT Depth (m)", 0.0, 20.0, 1.5)
            def_left = [{'H': 1.5, 'g': 18.0, 'p': 38.0, 'c': 0.0}, {'H': 3.0, 'g': 20.0, 'p': 28.0, 'c': 10.0}]
            left_layers = render_layers_input("L", "Passive Layers", def_left)
            st.markdown("---")
            st.caption("➡️ Right Side (Active)")
            right_q = st.number_input("Surcharge q (kPa)", 0.0, 100.0, 50.0)
            right_wt = st.number_input("Right WT Depth (m)", 0.0, 20.0, 6.0)
            def_right = [{'H': 6.0, 'g': 18.0, 'p': 38.0, 'c': 0.0}, {'H': 3.0, 'g': 20.0, 'p': 28.0, 'c': 10.0}]
            right_layers = render_layers_input("R", "Active Layers", def_right)
            st.markdown("---")
            calc_trigger = st.button("Calculate Pressure Profile", type="primary", use_container_width=True)

        with col_viz:
            st.subheader("Soil Profile Preview")
            fig_profile, ax_p = plt.subplots(figsize=(8, 6))
            wall_width = 1.0
            rect_wall = patches.Rectangle((-wall_width/2, 0), wall_width, wall_height, facecolor='lightgrey', edgecolor='black', hatch='//')
            ax_p.add_patch(rect_wall)
            Y_top, Y_exc = wall_height, wall_height - excavation_depth 
            
            # Draw Right
            current_y = Y_top
            for l in right_layers:
                h = l['H']
                color = '#E6D690' if l['type'] == "Sand" else ('#B0A494' if l['type'] == "Clay" else '#C1B088')
                rect = patches.Rectangle((wall_width/2, current_y - h), 6, h, facecolor=color, edgecolor='gray', alpha=0.6)
                ax_p.add_patch(rect)
                ax_p.text(wall_width/2 + 3, current_y - h/2, f"{l['type']}\n$\\gamma={l['gamma']}$", ha='center', va='center', fontsize=9)
                current_y -= h
            # Draw Left
            current_y = Y_exc
            for l in left_layers:
                h = l['H']
                color = '#E6D690' if l['type'] == "Sand" else ('#B0A494' if l['type'] == "Clay" else '#C1B088')
                rect = patches.Rectangle((-wall_width/2 - 6, current_y - h), 6, h, facecolor=color, edgecolor='gray', alpha=0.6)
                ax_p.add_patch(rect)
                ax_p.text(-wall_width/2 - 3, current_y - h/2, f"{l['type']}\n$\\gamma={l['gamma']}$", ha='center', va='center', fontsize=9)
                current_y -= h
            
            # Annotations
            if right_q > 0:
                for x in np.linspace(wall_width/2 + 0.5, wall_width/2 + 5.5, 6):
                    ax_p.arrow(x, Y_top + 1.0, 0, -0.8, head_width=0.2, fc='red', ec='red')
                ax_p.text(wall_width/2 + 3, Y_top + 1.2, f"q = {right_q}", color='red', ha='center', fontweight='bold')
            ax_p.plot([wall_width/2, wall_width/2 + 6], [Y_top, Y_top], 'k-', linewidth=2) 
            ax_p.plot([-wall_width/2 - 6, -wall_width/2], [Y_exc, Y_exc], 'k-', linewidth=2) 
            ax_p.set_xlim(-8, 8); ax_p.set_ylim(-2, wall_height + 3); ax_p.set_aspect('equal'); ax_p.axis('off')
            st.pyplot(fig_profile)

            if calc_trigger:
                st.markdown("---")
                st.subheader("Pressure Graph")
                fig_stress, ax_s = plt.subplots(figsize=(8, 6))
                y_steps = np.linspace(0, wall_height, 100)
                p_right = [calculate_stress(y, right_layers, right_wt, right_q, "Active")[0] for y in y_steps]
                y_steps_l = np.linspace(0, wall_height - excavation_depth, 100)
                p_left = [calculate_stress(y, left_layers, left_wt, 0, "Passive")[0] for y in y_steps_l]
                ax_s.plot(p_right, y_steps, 'r-', label="Active (Right)"); ax_s.fill_betweenx(y_steps, 0, p_right, color='red', alpha=0.1)
                global_depth_l = y_steps_l + excavation_depth
                ax_s.plot(p_left, global_depth_l, 'g-', label="Passive (Left)"); ax_s.fill_betweenx(global_depth_l, 0, p_left, color='green', alpha=0.1)
                ax_s.invert_yaxis(); ax_s.set_ylabel("Depth (m)"); ax_s.set_xlabel("Pressure (kPa)"); ax_s.grid(True, linestyle='--'); ax_s.legend()
                st.pyplot(fig_stress)

        if calc_trigger:
            st.markdown("---")
            st.subheader("Stress Table")
            table_data = []
            for z in range(0, int(wall_height) + 1):
                row = {"Depth (m)": float(z)}
                r_sig, r_u, r_K, r_L = calculate_stress(float(z), right_layers, right_wt, right_q, "Active")
                row["[R] Layer"], row["[R] Stress"], row["[R] Ka"] = r_L, r_sig, r_K
                local_z_left = z - excavation_depth
                if local_z_left >= 0:
                    l_sig, l_u, l_K, l_L = calculate_stress(local_z_left, left_layers, left_wt, 0, "Passive")
                    row["[L] Layer"], row["[L] Stress"], row["[L] Kp"] = l_L, l_sig, l_K
                else:
                    row["[L] Layer"], row["[L] Stress"], row["[L] Kp"] = "-", 0.0, 0.0
                table_data.append(row)
            df = pd.DataFrame(table_data)
            st.dataframe(df.style.format({"Depth (m)": "{:.1f}", "[R] Stress": "{:.2f}", "[R] Ka": "{:.3f}", "[L] Stress": "{:.2f}", "[L] Kp": "{:.3f}"}))

    # ---------------------------------------------------------
    # TAB 2: COULOMB (MATCHING HANDWRITTEN DIAGRAM)
    # ---------------------------------------------------------
    with tab_coulomb:
        st.header("Coulomb's Wedge Theory")
        
        col_c_in, col_c_viz = st.columns([0.4, 0.6], gap="medium")

        with col_c_in:
            st.subheader("1. Wall & Geometry")
            H_c = st.number_input("Wall Height (H) [m]", 1.0, 20.0, 6.0)
            alpha = st.number_input("Wall Batter (α) [deg]", 0.0, 30.0, 10.0, help="Angle from vertical")
            beta_c = st.number_input("Backfill Slope (β) [deg]", 0.0, 30.0, 15.0)
            st.markdown("---")
            st.subheader("2. Soil & Interface")
            c_soil_type = st.selectbox("Soil Type", ["Sand", "Custom"], key="c_soil_type")
            if c_soil_type == "Sand": d_phi, d_delta, d_gam = 32.0, 20.0, 18.0
            else: d_phi, d_delta, d_gam = 30.0, 15.0, 19.0
            phi_c = st.number_input("Friction Angle (ϕ') [deg]", 20.0, 45.0, d_phi)
            delta = st.number_input("Wall Friction (δ) [deg]", 0.0, 30.0, d_delta)
            gamma_c = st.number_input("Unit Weight (γ) [kN/m³]", 10.0, 25.0, d_gam)
            st.markdown("---")
            c_calc_btn = st.button("Calculate Wedge Forces", type="primary", use_container_width=True)

        with col_c_viz:
            st.subheader("Failure Wedge Diagram (FBD)")
            
            # Constants & Geometry
            phi_r, del_r = np.radians(phi_c), np.radians(delta)
            alp_r, bet_r = np.radians(alpha), np.radians(beta_c)
            top_x = H_c * np.tan(alp_r)
            rho_approx = 45 + (phi_c/2) # Approx failure plane for viz
            rho_rad = np.radians(rho_approx)
            
            # Intersection C
            if rho_rad > bet_r:
                wedge_x = (H_c - top_x * np.tan(bet_r)) / (np.tan(rho_rad) - np.tan(bet_r))
                wedge_y = wedge_x * np.tan(rho_rad)
            else:
                wedge_x, wedge_y = top_x + 5, top_x + 5 # Fallback

            # --- PLOT ---
            fig_w, ax_w = plt.subplots(figsize=(8, 8))
            
            # A. GEOMETRY
            # Wall
            wall_poly = [[0, 0], [top_x, H_c], [top_x - 1.5, H_c], [-1.5, 0]]
            ax_w.add_patch(patches.Polygon(wall_poly, facecolor='lightgrey', edgecolor='black', hatch='//'))
            # Wedge
            soil_poly = [[0, 0], [top_x, H_c], [wedge_x, wedge_y]]
            ax_w.add_patch(patches.Polygon(soil_poly, facecolor='#FFE0B2', alpha=0.5, edgecolor='none'))
            # Ground & Failure Lines
            ax_w.plot([top_x, wedge_x + 2], [H_c, H_c + (wedge_x + 2 - top_x)*np.tan(bet_r)], 'k-', linewidth=2)
            ax_w.plot([0, wedge_x], [0, wedge_y], 'r--', linewidth=2)
            
            # B. ANNOTATIONS (Normals & Angles) - To match handwritten sketch
            # 1. Wall Normal (at mid height)
            mid_wall_x, mid_wall_y = top_x/2, H_c/2
            # Wall slope is (H_c / top_x). Normal slope is -top_x/H_c
            dx_wn, dy_wn = 1.5, 1.5 * (top_x/H_c) # Perpendicular direction away from soil
            ax_w.plot([mid_wall_x, mid_wall_x - dx_wn], [mid_wall_y, mid_wall_y + dy_wn], 'k--', linewidth=1, alpha=0.7) # Normal line
            
            # 2. Failure Plane Normal
            mid_fail_x, mid_fail_y = wedge_x/2, wedge_y/2
            # Plane slope is tan(rho). Normal slope is -1/tan(rho)
            dx_fn, dy_fn = -1.5 * np.sin(rho_rad), 1.5 * np.cos(rho_rad) # Pointing up-left
            ax_w.plot([mid_fail_x, mid_fail_x + dx_fn], [mid_fail_y, mid_fail_y + dy_fn], 'k--', linewidth=1, alpha=0.7)

            # C. FORCES (If Calculated)
            if c_calc_btn:
                # Calc
                term1 = np.sqrt(np.sin(phi_r + del_r) * np.sin(phi_r - bet_r))
                term2 = np.sqrt(np.cos(alp_r + del_r) * np.cos(alp_r - bet_r))
                denom = (np.cos(alp_r)**2) * np.cos(alp_r + del_r) * (1 + (term1/term2))**2
                Ka_c = (np.cos(phi_r - alp_r)**2) / denom
                Pa = 0.5 * gamma_c * (H_c**2) * Ka_c

                # 1. Weight (W)
                cx, cy = (0+top_x+wedge_x)/3, (0+H_c+wedge_y)/3
                ax_w.arrow(cx, cy, 0, -2.0, head_width=0.2, color='purple', width=0.05, zorder=10)
                ax_w.text(cx + 0.3, cy - 1.0, "W", color='purple', fontweight='bold', fontsize=12)

                # 2. Wall Reaction (P) - Force of Wall ON Soil (FBD of Wedge)
                # Acts at angle delta ABOVE the normal
                # Normal angle (from horizontal) = 180 - (90 - alpha) = 90 + alpha.
                # Force P angle = (90 + alpha) + (90 - delta)? No.
                # Wall face angle = 90 - alpha. Normal is (90-alpha)+90 = 180-alpha.
                # P acts at angle delta from Normal, opposing sliding (sliding is down).
                # So P points UP relative to normal. 
                # Visual check: It should point Up and Right.
                px, py = top_x/3, H_c/3 # Lower third
                ax_w.arrow(px, py, 1.5, 1.0, head_width=0.2, color='red', width=0.05, zorder=10)
                ax_w.text(px + 1.6, py + 1.0, "P", color='red', fontweight='bold', fontsize=12)
                # Delta Arc
                ax_w.text(px + 0.3, py + 0.8, f"δ={delta}°", fontsize=8)

                # 3. Soil Reaction (R) - Force of Soil ON Soil
                # Acts at angle phi from Normal to failure plane.
                # Normal is 90 + rho. R is 90 + rho + phi?
                # Resists sliding down. So R points Up-Left.
                rx, ry = wedge_x/3, wedge_y/3
                ax_w.arrow(rx, ry, -0.8, 1.5, head_width=0.2, color='green', width=0.05, zorder=10)
                ax_w.text(rx - 0.8, ry + 1.5, "R", color='green', fontweight='bold', fontsize=12)
                # Phi Arc
                ax_w.text(rx - 0.3, ry + 0.8, f"ϕ={phi_c}°", fontsize=8)

            ax_w.set_aspect('equal')
            ax_w.set_xlim(-3, wedge_x + 2)
            ax_w.set_ylim(-1, max(H_c, wedge_y) + 2)
            ax_w.axis('off')
            ax_w.set_title("Free Body Diagram of Wedge", fontweight='bold')
            st.pyplot(fig_w)
            
            # --- CALCULATION PANEL ---
            if c_calc_btn:
                with st.expander("📝 Detailed Calculation Steps", expanded=True):
                    st.markdown(r"**1. Coulomb Coefficient ($K_a$):**")
                    st.latex(r"K_a = \frac{\cos^2(\phi - \alpha)}{\cos^2\alpha \cos(\alpha + \delta) \left[ 1 + \sqrt{\frac{\sin(\phi + \delta) \sin(\phi - \beta)}{\cos(\alpha + \delta) \cos(\alpha - \beta)}} \right]^2}")
                    st.write(f"Substituting values: **$K_a = {Ka_c:.4f}$**")
                    st.markdown(r"**2. Total Active Force ($P_a$):**")
                    st.latex(r"P_a = \frac{1}{2} \gamma H^2 K_a")
                    st.success(f"**Result: $P_a = {Pa:.2f}$ kN/m**")

if __name__ == "__main__":
    app()
