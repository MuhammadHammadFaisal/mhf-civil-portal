import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import math

def app():
    st.title("Slope Stability Calculator ⛰️")
    st.markdown("Based on **Chapter 8** of Soil Mechanics Notes.")
    
    tab_trans, tab_rot, tab_comp = st.tabs([
        "1. Translational (Infinite)", 
        "2. Rotational (Circular)", 
        "3. Compound (Block)"
    ])

    # =========================================================================
    # TAB 1: TRANSLATIONAL SLIDE (INFINITE SLOPE)
    # =========================================================================
    with tab_trans:
        st.header("Infinite Slope Analysis")
        st.info("Assumes failure plane is parallel to the ground surface. Common for long natural slopes.")
        
        col_t1, col_t2 = st.columns([1, 1])
        
        with col_t1:
            st.subheader("Slope & Soil")
            beta = st.number_input("Slope Angle (β) [deg]", 0.0, 60.0, 25.0)
            z = st.number_input("Depth to Failure Plane (z) [m]", 1.0, 20.0, 5.0)
            
            soil_case = st.radio("Soil Condition:", ["Dry Cohesionless (Sand)", "Seepage Parallel to Slope", "Cohesive Soil (c-ϕ)"])
            
            c_prime = 0.0
            phi_prime = 30.0
            gamma = 18.0
            gamma_sat = 20.0
            
            if soil_case == "Dry Cohesionless (Sand)":
                phi_prime = st.number_input("Friction Angle (ϕ') [deg]", 10.0, 45.0, 32.0)
            elif soil_case == "Seepage Parallel to Slope":
                phi_prime = st.number_input("Friction Angle (ϕ') [deg]", 10.0, 45.0, 32.0)
                gamma_sat = st.number_input("Saturated Unit Weight (γ_sat) [kN/m³]", 15.0, 25.0, 20.0)
            else: # Cohesive
                c_prime = st.number_input("Cohesion (c') [kPa]", 0.0, 100.0, 10.0)
                phi_prime = st.number_input("Friction Angle (ϕ') [deg]", 0.0, 45.0, 25.0)
                gamma = st.number_input("Unit Weight (γ) [kN/m³]", 15.0, 25.0, 19.0)
                u_cond = st.checkbox("Include Pore Pressure (u)?")
                u_val = 0.0
                if u_cond:
                    u_val = st.number_input("Pore Pressure at Depth z (u) [kPa]", 0.0, 100.0, 20.0)

        with col_t2:
            st.subheader("Calculation")
            
            beta_r = math.radians(beta)
            phi_r = math.radians(phi_prime)
            
            fs = 0.0
            formula_tex = ""
            
            if soil_case == "Dry Cohesionless (Sand)":
                # FS = tan(phi) / tan(beta)
                if beta > 0:
                    fs = math.tan(phi_r) / math.tan(beta_r)
                    formula_tex = r"FS = \frac{\tan \phi'}{\tan \beta}"
                else:
                    fs = 999.0
                    
            elif soil_case == "Seepage Parallel to Slope":
                # FS = (gamma' / gamma_sat) * (tan phi / tan beta)
                gamma_w = 9.81
                gamma_prime = gamma_sat - gamma_w
                if beta > 0:
                    fs = (gamma_prime / gamma_sat) * (math.tan(phi_r) / math.tan(beta_r))
                    formula_tex = r"FS = \frac{\gamma'}{\gamma_{sat}} \frac{\tan \phi'}{\tan \beta}"
                
            else: # Cohesive c-phi
                # FS = (c + (gamma*z*cos^2(beta) - u)tan(phi)) / (gamma*z*sin(beta)cos(beta))
                # Normal Stress
                sigma_n = gamma * z * (math.cos(beta_r)**2)
                tau_mob = gamma * z * math.sin(beta_r) * math.cos(beta_r)
                
                resisting = c_prime + (sigma_n - u_val) * math.tan(phi_r)
                if tau_mob > 0:
                    fs = resisting / tau_mob
                    formula_tex = r"FS = \frac{c' + (\gamma z \cos^2\beta - u)\tan\phi'}{\gamma z \sin\beta \cos\beta}"
            
            st.latex(formula_tex)
            
            if fs < 1.0:
                st.error(f"**Factor of Safety = {fs:.2f} (Unstable)**")
            elif fs < 1.5:
                st.warning(f"**Factor of Safety = {fs:.2f} (Marginal)**")
            else:
                st.success(f"**Factor of Safety = {fs:.2f} (Stable)**")

            # Diagram
            fig, ax = plt.subplots(figsize=(6,3))
            x = np.linspace(0, 10, 100)
            y_surf = (x) * np.tan(math.radians(beta))
            y_fail = y_surf - z
            ax.plot(x, y_surf, 'k-', linewidth=2, label="Surface")
            ax.plot(x, y_fail, 'r--', linewidth=2, label="Failure Plane")
            ax.fill_between(x, y_fail, y_surf, color='#E6D690', alpha=0.5)
            
            if soil_case == "Seepage Parallel to Slope":
                ax.plot(x, y_surf, 'b--', linewidth=1, label="Flow Line")
            
            ax.set_aspect('equal')
            ax.legend()
            ax.axis('off')
            st.pyplot(fig)

    # =========================================================================
    # TAB 2: ROTATIONAL SLIDE (CIRCULAR)
    # =========================================================================
    with tab_rot:
        st.header("Rotational Slip Analysis")
        st.info("Analyzes circular failure surfaces common in clay slopes.")
        
        # METHOD SELECTOR
        method = st.radio(
            "Select Calculation Method:",
            ["A. Mass Procedure (Undrained / ϕ=0)", "B. Method of Slices (Fellenius)"],
            horizontal=True
        )
        st.markdown("---")
        
        col_r1, col_r2 = st.columns([1, 1])
        
        # --- OPTION A: MASS PROCEDURE ---
        if "Mass Procedure" in method:
            with col_r1:
                st.subheader("Inputs")
                Cu = st.number_input("Undrained Shear Strength (Cu) [kPa]", 10.0, 200.0, 50.0)
                R = st.number_input("Radius of Failure Circle (R) [m]", 5.0, 50.0, 12.0)
                L_arc = st.number_input("Length of Failure Arc (L_arc) [m]", 5.0, 100.0, 18.0)
                
                st.markdown("#### Driving Force")
                W = st.number_input("Weight of Sliding Mass (W) [kN/m]", 100.0, 5000.0, 1200.0)
                d = st.number_input("Moment Arm (d) [m]", 0.1, 20.0, 4.5, help="Horizontal distance from center of rotation O to center of gravity of soil mass.")
                
            with col_r2:
                st.subheader("Calculation")
                # Moments
                M_resisting = Cu * L_arc * R
                M_driving = W * d
                
                FS = M_resisting / M_driving
                
                st.latex(r"FS = \frac{M_{resist}}{M_{drive}} = \frac{C_u \cdot L_{arc} \cdot R}{W \cdot d}")
                st.write(f"**Resisting Moment:** {M_resisting:.1f} kNm")
                st.write(f"**Driving Moment:** {M_driving:.1f} kNm")
                
                if FS < 1.0:
                    st.error(f"**FS = {FS:.2f} (Unstable)**")
                else:
                    st.success(f"**FS = {FS:.2f} (Stable)**")
                    
                # Diagram placeholder
                fig, ax = plt.subplots(figsize=(4,4))
                circle = patches.Arc((0, 10), R*2, R*2, theta1=210, theta2=330, color='red', linestyle='--')
                ax.add_patch(circle)
                ax.plot([0],[10], 'bo', label="Center O")
                ax.plot([-5, 5], [0, 0], 'k-', linewidth=2) # Ground
                ax.set_xlim(-R, R)
                ax.set_ylim(-5, R+2)
                ax.axis('off')
                ax.text(0, 11, "O", ha='center')
                st.pyplot(fig)

        # --- OPTION B: METHOD OF SLICES ---
        else:
            st.info("💡 Input data for representative slices (typically 5-10).")
            
            with col_r1:
                # Soil Properties Global
                st.markdown("**Global Soil Parameters**")
                c_sl = st.number_input("Cohesion (c') [kPa]", 0.0, 100.0, 5.0, key="sl_c")
                phi_sl = st.number_input("Friction Angle (ϕ') [deg]", 0.0, 45.0, 30.0, key="sl_p")
                
                # Slices Input Table
                st.markdown("**Slice Data**")
                
                # Default Data
                default_data = pd.DataFrame([
                    {"Slice": 1, "Weight (kN)": 150, "Base Angle α (deg)": -10, "Base Length l (m)": 2.5, "Pore Pressure u (kPa)": 0},
                    {"Slice": 2, "Weight (kN)": 250, "Base Angle α (deg)": 10, "Base Length l (m)": 2.5, "Pore Pressure u (kPa)": 15},
                    {"Slice": 3, "Weight (kN)": 200, "Base Angle α (deg)": 35, "Base Length l (m)": 2.8, "Pore Pressure u (kPa)": 10},
                ])
                
                edited_df = st.data_editor(default_data, num_rows="dynamic")
                
            with col_r2:
                if st.button("Calculate FS (Ordinary Method)"):
                    # FS = Sum(Resisting) / Sum(Driving)
                    # Resisting = c'l + (W cos a - u l) tan phi
                    # Driving = W sin a
                    
                    sum_resisting = 0.0
                    sum_driving = 0.0
                    phi_rad = math.radians(phi_sl)
                    
                    for index, row in edited_df.iterrows():
                        W = row["Weight (kN)"]
                        alpha = math.radians(row["Base Angle α (deg)"])
                        l = row["Base Length l (m)"]
                        u = row["Pore Pressure u (kPa)"]
                        
                        # Normal Force N' = W cos alpha - u l
                        N_prime = (W * math.cos(alpha)) - (u * l)
                        
                        # Shear Strength
                        T_f = (c_sl * l) + (N_prime * math.tan(phi_rad))
                        
                        # Driving Force
                        T_d = W * math.sin(alpha)
                        
                        sum_resisting += T_f
                        sum_driving += T_d
                    
                    if sum_driving != 0:
                        FS_slices = sum_resisting / sum_driving
                        st.metric("Factor of Safety", f"{FS_slices:.3f}")
                        
                        st.latex(r"FS = \frac{\sum [c'l + (W \cos \alpha - ul)\tan \phi']}{\sum W \sin \alpha}")
                        st.write(f"Sum Resisting Forces: {sum_resisting:.1f} kN")
                        st.write(f"Sum Driving Forces: {sum_driving:.1f} kN")
                    else:
                        st.error("Driving forces are zero. Check Slice Angles.")

    # =========================================================================
    # TAB 3: COMPOUND SLIDE (BLOCK ANALYSIS)
    # =========================================================================
    with tab_comp:
        st.header("Compound Slide (Block & Wedge)")
        st.info("Used when failure occurs along a weak layer (translational) combined with an active/passive wedge.")
        
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.subheader("Forces & Geometry")
            Pa = st.number_input("Active Thrust (Driving) Pa [kN]", 0.0, 5000.0, 500.0)
            Pp = st.number_input("Passive Resistance (Resisting) Pp [kN]", 0.0, 5000.0, 200.0)
            W_block = st.number_input("Weight of Central Block [kN]", 0.0, 10000.0, 2000.0)
            
            st.subheader("Weak Layer Properties")
            c_base = st.number_input("Base Cohesion (c') [kPa]", 0.0, 100.0, 5.0, key="blk_c")
            phi_base = st.number_input("Base Friction (ϕ') [deg]", 0.0, 45.0, 20.0, key="blk_p")
            L_base = st.number_input("Length of Base (L) [m]", 1.0, 100.0, 20.0)

        with col_c2:
            st.subheader("Analysis")
            # FS = (Pp + Resisting_Base) / Pa
            
            # Base Resistance T = c'L + N' tan phi
            # Assuming N' = W_block (Flat base)
            N_prime_base = W_block 
            T_base = (c_base * L_base) + (N_prime_base * math.tan(math.radians(phi_base)))
            
            Total_Resisting = Pp + T_base
            Total_Driving = Pa
            
            if Total_Driving > 0:
                FS_block = Total_Resisting / Total_Driving
                
                st.latex(r"FS = \frac{P_p + (c'L + W_{block}\tan\phi')}{P_a}")
                
                st.write(f"**Base Resistance:** {T_base:.1f} kN")
                st.write(f"**Total Resisting (Pp + Base):** {Total_Resisting:.1f} kN")
                
                if FS_block < 1:
                    st.error(f"**FS = {FS_block:.2f} (Unstable)**")
                else:
                    st.success(f"**FS = {FS_block:.2f} (Stable)**")
            
            # Diagram
            fig, ax = plt.subplots(figsize=(6,2))
            # Draw Block
            rect = patches.Rectangle((0,0), 10, 2, facecolor='grey', alpha=0.3)
            ax.add_patch(rect)
            # Arrows
            ax.arrow(12, 1, -1.5, 0, head_width=0.2, color='red', label='Pa') # Driving
            ax.arrow(-2, 1, 1.5, 0, head_width=0.2, color='green', label='Pp') # Resisting
            ax.text(12.5, 1, "Pa", color='red', va='center')
            ax.text(-3, 1, "Pp", color='green', va='center')
            ax.text(5, -0.5, "Weak Layer (c', ϕ')", ha='center')
            
            ax.set_xlim(-4, 14)
            ax.set_ylim(-1, 4)
            ax.axis('off')
            st.pyplot(fig)

if __name__ == "__main__":
    app()
