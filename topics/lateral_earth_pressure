import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def app():
    st.title("Lateral Earth Pressure Calculator 🧱")
    st.markdown("Based on **Chapter 7** of Soil Mechanics Notes.")
    
    # Tabs for the two theories
    tab_rankine, tab_coulomb = st.tabs(["1. Rankine's Theory", "2. Coulomb's Wedge Theory"])

    # =========================================================================
    # TAB 1: RANKINE'S THEORY
    # =========================================================================
    with tab_rankine:
        st.header("Rankine's Lateral Earth Pressure")
        st.info("Assumes: Smooth vertical wall, plane strain, plastic equilibrium[cite: 517, 773].")

        # --- 1. Inputs ---
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Soil Properties")
            phi = st.number_input("Friction Angle ($\phi'$) [deg]", 20.0, 45.0, 30.0, key="r_phi")
            gamma = st.number_input("Unit Weight ($\gamma$) [kN/m³]", 10.0, 25.0, 18.0, key="r_gamma")
            c = st.number_input("Cohesion ($c'$) [kPa]", 0.0, 50.0, 0.0, key="r_c")
            beta = st.number_input("Backfill Slope Angle ($\\beta$) [deg]", 0.0, 30.0, 0.0, key="r_beta")
        
        with col2:
            st.subheader("Wall & Loads")
            H = st.number_input("Wall Height ($H$) [m]", 1.0, 20.0, 5.0, key="r_H")
            q = st.number_input("Surcharge ($q$) [kPa]", 0.0, 100.0, 0.0, key="r_q")
            wt_depth = st.number_input("Water Table Depth [m] (from top)", 0.0, H, H, key="r_wt")

        mode = st.radio("State:", ["Active Case", "Passive Case"], horizontal=True, key="r_mode")

        # --- 2. Calculations ---
        phi_rad = np.radians(phi)
        beta_rad = np.radians(beta)
        
        # Coefficient Calculation (Rankine General Case for Sloping Ground) [cite: 682]
        # Note: If beta=0, this simplifies to standard formula.
        if mode == "Active Case":
            # Ka formula [cite: 682]
            num = np.cos(beta_rad) - np.sqrt(np.cos(beta_rad)**2 - np.cos(phi_rad)**2)
            den = np.cos(beta_rad) + np.sqrt(np.cos(beta_rad)**2 - np.cos(phi_rad)**2)
            K = np.cos(beta_rad) * (num / den)
            k_label = "K_a"
            failure_angle = 45 + (phi/2) # Theoretical angle from horizontal 
        else:
            # Passive Case (inverse of Active roughly, strictly Kp)
            num = np.cos(beta_rad) + np.sqrt(np.cos(beta_rad)**2 - np.cos(phi_rad)**2)
            den = np.cos(beta_rad) - np.sqrt(np.cos(beta_rad)**2 - np.cos(phi_rad)**2)
            K = np.cos(beta_rad) * (num / den)
            k_label = "K_p"
            failure_angle = 45 - (phi/2)

        st.markdown("---")
        st.subheader(f"Results ({mode})")
        st.latex(f"{k_label} = {K:.3f}")
        
        # Pressure Calculation at Key Depths (Top, WT, Bottom)
        # Sigma_h = Sigma_v * K - 2c * sqrt(K) (+ Hydrostatic)
        
        z_vals = [0, wt_depth, H]
        pressures = []
        
        for z in z_vals:
            # Vertical Stress
            if z <= wt_depth:
                sig_v = (gamma * z) + q
                u = 0
            else:
                sig_v = (gamma * wt_depth) + ((gamma - 9.81) * (z - wt_depth)) + q
                u = (z - wt_depth) * 9.81
            
            # Lateral Earth Pressure [cite: 565]
            if mode == "Active Case":
                sig_h = (sig_v * K) - (2 * c * np.sqrt(K))
            else:
                sig_h = (sig_v * K) + (2 * c * np.sqrt(K)) # Passive adds cohesion [cite: 570]
            
            # Check for tension crack (negative pressure) in Active case
            if sig_h < 0: sig_h = 0
            
            total_h = sig_h + u
            pressures.append(total_h)

        # Tension Crack Depth (Active Clay) 
        z_crack = 0
        if mode == "Active Case" and c > 0:
            z_crack = (2 * c) / (gamma * np.sqrt(K))
            if z_crack > H: z_crack = H
            st.metric("Tension Crack Depth ($z_c$)", f"{z_crack:.2f} m")

        # --- 3. Visualization (Diagram) ---
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
        
        # Plot 1: Soil Profile & Failure Plane
        ax1.set_title("Physical Diagram")
        
        # Wall
        wall = patches.Rectangle((0, 0), 0.2, H, facecolor='grey', edgecolor='black', hatch='///')
        ax1.add_patch(wall)
        
        # Ground Surface
        x_surf = np.linspace(0.2, 5 + H, 100)
        y_surf = H + (x_surf - 0.2) * np.tan(beta_rad)
        ax1.plot(x_surf, y_surf, 'k-', linewidth=2)
        
        # Failure Plane
        # Starting from heel of wall (0.2, 0)
        # Angle depends on Active/Passive. 
        # Active failure plane is steeper (45 + phi/2). Passive is shallower (45 - phi/2).
        f_angle_rad = np.radians(failure_angle)
        x_fail = np.linspace(0.2, H/np.tan(f_angle_rad) + 2, 100)
        y_fail = (x_fail - 0.2) * np.tan(f_angle_rad)
        
        # Clip failure plane to ground surface
        # Find intersection
        # y_fail = (x-0.2)tan(theta)
        # y_surf = H + (x-0.2)tan(beta)
        # Intersection logic simplified for viz
        ax1.plot(x_fail, y_fail, 'r--', label=f"Failure Plane ($\\theta={failure_angle:.1f}^\circ$)")
        
        # Water Table
        if wt_depth < H:
            ax1.axhline(H - wt_depth, color='blue', linestyle='-.', label="Water Table")
            ax1.text(1.0, H - wt_depth + 0.1, "▽", color='blue', fontsize=12, ha='center')

        ax1.set_xlim(-1, H + 2)
        ax1.set_ylim(-1, H + 2)
        ax1.legend(loc='upper right')
        ax1.set_aspect('equal')
        ax1.axis('off')
        
        # Plot 2: Pressure Distribution
        ax2.set_title("Lateral Pressure Distribution ($\sigma_h$)")
        # Invert Y for depth (0 at top)
        y_plot = [H, H - wt_depth, 0] # Corresponding to z=0, z=wt, z=H
        ax2.plot(pressures, y_plot, 'k-o')
        ax2.fill_betweenx(y_plot, 0, pressures, alpha=0.3, color='orange')
        
        # Tension Crack Visual
        if z_crack > 0:
            ax2.axhline(H - z_crack, color='red', linestyle=':', label="Tension Crack")
            
        ax2.set_xlabel("Pressure (kPa)")
        ax2.set_ylabel("Height from base (m)")
        ax2.set_ylim(0, H + 1)
        ax2.grid(True, linestyle='--', alpha=0.5)

        st.pyplot(fig)


    # =========================================================================
    # TAB 2: COULOMB'S WEDGE THEORY
    # =========================================================================
    with tab_coulomb:
        st.header("Coulomb's Wedge Theory")
        st.info("Considers Wall Friction ($\delta$) and Batter Angle. Analyzes the equilibrium of a soil wedge[cite: 781, 826].")

        # --- 1. Inputs ---
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Soil & Interface")
            phi_c = st.number_input("Friction Angle ($\phi'$) [deg]", 20.0, 45.0, 30.0, key="c_phi")
            delta = st.number_input("Wall Friction ($\delta$) [deg]", 0.0, phi_c, phi_c/2, key="c_delta", help="Typically phi/2 to 2/3 phi [cite: 783]")
            gamma_c = st.number_input("Unit Weight ($\gamma$) [kN/m³]", 10.0, 25.0, 18.0, key="c_gamma")
        
        with c2:
            st.subheader("Geometry")
            H_c = st.number_input("Wall Height ($H$) [m]", 1.0, 20.0, 5.0, key="c_H")
            theta = st.number_input("Wall Batter Angle ($\\alpha$) [deg]", 0.0, 30.0, 10.0, help="Angle of wall back face from vertical")
            beta_c = st.number_input("Backfill Slope ($\\beta$) [deg]", 0.0, 30.0, 0.0, key="c_beta")

        # --- 2. Calculation (Coulomb Ka) ---
        # Converting to Radians
        phi_r = np.radians(phi_c)
        del_r = np.radians(delta)
        alp_r = np.radians(theta) # Note: Some formulas use theta for failure plane, alpha for wall.
        bet_r = np.radians(beta_c)
        
        # Standard Coulomb Ka Formula
        # Source: Analytical solution matching the wedge theory maximum P
        term1 = np.sqrt(np.sin(phi_r + del_r) * np.sin(phi_r - bet_r))
        term2 = np.sqrt(np.cos(alp_r + del_r) * np.cos(alp_r - bet_r))
        denominator = (np.cos(alp_r)**2) * np.cos(alp_r + del_r) * (1 + (term1/term2))**2
        
        Ka_c = (np.cos(phi_r - alp_r)**2) / denominator
        
        Pa_c = 0.5 * gamma_c * (H_c**2) * Ka_c
        
        st.markdown("---")
        st.subheader("Results (Active Wedge)")
        col_res1, col_res2 = st.columns(2)
        col_res1.metric("Coulomb Coefficient ($K_a$)", f"{Ka_c:.3f}")
        col_res2.metric("Total Active Thrust ($P_A$)", f"{Pa_c:.2f} kN/m")

        # --- 3. Visualization (Force Polygon & Wedge) ---
        st.write("### Trial Wedge Visualization")
        
        fig2, ax = plt.subplots(figsize=(8, 6))
        
        # Draw Wall (Battered)
        # Base at (0,0), Top at (H*tan(theta), H)
        wall_top_x = H_c * np.tan(alp_r)
        wall_poly = patches.Polygon([[0,0], [wall_top_x, H_c], [-1, H_c], [-1, 0]], 
                                    facecolor='grey', edgecolor='black', hatch='///')
        ax.add_patch(wall_poly)
        
        # Draw Ground
        ground_x = np.linspace(wall_top_x, wall_top_x + H_c*2, 100)
        ground_y = H_c + (ground_x - wall_top_x) * np.tan(bet_r)
        ax.plot(ground_x, ground_y, 'k-', linewidth=2)
        
        # Draw Critical Failure Plane
        # The angle rho (failure plane from horizontal) for Coulomb active can be approximated or calculated.
        # For visualization, we will draw a representative wedge.
        # Let's assume a failure plane angle approx 45 + phi/2 for the diagram purpose
        rho_approx = 45 + (phi_c / 2) 
        rho_rad = np.radians(rho_approx)
        
        # Wedge coordinates
        # Start at heel (0,0) -> intersect with surface
        # Line: y = x * tan(rho)
        # Surf: y = H + (x - top_x) * tan(beta)
        # Intersection (simplified for viz):
        wedge_x = H_c / np.tan(rho_rad) + 1.5 
        wedge_y = wedge_x * np.tan(rho_rad) # Just illustrative
        
        ax.plot([0, wedge_x], [0, wedge_y], 'r--', linewidth=2, label="Failure Plane")
        
        # Force Vectors (Stylized) based on [cite: 826]
        # Weight W (Gravity)
        cg_x = (wall_top_x + wedge_x) / 3 # Rough Center of Gravity
        cg_y = H_c / 2
        ax.arrow(cg_x, cg_y, 0, -1.5, head_width=0.15, head_length=0.2, fc='blue', ec='blue', label='Weight (W)')
        ax.text(cg_x + 0.1, cg_y - 0.7, "W", color='blue', fontweight='bold')

        # Reaction R (on failure plane) - angled at phi from normal
        ax.arrow(cg_x, cg_y, -1, 1, head_width=0.15, head_length=0.2, fc='green', ec='green')
        ax.text(cg_x - 0.8, cg_y + 0.5, "R", color='green', fontweight='bold')
        
        # Thrust P (on wall) - angled at delta from normal
        # Normal to wall is at angle theta. P is at theta + delta.
        ax.arrow(wall_top_x/2, H_c/3, -0.5, 0, head_width=0.15, head_length=0.2, fc='red', ec='red')
        ax.text(wall_top_x/2 - 0.6, H_c/3 + 0.1, "$P_A$", color='red', fontweight='bold')

        ax.set_aspect('equal')
        ax.set_xlim(-2, H_c + 3)
        ax.set_ylim(-1, H_c + 3)
        ax.axis('off')
        ax.legend(loc='upper right')
        
        st.pyplot(fig2)

if __name__ == "__main__":
    app()
