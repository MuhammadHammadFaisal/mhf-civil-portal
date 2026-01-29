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
        sigma_n = gamma * z * (math.cos(beta_r)**2)
        tau_mob = gamma * z * math.sin(beta_r) * math.cos(beta_r)
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
                               ["Dry Cohesionless (Sand)", "Seepage Parallel to Slope", "Cohesive Soil (c-ϕ)"],
                               key="trans_case") 
            
            beta = st.number_input("Slope Angle (β) [deg]", 0.0, 60.0, 25.0, key="trans_beta") 
            z = st.number_input("Depth to Failure Plane (z) [m]", 0.5, 20.0, 5.0, key="trans_z")
            
            # Dynamic Inputs
            c_prime, phi_prime, gamma, gamma_sat, u_val = 0.0, 30.0, 18.0, 20.0, 0.0
            
            if soil_case == "Dry Cohesionless (Sand)":
                phi_prime = st.number_input("Friction Angle (ϕ') [deg]", 10.0, 45.0, 32.0, key="trans_phi_sand")
            elif soil_case == "Seepage Parallel to Slope":
                phi_prime = st.number_input("Friction Angle (ϕ') [deg]", 10.0, 45.0, 32.0, key="trans_phi_seep")
                gamma_sat = st.number_input("Saturated Unit Weight (γ_sat) [kN/m³]", 15.0, 25.0, 20.0, key="trans_gsat")
            else:
                c_prime = st.number_input("Cohesion (c') [kPa]", 0.0, 100.0, 10.0, key="trans_c")
                phi_prime = st.number_input("Friction Angle (ϕ') [deg]", 0.0, 45.0, 25.0, key="trans_phi_coh")
                gamma = st.number_input("Unit Weight (γ) [kN/m³]", 15.0, 25.0, 19.0, key="trans_gamma")
                if st.checkbox("Include Pore Pressure?", key="trans_check_u"):
                    u_val = st.number_input("Pore Pressure (u) [kPa]", 0.0, 100.0, 20.0, key="trans_u")

            calc_t = st.button("Calculate FS", type="primary", key="btn_calc_translational")

        with col_t2:
            st.subheader("Analysis")
            fig_t, ax_t = plt.subplots(figsize=(6, 4))
            x = np.linspace(0, 10, 100)
            beta_r = math.radians(beta)
            y_surf = x * math.tan(beta_r)
            y_fail = y_surf - z
            
            ax_t.plot(x, y_surf, 'k-', linewidth=2, label="Ground Surface")
            ax_t.plot(x, y_fail, 'r--', linewidth=2, label="Failure Plane")
            ax_t.fill_between(x, y_fail, y_surf, color='#E6D690', alpha=0.5)
            
            if soil_case == "Seepage Parallel to Slope":
                ax_t.plot(x, y_surf - 0.2, 'b--', linewidth=1, label="Flow Line")
            
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
        
        method = st.radio("**Calculation Method:**", 
                          ["A. Mass Procedure (Undrained / ϕ=0)", "B. Method of Slices"], 
                          horizontal=True, key="rot_method_select") 
        st.markdown("---")
        
        # --- A. MASS PROCEDURE (MATCHING HANDWRITTEN SKETCH) ---
        if "Mass Procedure" in method:
            col_r1, col_r2 = st.columns([0.4, 0.6], gap="medium")
            
            with col_r1:
                st.subheader("1. Geometry & Loads")
                H_slope = st.number_input("Slope Height (H) [m]", 1.0, 50.0, 8.5, key="mass_H")
                beta_slope = st.number_input("Slope Angle [deg]", 0.0, 90.0, 45.0, key="mass_beta")
                
                st.markdown("**Failure Circle**")
                R = st.number_input("Radius (R) [m]", 5.0, 50.0, 12.1, key="mass_R")
                dist_d = st.number_input("Moment Arm (d) [m]", 0.0, 20.0, 4.5, help="Horizontal distance from Center O to Centroid", key="mass_d")
                
                st.subheader("2. Soil Properties")
                gamma_clay = st.number_input("Unit Weight (γ) [kN/m³]", 10.0, 25.0, 19.0, key="mass_gamma")
                Cu = st.number_input("Undrained Shear Strength (Cu) [kPa]", 10.0, 200.0, 65.0, key="mass_cu")
                
                st.caption("Weight Calculation:")
                area_approx = st.number_input("Area of Sliding Mass [m²]", 1.0, 500.0, 70.0, key="mass_area")
                W_calc = area_approx * gamma_clay
                st.write(f"Weight (W) = {W_calc:.1f} kN/m")
                
                calc_rot = st.button("Calculate FS (Mass Procedure)", type="primary", key="btn_calc_mass")

            with col_r2:
                st.subheader("Failure Diagram")
                # Visualization to match sketch image_17a399.jpg
                fig_c, ax_c = plt.subplots(figsize=(8, 6))
                
                # 1. Slope Geometry
                # Toe at (0,0). Crest at (X_crest, H)
                X_crest = H_slope / math.tan(math.radians(beta_slope))
                Y_crest = H_slope
                
                # Ground Polygon
                ground_x = [-5, 0, X_crest, X_crest + 10]
                ground_y = [0, 0, Y_crest, Y_crest]
                ax_c.plot(ground_x, ground_y, 'k-', linewidth=2)
                
                # 2. Failure Circle (Arc)
                # Need Center O (Xc, Yc). 
                # Constraint 1: Passes through Toe (0,0) -> Xc^2 + Yc^2 = R^2
                # Constraint 2: Visual placement. Usually Yc > H. 
                # Let's assume Xc is slightly to the right of toe for a typical "deep" slip, 
                # or rely on the geometric constraint that it cuts the top surface.
                
                # Try to place O such that the arc looks like the sketch
                # Sketch has O almost vertically above toe. Let's assume Xc = 0.5m
                Xc = 0.5
                Yc = math.sqrt(R**2 - Xc**2) # Height to ensure it passes through (0,0)
                
                # Find intersection with top surface (y = H)
                # (x - Xc)^2 + (H - Yc)^2 = R^2
                # (x - Xc)^2 = R^2 - (H - Yc)^2
                term = R**2 - (Y_crest - Yc)**2
                if term > 0:
                    x_intersect = Xc + math.sqrt(term)
                    
                    # 3. Create the "Wedge" Polygon (Hatched)
                    # We need points along the arc from 0 to x_intersect
                    # Angle range
                    theta_start = math.atan2(0 - Yc, 0 - Xc) # Angle to toe
                    theta_end = math.atan2(Y_crest - Yc, x_intersect - Xc) # Angle to crest intersection
                    
                    # Generate arc points
                    thetas = np.linspace(theta_start, theta_end, 50)
                    arc_x = Xc + R * np.cos(thetas)
                    arc_y = Yc + R * np.sin(thetas)
                    
                    # Combine into polygon vertices: Toe -> Arc -> Crest Intersect -> Crest Corner -> Toe
                    # If x_intersect is beyond crest, we go to crest corner.
                    poly_verts = list(zip(arc_x, arc_y))
                    poly_verts.append((X_crest, Y_crest)) # Top of slope
                    poly_verts.append((0, 0)) # Close at toe
                    
                    # Hatching Patch
                    soil_mass = patches.Polygon(poly_verts, closed=True, facecolor='none', edgecolor='black', hatch='//', alpha=0.5)
                    ax_c.add_patch(soil_mass)
                    ax_c.plot(arc_x, arc_y, 'k-', linewidth=1.5) # Draw arc solid
                    
                    # 4. Draw Center O and Radius
                    ax_c.plot(Xc, Yc, 'bo', label="O")
                    ax_c.plot([Xc, 0], [Yc, 0], 'b--', linewidth=1) # Radius line
                    ax_c.text(Xc/2, Yc/2, f"R={R}m", color='blue', rotation=70, ha='right')
                    
                    # 5. Centroid W and Dimension d
                    # Centroid X = Xc + d
                    X_w = Xc + dist_d
                    Y_w = Y_crest / 2 # Approx height
                    ax_c.arrow(X_w, Y_w, 0, -3, head_width=0.5, color='black', width=0.1)
                    ax_c.text(X_w + 0.5, Y_w - 3, "W", fontweight='bold')
                    
                    # Dimension line for d
                    ax_c.plot([Xc, Xc], [Yc, Yc+2], 'k-', linewidth=0.5) # Extension line at O
                    ax_c.plot([X_w, X_w], [Y_w, Yc+2], 'k-', linewidth=0.5) # Extension line at W
                    ax_c.annotate(f"d={dist_d}m", xy=(Xc, Yc+1.5), xytext=(X_w, Yc+1.5), arrowprops=dict(arrowstyle='<->'))
                    
                    # Dimension line for H
                    ax_c.annotate(f"H={H_slope}m", xy=(-2, 0), xytext=(-2, Y_crest), arrowprops=dict(arrowstyle='<->'))
                    
                    # Calculate Arc Length for Display
                    theta_deg = math.degrees(theta_end - theta_start)
                    L_calc = (theta_deg/360) * 2 * math.pi * R
                    
                else:
                    st.error("Geometry Error: Failure circle does not intersect slope top.")
                    L_calc = 0

                ax_c.set_aspect('equal')
                ax_c.set_xlim(-5, X_crest + 10)
                ax_c.set_ylim(-2, Yc + 5)
                ax_c.axis('off')
                st.pyplot(fig_c)
                
                if calc_rot:
                    M_res = Cu * L_calc * R
                    M_drv = W_calc * dist_d
                    
                    if M_drv > 0:
                        FS = M_res / M_drv
                        st.markdown("### Results")
                        st.latex(r"FS = \frac{C_u \cdot L_{arc} \cdot R}{W \cdot d}")
                        st.write(f"**Calculated Arc Length:** {L_calc:.2f} m")
                        st.write(f"**Resisting Moment:** {M_res:.1f} kNm")
                        st.write(f"**Driving Moment:** {M_drv:.1f} kNm")
                        
                        if FS < 1.0:
                            st.error(f"**FS = {FS:.2f} (Unstable)**")
                        else:
                            st.success(f"**FS = {FS:.2f} (Stable)**")
                    else:
                        st.error("Driving Moment is zero.")

        # --- B. METHOD OF SLICES ---
        else:
            col_s1, col_s2 = st.columns([0.4, 0.6], gap="medium")
            
            with col_s1:
                st.subheader("Global Parameters")
                c_sl = st.number_input("Cohesion (c') [kPa]", 0.0, 100.0, 5.0, key="slice_c")
                phi_sl = st.number_input("Friction Angle (ϕ') [deg]", 0.0, 45.0, 30.0, key="slice_phi")
                
                st.markdown("### Slice Data Table")
                st.info("Edit the table below to add slices.")
                
                default_data = pd.DataFrame([
                    {"Slice": 1, "Weight (kN)": 150, "Base Angle α (deg)": -10, "Base Length l (m)": 2.5, "u (kPa)": 0},
                    {"Slice": 2, "Weight (kN)": 250, "Base Angle α (deg)": 10, "Base Length l (m)": 2.5, "u (kPa)": 15},
                    {"Slice": 3, "Weight (kN)": 200, "Base Angle α (deg)": 35, "Base Length l (m)": 2.8, "u (kPa)": 10},
                ])
                
                edited_df = st.data_editor(default_data, num_rows="dynamic", key="slice_editor")
                
                calc_slices = st.button("Calculate FS (Ordinary Method)", type="primary", key="btn_calc_slices")

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
                        
                        N_prime = (W * math.cos(alpha)) - (u * l)
                        T_f = (c_sl * l) + (N_prime * math.tan(phi_rad))
                        T_d = W * math.sin(alpha)
                        
                        sum_resisting += T_f
                        sum_driving += T_d
                        
                        details.append({"Slice": row["Slice"], "Driving (T)": round(T_d, 1), "Resisting (S)": round(T_f, 1)})
                    
                    if sum_driving != 0:
                        FS_slices = sum_resisting / sum_driving
                        st.metric("Factor of Safety", f"{FS_slices:.3f}")
                        st.latex(r"FS = \frac{\sum [c'l + (W \cos \alpha - ul)\tan \phi']}{\sum W \sin \alpha}")
                        st.dataframe(pd.DataFrame(details))
                    else:
                        st.error("Total Driving Force is zero.")

    # ---------------------------------------------------------
    # TAB 3: COMPOUND (BLOCK)
    # ---------------------------------------------------------
    with tab_comp:
        st.header("Compound Slide Analysis")
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.subheader("Forces")
            Pa = st.number_input("Active Thrust (Pa) [kN]", 0.0, 5000.0, 500.0, key="block_Pa")
            Pp = st.number_input("Passive Resistance (Pp) [kN]", 0.0, 5000.0, 200.0, key="block_Pp")
            W_block = st.number_input("Weight of Central Block [kN]", 0.0, 10000.0, 2000.0, key="block_W")
            
            st.subheader("Weak Layer")
            c_base = st.number_input("Base Cohesion (c') [kPa]", 0.0, 100.0, 5.0, key="block_c")
            phi_base = st.number_input("Base Friction (ϕ') [deg]", 0.0, 45.0, 20.0, key="block_phi")
            L_base = st.number_input("Length of Base (L) [m]", 1.0, 100.0, 20.0, key="block_L")
            
            calc_blk = st.button("Calculate FS", type="primary", key="btn_calc_block")

        with col_c2:
            st.subheader("Block Diagram")
            fig_b, ax_b = plt.subplots(figsize=(6, 3))
            rect = patches.Rectangle((0, 0), 10, 3, facecolor='grey', alpha=0.3, edgecolor='black')
            ax_b.add_patch(rect)
            
            ax_b.arrow(-2, 1.5, 1.5, 0, head_width=0.3, color='red', width=0.05)
            ax_b.text(-2.5, 1.5, "Pa", color='red', fontweight='bold', va='center')
            ax_b.arrow(12, 1.5, -1.5, 0, head_width=0.3, color='green', width=0.05)
            ax_b.text(12.5, 1.5, "Pp", color='green', fontweight='bold', va='center')
            ax_b.text(5, -0.5, f"Weak Layer\n(c'={c_base}, ϕ'={phi_base})", ha='center')
            
            ax_b.set_xlim(-4, 14); ax_b.set_ylim(-1, 5); ax_b.axis('off')
            st.pyplot(fig_b)
            
            if calc_blk:
                resisting_base = (c_base * L_base) + (W_block * math.tan(math.radians(phi_base)))
                total_resisting = Pp + resisting_base
                total_driving = Pa
                
                if total_driving > 0:
                    FS_block = total_resisting / total_driving
                    st.latex(r"FS = \frac{P_p + (c'L + W_{block}\tan\phi')}{P_a}")
                    st.success(f"**Factor of Safety = {FS_block:.2f}**")
                else:
                    st.error("Active Thrust (Pa) must be > 0")

if __name__ == "__main__":
    app()
