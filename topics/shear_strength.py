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
    tab_rankine, tab_coulomb = st.tabs(["1. Rankine's Theory (Multi-Layer)", "2. Coulomb's Wedge Theory"])

    # =========================================================================
    # TAB 1: RANKINE'S THEORY (UPGRADED)
    # =========================================================================
    with tab_rankine:
        st.header("Rankine Analysis (Layered Soil)")
        st.info("Calculates Active/Passive pressures for stratified soil with a Water Table.")

        col_input, col_viz = st.columns([1, 1])

        # -------------------------------------------------
        # 1. INPUTS
        # -------------------------------------------------
        with col_input:
            st.subheader("Global Parameters")
            c1, c2 = st.columns(2)
            wt_depth = c1.number_input("Water Table Depth (m)", 0.0, 20.0, 5.0, step=0.5)
            q_surcharge = c2.number_input("Surcharge q (kPa)", 0.0, 100.0, 10.0, step=5.0)
            
            mode = st.radio("Analysis Mode:", ["Active Case (Ka)", "Passive Case (Kp)"], horizontal=True)

            st.subheader("Soil Stratigraphy")
            num_layers = st.number_input("Number of Layers", 1, 5, 2)
            
            layers = []
            current_depth = 0.0
            
            # Layer Input Loop
            for i in range(int(num_layers)):
                with st.expander(f"Layer {i+1} (Top: {current_depth}m)", expanded=True):
                    cols = st.columns(4)
                    thickness = cols[0].number_input(f"H (m)", 1.0, 20.0, 3.0, key=f"h_{i}")
                    gamma = cols[1].number_input(f"γ (kN/m³)", 10.0, 25.0, 18.0, key=f"g_{i}")
                    phi = cols[2].number_input(f"ϕ' (deg)", 0.0, 45.0, 30.0, key=f"p_{i}")
                    c = cols[3].number_input(f"c' (kPa)", 0.0, 50.0, 0.0, key=f"c_{i}")
                    
                    # Store Layer Data
                    layers.append({
                        "id": i+1,
                        "top": current_depth,
                        "bottom": current_depth + thickness,
                        "gamma": gamma,
                        "phi": phi,
                        "c": c
                    })
                    current_depth += thickness
            
            total_H = current_depth

        # -------------------------------------------------
        # 2. CALCULATION ENGINE
        # -------------------------------------------------
        
        # Function to calculate stress at a specific depth 'z'
        # We pass 'layer_idx' explicitly to handle boundary jumps (top of layer vs bottom of previous)
        def get_stress_at_z(z, layer_idx):
            # 1. Vertical Stress Calculation (Accumulate from top)
            sig_v = q_surcharge
            temp_z = 0
            
            # Sum weight of layers above current depth
            for k in range(len(layers)):
                l = layers[k]
                if z > l['bottom']:
                    # Fully traverse this layer
                    h_eff = l['bottom'] - l['top']
                    # Check if submerged or partially submerged
                    # Simple assumption: If layer is below WT, use buoyant weight? 
                    # Standard practice: Calculate Total Stress first, then subtract u.
                    # We will stick to TOTAL weight for Sigma_v, then subtract u.
                    sig_v += h_eff * l['gamma']
                else:
                    # We are in this layer, go to z
                    h_eff = z - l['top']
                    sig_v += h_eff * l['gamma']
                    break
            
            # 2. Pore Pressure
            if z > wt_depth:
                u = (z - wt_depth) * GAMMA_W
            else:
                u = 0.0
            
            # 3. Effective Vertical Stress
            sig_v_eff = sig_v - u
            
            # 4. Lateral Coefficients for the Specific Layer
            # (Use properties of the requested layer_idx)
            target_layer = layers[layer_idx]
            phi_rad = np.radians(target_layer['phi'])
            c_val = target_layer['c']
            
            if "Active" in mode:
                K = (1 - np.sin(phi_rad)) / (1 + np.sin(phi_rad))
                # Sigma_h' = Sv' * Ka - 2c * sqrt(Ka)
                sig_h_eff = (sig_v_eff * K) - (2 * c_val * np.sqrt(K))
            else:
                K = (1 + np.sin(phi_rad)) / (1 - np.sin(phi_rad))
                # Sigma_h' = Sv' * Kp + 2c * sqrt(Kp)
                sig_h_eff = (sig_v_eff * K) + (2 * c_val * np.sqrt(K))
            
            # Tension crack check (no tension in soil usually)
            if sig_h_eff < 0: sig_h_eff = 0
            
            # 5. Total Lateral Pressure
            sig_h_total = sig_h_eff + u
            
            return {
                "z": z,
                "Layer": target_layer['id'],
                "Sv_eff": sig_v_eff,
                "u": u,
                "K": K,
                "Sh_eff": sig_h_eff,
                "Sh_total": sig_h_total
            }

        # Generate Data for Plotting (High Res + Boundaries)
        plot_data = []
        # Generate Data for Table (1m Intervals)
        table_data = []
        
        # 1. Table Generation (1m interval loop)
        # We loop integers from 0 to total_H
        for z_int in range(int(total_H) + 1):
            # Find which layer this z belongs to
            # If z is exactly on boundary, usually take the layer BELOW for calculation list
            l_idx = 0
            for i, l in enumerate(layers):
                if z_int >= l['top'] and z_int < l['bottom']:
                    l_idx = i
                    break
                if z_int == total_H: # Bottom case
                    l_idx = len(layers) - 1
            
            res = get_stress_at_z(float(z_int), l_idx)
            table_data.append(res)

        # 2. Plot Generation (Handle Jumps)
        # We calculate at Top and Bottom of EVERY layer
        for i, l in enumerate(layers):
            # Top of layer
            res_top = get_stress_at_z(l['top'], i)
            plot_data.append(res_top)
            
            # Bottom of layer
            res_bot = get_stress_at_z(l['bottom'], i)
            plot_data.append(res_bot)
            
            # If WT is inside this layer, add a point there to show slope change
            if l['top'] < wt_depth < l['bottom']:
                res_wt = get_stress_at_z(wt_depth, i)
                plot_data.append(res_wt)

        # Sort plot data by depth
        plot_data.sort(key=lambda x: (x['z'], x['Layer']))
        
        df_table = pd.DataFrame(table_data)
        
        # -------------------------------------------------
        # 3. VISUALIZATION
        # -------------------------------------------------
        with col_viz:
            st.subheader("Pressure Profile")
            fig, ax = plt.subplots(figsize=(6, 8))
            
            # Extract lists for plotting
            z_vals = [p['z'] for p in plot_data]
            sh_vals = [p['Sh_total'] for p in plot_data]
            u_vals = [p['u'] for p in plot_data]
            
            # Plot Total Lateral Pressure
            ax.plot(sh_vals, z_vals, 'r-o', linewidth=2, label="Total Lateral Pressure ($\sigma_h$)")
            # Plot Water Pressure
            ax.plot(u_vals, z_vals, 'b--', label="Pore Water Pressure ($u$)")
            
            # Draw Layer Boundaries
            for l in layers:
                ax.axhline(l['bottom'], color='gray', linestyle=':', linewidth=1)
                ax.text(max(sh_vals)*1.05 if len(sh_vals)>0 else 1, (l['top']+l['bottom'])/2, 
                        f"L{l['id']}", va='center', fontsize=8)

            # Draw Water Table
            ax.axhline(wt_depth, color='blue', linestyle='-.', linewidth=2)
            ax.text(0, wt_depth, "▽ WT", color='blue', va='bottom', fontweight='bold')
            
            ax.set_ylim(total_H, 0) # Invert Y
            ax.set_xlabel("Pressure (kPa)")
            ax.set_ylabel("Depth (m)")
            ax.grid(True, alpha=0.3)
            ax.legend()
            st.pyplot(fig)

        # -------------------------------------------------
        # 4. OUTPUT TABLE (1m Intervals)
        # -------------------------------------------------
        st.subheader("Calculated Stress Table (1m Intervals)")
        
        # Format for clean display
        display_df = df_table[["z", "Layer", "Sv_eff", "u", "K", "Sh_eff", "Sh_total"]].copy()
        display_df.columns = ["Depth (m)", "Layer", "Eff. Vert. Stress (kPa)", "Pore Pressure (kPa)", "Coeff (K)", "Eff. Lat. Stress (kPa)", "Total Lat. Stress (kPa)"]
        
        st.dataframe(display_df.style.format("{:.2f}"))

    # =========================================================================
    # TAB 2: COULOMB'S WEDGE THEORY (Simplified for Single Layer)
    # =========================================================================
    with tab_coulomb:
        st.header("Coulomb's Wedge Theory")
        st.info("Uses a simplified homogeneous soil assumption for complex geometry (Wall Friction, Batter).")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Soil & Wall")
            phi_c = st.number_input("Friction Angle ($\phi'$) [deg]", 20.0, 45.0, 30.0)
            delta = st.number_input("Wall Friction ($\delta$) [deg]", 0.0, 30.0, 15.0)
            gamma_c = st.number_input("Unit Weight ($\gamma$) [kN/m³]", 10.0, 25.0, 18.0)
            c_c = st.number_input("Cohesion ($c'$) [kPa]", 0.0, 50.0, 0.0, help="Coulomb theory usually assumes c=0, but we can add 2c√Ka term if needed.")
        
        with c2:
            st.subheader("Geometry")
            H_c = st.number_input("Wall Height ($H$) [m]", 1.0, 20.0, 5.0)
            alpha = st.number_input("Wall Batter ($\alpha$) [deg]", 0.0, 30.0, 0.0)
            beta_c = st.number_input("Backfill Slope ($\beta$) [deg]", 0.0, 30.0, 0.0)
        
        # Coulomb Ka Calculation
        phi_r = np.radians(phi_c)
        del_r = np.radians(delta)
        alp_r = np.radians(alpha)
        bet_r = np.radians(beta_c)

        # [cite_start]Standard Coulomb Formula [cite: 816]
        term1 = np.sqrt(np.sin(phi_r + del_r) * np.sin(phi_r - bet_r))
        term2 = np.sqrt(np.cos(alp_r + del_r) * np.cos(alp_r - bet_r))
        denom = (np.cos(alp_r)**2) * np.cos(alp_r + del_r) * (1 + (term1/term2))**2
        Ka_c = (np.cos(phi_r - alp_r)**2) / denom
        
        # Resultant Force
        # Pa = 0.5 * gamma * H^2 * Ka
        Pa = 0.5 * gamma_c * (H_c**2) * Ka_c
        
        # If cohesion exists, subtract tension crack term approximation?
        # Standard Coulomb is for c=0. For c>0, Bell's modification is essentially Rankine's term.
        # We will stick to c=0 cohesionless visual or basic result.
        
        st.metric("Coulomb Coefficient ($K_a$)", f"{Ka_c:.3f}")
        st.metric("Total Active Force ($P_a$)", f"{Pa:.2f} kN/m")
        
        st.caption("Note: Diagram not included for Coulomb tab in this upgrade to prioritize Rankine Multi-layer features.")

if __name__ == "__main__":
    app()
