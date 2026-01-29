import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def calculate_infinite_slope(beta, phi, c, gamma, gamma_sat, z, u, case):
    beta_r = math.radians(beta)
    phi_r = math.radians(phi)
    
    if case == "Dry Cohesionless (Sand)":
        if beta > 0:
            fs = math.tan(phi_r) / math.tan(beta_r)
            formula = r"FS = \frac{\tan \phi'}{\tan \beta}"
        else:
            return 999.0, "Stable (Flat)"
            
    elif case == "Seepage Parallel to Slope":
        gamma_w = 9.81
        gamma_prime = gamma_sat - gamma_w
        if beta > 0:
            fs = (gamma_prime / gamma_sat) * (math.tan(phi_r) / math.tan(beta_r))
            formula = r"FS = \frac{\gamma'}{\gamma_{sat}} \frac{\tan \phi'}{\tan \beta}"
        else:
            return 999.0, "Stable"
            
    else: # Cohesive
        # Normal Stress on failure plane
        # Sigma_n = gamma * z * cos^2(beta)
        sigma_n = gamma * z * (math.cos(beta_r)**2)
        # Shear Stress (Driving)
        tau_mob = gamma * z * math.sin(beta_r) * math.cos(beta_r)
        
        # Resisting Strength = c' + (sigma_n - u) tan(phi)
        resisting = c + (sigma_n - u) * math.tan(phi_r)
        
        if tau_mob > 0.001:
            fs = resisting / tau_mob
            formula = r"FS = \frac{c' + (\gamma z \cos^2\beta - u)\tan\phi'}{\gamma z \sin\beta \cos\beta}"
        else:
            return 999.0, "Stable (Flat)"
            
    return fs, formula

