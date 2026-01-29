import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# =========================================================
# APP CONFIG
# =========================================================
# st.set_page_config(page_title="Lateral Earth Pressure", layout="wide") # Uncomment if running standalone
GAMMA_W = 9.81

def app():
    st.title("Lateral Earth Pressure Calculator 🧱")
    st.markdown("---")
    
    # We maintain the tab structure
    tab_rankine, tab_coulomb = st.tabs(["1. Rankine's Theory (Wall Profile)", "2. Coulomb's Wedge Theory"])

    # =========================================================================
    # TAB 1: RANKINE'S THEORY (DUAL SIDE PROFILE)
    # =========================================================================
    with tab_rankine:
        st.header("Rankine Analysis: Retaining Wall Profile")
        st.info("Define soil layers for the **Backfill (Right/Active)** and **Excavation (Left/Passive)** sides separately.")

        # --- GLOBAL WALL GEOMETRY ---
        st.subheader("1. Wall Geometry")
        c_geo1, c_geo2 = st.columns(2)
        wall_height = c_geo1.number_input("Total Wall Height (m)", 1.0, 30.0, 9.0, step=0.5, key="w_h")
        excavation_depth = c_geo2.number_input("Excavation Depth on Left (m)", 0.0, wall_height, 4.5, step=0.5, key="w_exc", help="Distance from Top of Wall to the Left Ground Surface")

        st.markdown("---")

        # --- SOIL INPUTS (Split Columns) ---
        col_left, col_right = st.columns(2)

        # Helper function to render layer inputs
        def render_layers_input(prefix, label, default_layers):
            st.markdown(f"### {label}")
            num = st.number_input(f"Layers ({prefix})", 1, 5, len(default_layers), key=f"{prefix}_num")
            layers = []
            current_z = 0.0
            for i in range(int(num)):
                with st.expander(f"Layer {i+1}", expanded=True):
                    c1, c2 = st.columns(2)
                    h = c1.number_input(f"H (m)", 0.1, 20.0, default_layers[i]['H'] if i < len(default_layers) else 3.0, key=f"{prefix}_h_{i}")
                    gamma = c2.number_input(f"γ (kN/m³)", 10.0, 25.0, default_layers[i]['g'] if i < len(default_layers) else 18.0, key=f"{prefix}_g_{i}")
                    c3, c4 = st.columns(2)
                    phi = c3.number_input(f"ϕ' (deg)", 0.0, 45.0, default_layers[i]['p'] if i < len(default_layers) else 30.0, key=f"{prefix}_p_{i}")
                    c = c4.number_input(f"c' (kPa)", 0.0, 50.0, default_layers[i]['c'] if i < len(default_layers) else 0.0, key=f"{prefix}_c_{i}")
                    
                    layers.append({"id": i+1, "H": h, "gamma": gamma, "phi": phi, "c": c, "top": current_z, "bottom": current_z + h})
                    current_z += h
            return layers

        # 1. LEFT SIDE (PASSIVE)
        with col_left:
            st.info("⬅️ **Left Side (Passive)**")
            # Default: 1.5m Sand, 3m Clay (matches your image example relative to excavation)
            def_left = [{'H': 1.5, 'g': 18.0, 'p': 38.0, 'c': 0.0}, {'H': 3.0, 'g': 20.0, 'p': 28.0, 'c': 10.0}]
            left_wt = st.number_input("Left WT Depth (from Left Surface) (m)", 0.0, 20.0, 1.5, key="l_wt")
            left_layers = render_layers_input("L", "Passive Soil Layers", def_left)

        # 2. RIGHT SIDE (ACTIVE)
        with col_right:
            st.warning("➡️ **Right Side (Active)**")
            # Default: 6m Sand, 3m Clay (matches your image example)
            def_right = [{'H': 6.0, 'g': 18.0, 'p': 38.0, 'c': 0.0}, {'H': 3.0, 'g': 20.0, 'p': 28.0, 'c': 10.0}]
            right_q = st.number_input("Surcharge q (kPa)", 0.0, 100.0, 50.0, key="r_q")
            right_wt = st.number_input("Right WT Depth (from Right Surface) (m)", 0.0, 20.0, 6.0, key="r_wt")
            right_layers = render_layers_input("R", "Active Soil Layers", def_right)

        # -------------------------------------------------
        # CALCULATION ENGINE
        # -------------------------------------------------
        def calculate_stress(z_local, layers, wt_depth, surcharge, mode="Active"):
            # Identify layer
            active_layer = layers[-1]
            for l in layers:
                if z_local < l['bottom']: # Strict less than to catch top boundary correctly in loops
                    active_layer = l
                    break
                if z_local == l['bottom']: # Catch exact boundary
                    active_layer = l
                    break
            
            # Vertical Stress (Total)
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
            
            # Lateral Coefficients
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
        # VISUALIZATION & OUTPUT
        # -------------------------------------------------
        st.markdown("---")
        
        # Prepare Plot Data
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # 1. Draw Wall
        wall_width = 1.0
        # Wall goes from Global 0 to Global Wall Height
        rect_wall = patches.Rectangle((-wall_width/2, 0), wall_width, wall_height, facecolor='lightgrey', edgecolor='black', hatch='//')
        ax.add_patch(rect_wall)
        
        # 2. Draw Right Side (Active)
        # Global Y = 0 is Top of Wall. Y increases downwards? No, let's plot Elevation Y.
        # Let Top of Wall = Elevation H. Bottom = 0.
        
        Y_top = wall_height
        Y_exc = wall_height - excavation_depth # Elevation of left surface
        
        # -- Right Layers --
        r_stress_points = [] # For plotting stress profile
        current_y = Y_top
        for l in right_layers:
            h = l['H']
            # Draw Soil Box
            rect = patches.Rectangle((wall_width/2, current_y - h), 5, h, facecolor='#E6D690' if l['id']%2!=0 else '#C1B088', edgecolor='gray', alpha=0.5)
            ax.add_patch(rect)
            ax.text(wall_width/2 + 2.5, current_y - h/2, f"R-L{l['id']}\n$\gamma={l['gamma']}$", ha='center', fontsize=8)
            current_y -= h

        # -- Left Layers --
        l_stress_points = []
        current_y = Y_exc
        for l in left_layers:
            h = l['H']
            rect = patches.Rectangle((-wall_width/2 - 5, current_y - h), 5, h, facecolor='#A4C2A5' if l['id']%2!=0 else '#86A388', edgecolor='gray', alpha=0.5)
            ax.add_patch(rect)
            ax.text(-wall_width/2 - 2.5, current_y - h/2, f"L-L{l['id']}\n$\gamma={l['gamma']}$", ha='center', fontsize=8)
            current_y -= h
            
        # -- Surcharge (Right) --
        if right_q > 0:
            for x in np.linspace(wall_width/2 + 0.5, wall_width/2 + 4.5, 5):
                ax.arrow(x, Y_top + 1.0, 0, -0.8, head_width=0.2, fc='red', ec='red')
            ax.text(wall_width/2 + 2.5, Y_top + 1.2, f"q = {right_q} kPa", color='red', ha='center', fontweight='bold')

        # -- Water Tables --
        # Right WT
        wt_elev_r = Y_top - right_wt
        ax.plot([wall_width/2, wall_width/2 + 5], [wt_elev_r, wt_elev_r], 'b--', linewidth=2)
        ax.text(wall_width/2 + 4.5, wt_elev_r, "▽", color='blue', ha='center', va='bottom', fontsize=14)
        
        # Left WT
        wt_elev_l = Y_exc - left_wt
        ax.plot([-wall_width/2 - 5, -wall_width/2], [wt_elev_l, wt_elev_l], 'b--', linewidth=2)
        ax.text(-wall_width/2 - 4.5, wt_elev_l, "▽", color='blue', ha='center', va='bottom', fontsize=14)

        # -- Ground Lines --
        ax.plot([wall_width/2, wall_width/2 + 5], [Y_top, Y_top], 'k-', linewidth=2) # Right Surface
        ax.plot([-wall_width/2 - 5, -wall_width/2], [Y_exc, Y_exc], 'k-', linewidth=2) # Left Surface

        # -- Pressure Diagrams --
        # Calculate Right Stress Profile
        # We calculate at Y_top down to 0
        y_steps = np.linspace(0, wall_height, 50)
        p_right = []
        for y_depth in y_steps:
            sig, _, _, _ = calculate_stress(y_depth, right_layers, right_wt, right_q, "Active")
            p_right.append(sig)
        
        # Plot Active (Red) on Right
        # Scale factor for visualization
        scale = 0.05 
        ax.plot([wall_width/2 + p * scale for p in p_right], [Y_top - y for y in y_steps], 'r-', linewidth=2)
        ax.fill_betweenx([Y_top - y for y in y_steps], wall_width/2, [wall_width/2 + p * scale for p in p_right], color='red', alpha=0.3)

        # Calculate Left Stress Profile
        # Valid only below excavation
        y_steps_l = np.linspace(0, wall_height - excavation_depth, 50) # local depth 0 to remaining height
        p_left = []
        for y_depth in y_steps_l:
            sig, _, _, _ = calculate_stress(y_depth, left_layers, left_wt, 0, "Passive")
            p_left.append(sig)
            
        # Plot Passive (Green) on Left
        # Note: Passive pushes TO the right, so we plot it extending leftwards from left face
        ax.plot([-wall_width/2 - p * scale for p in p_left], [Y_exc - y for y in y_steps_l], 'g-', linewidth=2)
        ax.fill_betweenx([Y_exc - y for y in y_steps_l], -wall_width/2, [-wall_width/2 - p * scale for p in p_left], color='green', alpha=0.3)

        # Labels
        ax.set_xlim(-7, 7)
        ax.set_ylim(-1, wall_height + 2)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(f"Wall Profile & Pressure Diagrams\n(Red=Active, Green=Passive)", fontweight='bold')
        
        st.pyplot(fig)

        # -------------------------------------------------
        # TABLE GENERATION
        # -------------------------------------------------
        st.subheader("Calculated Stress Table (1m Intervals)")
        
        # Generate rows based on Global Depth (from Top of Wall = 0)
        table_data = []
        for z in range(0, int(wall_height) + 1):
            row = {"Global Depth (m)": z}
            
            # Right Side (Active) Calculation
            r_sig, r_u, r_K, r_L = calculate_stress(float(z), right_layers, right_wt, right_q, "Active")
            row["[R] Layer"] = r_L
            row["[R] Total Lat. Stress (kPa)"] = r_sig
            row["[R] Ka"] = r_K
            
            # Left Side (Passive) Calculation
            # Z is global. Local z for left = Z - excavation_depth
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
        
        # Define specific formatting to handle the "-" string in [L] Layer safely
        format_dict = {
            "Global Depth (m)": "{:.1f}",
            "[R] Total Lat. Stress (kPa)": "{:.2f}",
            "[R] Ka": "{:.3f}",
            "[L] Total Lat. Stress (kPa)": "{:.2f}",
            "[L] Kp": "{:.3f}"
        }
        
        st.dataframe(df.style.format(format_dict))

    # =========================================================================
    # TAB 2: COULOMB'S WEDGE THEORY (Simplified)
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
        
        phi_r = np.radians(phi_c)
        del_r = np.radians(delta)
        alp_r = np.radians(alpha)
        bet_r = np.radians(beta_c)

        term1 = np.sqrt(np.sin(phi_r + del_r) * np.sin(phi_r - bet_r))
        term2 = np.sqrt(np.cos(alp_r + del_r) * np.cos(alp_r - bet_r))
        denom = (np.cos(alp_r)**2) * np.cos(alp_r + del_r) * (1 + (term1/term2))**2
        Ka_c = (np.cos(phi_r - alp_r)**2) / denom
        
        Pa = 0.5 * gamma_c * (H_c**2) * Ka_c
        
        st.metric("Coulomb Coefficient ($K_a$)", f"{Ka_c:.3f}")
        st.metric("Total Active Force ($P_a$)", f"{Pa:.2f} kN/m")

if __name__ == "__main__":
    app()