# =========================================================
# MAIN APP
# =========================================================
def app():
    st.title("Slope Stability Calculator ⛰️")
    st.markdown("Based on **Chapter 8** of Soil Mechanics Notes.")
    
    tab_trans, tab_rot, tab_comp = st.tabs([
        "1. Translational (Infinite)", 
        "2. Rotational (Circular)", 
        "3. Compound (Block)"
    ])

    # ---------------------------------------------------------
    # TAB 1: TRANSLATIONAL (INFINITE SLOPE)
    # ---------------------------------------------------------
    with tab_trans:
        st.header("Infinite Slope Analysis")
        st.info("Assumes failure plane is parallel to the ground surface. Best for long natural slopes.")
        
        col_t1, col_t2 = st.columns([0.4, 0.6], gap="medium")
        
        with col_t1:
            st.subheader("Inputs")
            soil_case = st.radio("Soil Condition:", 
                               ["Dry Cohesionless (Sand)", "Seepage Parallel to Slope", "Cohesive Soil (c-ϕ)"])
            
            beta = st.number_input("Slope Angle (β) [deg]", 0.0, 60.0, 25.0)
            z = st.number_input("Depth to Failure Plane (z) [m]", 0.5, 20.0, 5.0)
            
            # Dynamic Inputs
            c_prime, phi_prime, gamma, gamma_sat, u_val = 0.0, 30.0, 18.0, 20.0, 0.0
            
            if soil_case == "Dry Cohesionless (Sand)":
                phi_prime = st.number_input("Friction Angle (ϕ') [deg]", 10.0, 45.0, 32.0)
            elif soil_case == "Seepage Parallel to Slope":
                phi_prime = st.number_input("Friction Angle (ϕ') [deg]", 10.0, 45.0, 32.0)
                gamma_sat = st.number_input("Saturated Unit Weight (γ_sat) [kN/m³]", 15.0, 25.0, 20.0)
            else:
                c_prime = st.number_input("Cohesion (c') [kPa]", 0.0, 100.0, 10.0)
                phi_prime = st.number_input("Friction Angle (ϕ') [deg]", 0.0, 45.0, 25.0)
                gamma = st.number_input("Unit Weight (γ) [kN/m³]", 15.0, 25.0, 19.0)
                if st.checkbox("Include Pore Pressure?"):
                    u_val = st.number_input("Pore Pressure (u) [kPa]", 0.0, 100.0, 20.0)

            calc_t = st.button("Calculate FS", type="primary")

        with col_t2:
            st.subheader("Analysis")
            
            # Draw Diagram (Always visible)
            fig_t, ax_t = plt.subplots(figsize=(6, 4))
            x = np.linspace(0, 10, 100)
            beta_r = math.radians(beta)
            y_surf = x * math.tan(beta_r)
            # Failure plane is parallel at depth z (vertical depth z, or perpendicular?)
            # Usually z is vertical depth in formulas (gamma*z). 
            y_fail = y_surf - z
            
            ax_t.plot(x, y_surf, 'k-', linewidth=2, label="Ground Surface")
            ax_t.plot(x, y_fail, 'r--', linewidth=2, label="Failure Plane")
            ax_t.fill_between(x, y_fail, y_surf, color='#E6D690', alpha=0.5)
            
            if soil_case == "Seepage Parallel to Slope":
                ax_t.plot(x, y_surf - 0.2, 'b--', linewidth=1, label="Flow Line")
            
            # Annotations
            ax_t.text(5, 5*math.tan(beta_r) + 1, f"β={beta}°", ha='center')
            ax_t.arrow(5, 5*math.tan(beta_r), 0, -z, length_includes_head=True, head_width=0.2, color='black')
            ax_t.text(5.2, 5*math.tan(beta_r) - z/2, f"z={z}m", va='center')

            ax_t.set_aspect('equal')
            ax_t.legend()
            ax_t.axis('off')
            st.pyplot(fig_t)
            
            if calc_t:
                fs_val, form_tex = calculate_infinite_slope(beta, phi_prime, c_prime, gamma, gamma_sat, z, u_val, soil_case)
                st.latex(form_tex)
                
                if fs_val < 1.0:
                    st.error(f"**FS = {fs_val:.2f} (Unstable)**")
                elif fs_val < 1.5:
                    st.warning(f"**FS = {fs_val:.2f} (Marginal)**")
                else:
                    st.success(f"**FS = {fs_val:.2f} (Stable)**")

    # ---------------------------------------------------------
    # TAB 2: ROTATIONAL (CIRCULAR)
    # ---------------------------------------------------------
    with tab_rot:
        st.header("Rotational Slip Analysis")
        st.info("Analyzes circular failure surfaces. Choose the method below.")
        
        method = st.radio("**Calculation Method:**", ["A. Mass Procedure (Undrained / ϕ=0)", "B. Method of Slices"], horizontal=True)
        st.markdown("---")
        
        # --- A. MASS PROCEDURE ---
        if "Mass Procedure" in method:
            col_r1, col_r2 = st.columns([0.4, 0.6], gap="medium")
            
            with col_r1:
                st.subheader("1. Geometry & Loads")
                H_slope = st.number_input("Slope Height (H) [m]", 1.0, 50.0, 8.5)
                beta_slope = st.number_input("Slope Angle [deg]", 0.0, 90.0, 45.0)
                
                st.markdown("**Failure Circle**")
                R = st.number_input("Radius (R) [m]", 5.0, 50.0, 12.1)
                dist_d = st.number_input("Moment Arm (d) [m]", 0.0, 20.0, 4.5, help="Horizontal distance from Center O to Centroid of soil mass")
                
                st.subheader("2. Soil Properties")
                gamma_clay = st.number_input("Unit Weight (γ) [kN/m³]", 10.0, 25.0, 19.0)
                Cu = st.number_input("Undrained Shear Strength (Cu) [kPa]", 10.0, 200.0, 65.0)
                
                # Auto-calculate suggested W or let user override
                # Area approx for display
                # W = Area * gamma
                st.caption("Weight Calculation:")
                area_approx = st.number_input("Area of Sliding Mass [m²]", 1.0, 500.0, 70.0)
                W_calc = area_approx * gamma_clay
                st.write(f"Weight (W) = {W_calc:.1f} kN/m")
                
                calc_rot = st.button("Calculate FS (Mass Procedure)", type="primary")

            with col_r2:
                st.subheader("Failure Diagram")
                
                # Calculate Arc Length (approx based on R and geometry)
                # For visualization, we draw a generic arc matching the user input R
                fig_c, ax_c = plt.subplots(figsize=(8, 6))
                
                # Draw Slope
                # Toe at (0,0). Top at (H/tan(beta), H)
                toe_x, toe_y = 0, 0
                crest_x = H_slope / math.tan(math.radians(beta_slope))
                crest_y = H_slope
                
                ground_x = [-10, 0, crest_x, crest_x + 10]
                ground_y = [0, 0, crest_y, crest_y]
                
                ax_c.plot(ground_x, ground_y, 'k-', linewidth=2.5, label="Ground Surface")
                
                # Draw Failure Circle
                # Center O needs to be located.
                # User gave 'd' (horiz dist from O to Centroid). 
                # Let's assume O is at (d, y_center). 
                # We need O such that arc passes through Toe (0,0).
                # x_o^2 + y_o^2 = R^2.
                # This is under-constrained without knowing O coordinates. 
                # For Visual: Place O at (crest_x/2 - 2, H + R*0.8) arbitrarily to look like the sketch
                
                o_x = -2.0 # Slightly left of toe
                o_y = math.sqrt(R**2 - o_x**2) # Height to make arc pass toe
                
                # Draw Arc from Toe to Crest+
                # Angles
                theta_toe = math.degrees(math.atan2(0 - o_y, 0 - o_x))
                # End angle? approx
                theta_end = -30 
                
                arc = patches.Arc((o_x, o_y), 2*R, 2*R, theta1=theta_toe, theta2=theta_end, color='red', linestyle='--', linewidth=2, label="Failure Surface")
                ax_c.add_patch(arc)
                
                # Draw Center O
                ax_c.plot(o_x, o_y, 'bo', markersize=8, label="Center O")
                ax_c.text(o_x, o_y + 1, "O", ha='center', fontweight='bold')
                
                # Draw Moment Arm d
                # Centroid approx at x = d from O? No, d is horizontal distance.
                # Centroid X = o_x + d
                centroid_x = o_x + dist_d
                centroid_y = H_slope / 2 # Approx
                
                ax_c.plot(centroid_x, centroid_y, 'go', label="Centroid (W)")
                ax_c.arrow(centroid_x, centroid_y, 0, -3, head_width=0.5, color='purple', width=0.1)
                ax_c.text(centroid_x + 0.5, centroid_y - 2, "W", color='purple', fontweight='bold')
                
                # Dimension Lines
                # R
                ax_c.plot([o_x, 0], [o_y, 0], 'b:', linewidth=1)
                ax_c.text(o_x/2, o_y/2, f"R={R}m", color='blue', rotation=60)
                
                # d
                ax_c.plot([o_x, centroid_x], [o_y, o_y], 'k:', linewidth=1)
                ax_c.annotate(f"d={dist_d}m", xy=(o_x, o_y), xytext=(centroid_x, o_y), arrowprops=dict(arrowstyle='<->'))
                
                # Arc Angle Calculation
                # L_arc = R * theta_rad
                # We need theta_rad. 
                # Let's approximate L_arc from the arc drawing for visual, but use formula for calc.
                # Actually, L_arc is usually derived or given. 
                # Let's calculate theta using the intersection with top surface.
                # Intersection at y=H. x_int = o_x + sqrt(R^2 - (H-o_y)^2)
                try:
                    x_int = o_x + math.sqrt(R**2 - (crest_y - o_y)**2)
                    theta_rad = math.atan2(crest_y - o_y, x_int - o_x) - math.atan2(0 - o_y, 0 - o_x)
                    theta_deg = math.degrees(abs(theta_rad))
                    L_arc_calc = (theta_deg / 360) * 2 * math.pi * R
                except:
                    L_arc_calc = 20.0 # Fallback
                
                ax_c.text(2, 2, f"L_arc ≈ {L_arc_calc:.1f}m", color='red')

                ax_c.set_aspect('equal')
                ax_c.set_xlim(-10, 20)
                ax_c.set_ylim(-5, 25)
                ax_c.axis('off')
                ax_c.legend(loc='upper right')
                st.pyplot(fig_c)
                
                if calc_rot:
                    # FS = Resisting / Driving
                    # Resisting = Cu * L_arc * R
                    # Driving = W * d
                    
                    M_res = Cu * L_arc_calc * R
                    M_drv = W_calc * dist_d
                    
                    if M_drv > 0:
                        FS = M_res / M_drv
                        
                        st.markdown("### Results")
                        st.latex(r"FS = \frac{C_u \cdot L_{arc} \cdot R}{W \cdot d}")
                        st.write(f"**Resisting Moment:** {M_res:.1f} kNm")
                        st.write(f"**Driving Moment:** {M_drv:.1f} kNm")
                        
                        if FS < 1.0:
                            st.error(f"**FS = {FS:.2f} (Unstable)**")
                        else:
                            st.success(f"**FS = {FS:.2f} (Stable)**")
                    else:
                        st.error("Driving Moment is zero. Check 'd' or 'Weight'.")

        # --- B. METHOD OF SLICES ---
        else:
            col_s1, col_s2 = st.columns([0.4, 0.6], gap="medium")
            
            with col_s1:
                st.subheader("Global Parameters")
                c_sl = st.number_input("Cohesion (c') [kPa]", 0.0, 100.0, 5.0)
                phi_sl = st.number_input("Friction Angle (ϕ') [deg]", 0.0, 45.0, 30.0)
                
                st.markdown("### Slice Data Table")
                st.info("Edit the table below to add slices.")
                
                # Default Data
                default_data = pd.DataFrame([
                    {"Slice": 1, "Weight (kN)": 150, "Base Angle α (deg)": -10, "Base Length l (m)": 2.5, "u (kPa)": 0},
                    {"Slice": 2, "Weight (kN)": 250, "Base Angle α (deg)": 10, "Base Length l (m)": 2.5, "u (kPa)": 15},
                    {"Slice": 3, "Weight (kN)": 200, "Base Angle α (deg)": 35, "Base Length l (m)": 2.8, "u (kPa)": 10},
                ])
                
                edited_df = st.data_editor(default_data, num_rows="dynamic")
                
                calc_slices = st.button("Calculate FS (Ordinary Method)", type="primary")

            with col_s2:
                if calc_slices:
                    st.subheader("Calculation Results")
                    
                    sum_resisting = 0.0
                    sum_driving = 0.0
                    phi_rad = math.radians(phi_sl)
                    
                    details = []
                    
                    for index, row in edited_df.iterrows():
                        W = row["Weight (kN)"]
                        alpha = math.radians(row["Base Angle α (deg)"])
                        l = row["Base Length l (m)"]
                        u = row["u (kPa)"]
                        
                        # Normal Force N' = W cos alpha - u l
                        N_prime = (W * math.cos(alpha)) - (u * l)
                        
                        # Shear Strength (Resisting)
                        # T_f = c'l + N' tan phi
                        T_f = (c_sl * l) + (N_prime * math.tan(phi_rad))
                        
                        # Driving Force
                        T_d = W * math.sin(alpha)
                        
                        sum_resisting += T_f
                        sum_driving += T_d
                        
                        details.append({
                            "Slice": row["Slice"],
                            "Driving (T)": round(T_d, 1),
                            "Resisting (S)": round(T_f, 1)
                        })
                    
                    if sum_driving != 0:
                        FS_slices = sum_resisting / sum_driving
                        
                        st.metric("Factor of Safety", f"{FS_slices:.3f}")
                        st.latex(r"FS = \frac{\sum [c'l + (W \cos \alpha - ul)\tan \phi']}{\sum W \sin \alpha}")
                        
                        st.write(f"**Total Resisting:** {sum_resisting:.1f} kN")
                        st.write(f"**Total Driving:** {sum_driving:.1f} kN")
                        
                        # Show breakdown
                        st.dataframe(pd.DataFrame(details))
                        
                    else:
                        st.error("Total Driving Force is zero.")

    # ---------------------------------------------------------
    # TAB 3: COMPOUND (BLOCK)
    # ---------------------------------------------------------
    with tab_comp:
        st.header("Compound Slide Analysis")
        st.info("Analysis of a Block Failure (Active Wedge + Passive Wedge + Central Block).")
        
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.subheader("Forces")
            Pa = st.number_input("Active Thrust (Pa) [kN]", 0.0, 5000.0, 500.0)
            Pp = st.number_input("Passive Resistance (Pp) [kN]", 0.0, 5000.0, 200.0)
            W_block = st.number_input("Weight of Central Block [kN]", 0.0, 10000.0, 2000.0)
            
            st.subheader("Weak Layer")
            c_base = st.number_input("Base Cohesion (c') [kPa]", 0.0, 100.0, 5.0)
            phi_base = st.number_input("Base Friction (ϕ') [deg]", 0.0, 45.0, 20.0)
            L_base = st.number_input("Length of Base (L) [m]", 1.0, 100.0, 20.0)
            
            calc_blk = st.button("Calculate FS", type="primary")

        with col_c2:
            st.subheader("Block Diagram")
            fig_b, ax_b = plt.subplots(figsize=(6, 3))
            
            # Draw Block
            rect = patches.Rectangle((0, 0), 10, 3, facecolor='grey', alpha=0.3, edgecolor='black')
            ax_b.add_patch(rect)
            
            # Arrows
            # Pa (Driving) - Pushes Right
            ax_b.arrow(-2, 1.5, 1.5, 0, head_width=0.3, color='red', width=0.05)
            ax_b.text(-2.5, 1.5, "Pa", color='red', fontweight='bold', va='center')
            
            # Pp (Resisting) - Pushes Left
            ax_b.arrow(12, 1.5, -1.5, 0, head_width=0.3, color='green', width=0.05)
            ax_b.text(12.5, 1.5, "Pp", color='green', fontweight='bold', va='center')
            
            # Base Resistance
            ax_b.text(5, -0.5, f"Weak Layer\n(c'={c_base}, ϕ'={phi_base})", ha='center')
            
            ax_b.set_xlim(-4, 14)
            ax_b.set_ylim(-1, 5)
            ax_b.axis('off')
            st.pyplot(fig_b)
            
            if calc_blk:
                # T_base = c L + W tan phi
                resisting_base = (c_base * L_base) + (W_block * math.tan(math.radians(phi_base)))
                
                total_resisting = Pp + resisting_base
                total_driving = Pa
                
                if total_driving > 0:
                    FS_block = total_resisting / total_driving
                    st.latex(r"FS = \frac{P_p + (c'L + W_{block}\tan\phi')}{P_a}")
                    st.success(f"**Factor of Safety = {FS_block:.2f}**")
                    st.write(f"Base Resistance: {resisting_base:.1f} kN")
                else:
                    st.error("Active Thrust (Pa) must be > 0")

if __name__ == "__main__":
    app()
