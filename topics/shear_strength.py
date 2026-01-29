import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import math

def app():
    # =================================================================
    # 1. HEADER & MODE
    # =================================================================
    st.header("Shear Strength Analysis (Mohr-Coulomb)")
    st.markdown("---")

    calc_mode = st.radio(
        "**Calculation Goal:**",
        ["1. Forward Analysis (Safety Check)", "2. Back Analysis (Find Parameters from Lab Data)"],
        horizontal=True
    )
    st.markdown("---")

    # =================================================================
    # 2. GLOBAL PARAMETERS
    # =================================================================
    # For Shear Strength, global params are usually the soil constants (in Mode 1)
    # or empty in Mode 2.
    
    global_params = {}
    
    col_g1, col_g2 = st.columns(2)
    
    if "1. Forward" in calc_mode:
        with col_g1:
            c_prime = st.number_input("Cohesion ($c'$) [kPa]", value=10.0, step=1.0)
        with col_g2:
            phi_deg = st.number_input("Friction Angle ($\phi'$) [deg]", value=30.0, step=1.0)
        global_params = {"c": c_prime, "phi": phi_deg}
    else:
        with col_g1:
             st.info("Enter data from **2 Failure Tests** to find $c'$ and $\phi'$.")
        # No globals for Mode 2, they are calculated results.

    # =================================================================
    # 3. LAYOUT: INPUTS (Left) - VISUALIZATION (Right)
    # =================================================================
    col_input, col_viz = st.columns([1.5, 1])

    test_data = []
    
    with col_input:
        st.subheader("Stress Conditions / Lab Data")
        
        # Determine number of 'samples' based on mode
        num_tests = 1 if "1. Forward" in calc_mode else 2
        
        for i in range(num_tests):
            title = f"Stress State" if num_tests == 1 else f"Lab Test #{i+1} (at Failure)"
            expanded_state = True
            
            with st.expander(title, expanded=expanded_state):
                c1, c2 = st.columns(2)
                
                # Inputs: Minor Principal Stress (Confining) and Major Principal Stress
                sig3 = c1.number_input(f"$\sigma'_3$ (Confining) [kPa]", value=50.0 + (i*50), key=f"s3_{i}")
                
                if "1. Forward" in calc_mode:
                    # In forward mode, user defines the applied stress to check safety
                    sig1 = c2.number_input(f"$\sigma'_1$ (Major) [kPa]", value=120.0, key=f"s1_{i}")
                    user_comment = "User defined stress state"
                else:
                    # In back analysis, these are failure stresses from the lab
                    sig1 = c2.number_input(f"$\sigma'_{{1f}}$ (Failure) [kPa]", value=150.0 + (i*150), key=f"s1f_{i}")
                    user_comment = "Measured at failure"

                # Calculate center and radius for this specific circle
                center = (sig1 + sig3) / 2
                radius = (sig1 - sig3) / 2
                
                test_data.append({
                    "id": i+1,
                    "sig3": sig3,
                    "sig1": sig1,
                    "center": center,
                    "radius": radius,
                    "comment": user_comment
                })

    # =================================================================
    # HELPER: CALCULATION ENGINE
    # =================================================================
    def calculate_safety(test, g_params):
        # Unpack
        s1 = test['sig1']
        s3 = test['sig3']
        c = g_params['c']
        phi = g_params['phi']
        phi_rad = math.radians(phi)
        
        # 1. Calculate Shear Strength available on the failure plane
        # Based on Mohr-Coulomb: tau_f = c + sigma * tan(phi)
        
        # We need to find the theoretical max sigma1 this soil can take at this sigma3
        # Formula: sig1_fail = sig3 * tan^2(45 + phi/2) + 2*c*tan(45 + phi/2)
        tan_factor = math.tan(math.radians(45 + phi/2))
        sig1_max_theoretical = (s3 * (tan_factor**2)) + (2 * c * tan_factor)
        
        # Safety Analysis
        is_safe = s1 < sig1_max_theoretical
        fs_stress = sig1_max_theoretical / s1 if s1 > 0 else 0
        
        math_log = [
            f"**1. Circle Geometry:**",
            f"Center = $({s1:.1f} + {s3:.1f})/2 = {test['center']:.1f}$ kPa",
            f"Radius = $({s1:.1f} - {s3:.1f})/2 = {test['radius']:.1f}$ kPa",
            f"**2. Failure Criteria:**",
            f"Max Theoretical $\sigma'_1$ = ${sig1_max_theoretical:.2f}$ kPa",
            f"Applied $\sigma'_1$ = ${s1:.2f}$ kPa",
        ]
        
        status = "SAFE" if is_safe else "FAILURE"
        
        return {
            "status": status,
            "sig1_max": sig1_max_theoretical,
            "log": math_log
        }

    def solve_parameters(tests):
        # Solves for c and phi given two failure circles
        # Uses the relationship: sig1 = sig3 * Kp + 2*c*sqrt(Kp)
        # Where Kp = tan^2(45 + phi/2)
        # This is a linear regression of form: y = mx + b
        # y = sig1, x = sig3, m = Kp, b = 2*c*sqrt(Kp)
        
        t1 = tests[0]
        t2 = tests[1]
        
        dy = t2['sig1'] - t1['sig1']
        dx = t2['sig3'] - t1['sig3']
        
        log = ["**Back Calculation Steps:**"]
        
        if dx == 0:
            return {"c": 0, "phi": 0, "log": ["Error: Confining pressures must be different."]}
            
        Kp = dy / dx # Slope m
        
        # Find phi
        # Kp = tan^2(45 + phi/2)  -> sqrt(Kp) = tan(45 + phi/2)
        # atan(sqrt(Kp)) = 45 + phi/2 -> phi = 2 * (atan(sqrt(Kp)) - 45)
        
        if Kp < 1:
            phi_val = 0
            log.append("Slope < 1, impossible for Mohr-Coulomb.")
        else:
            term = math.atan(math.sqrt(Kp))
            phi_rad = 2 * (term - math.radians(45))
            phi_val = math.degrees(phi_rad)
        
        # Find c
        # Intercept b = sig1 - m*sig3
        # b = 2*c*sqrt(Kp) -> c = b / (2*sqrt(Kp))
        b = t1['sig1'] - (Kp * t1['sig3'])
        c_val = b / (2 * math.sqrt(Kp))
        
        log.append(f"Slope (m) $\Delta\sigma_1 / \Delta\sigma_3$ = {Kp:.3f}")
        log.append(f"Friction Angle $\phi' = {phi_val:.2f}^\circ$")
        log.append(f"Cohesion $c' = {c_val:.2f}$ kPa")
        
        return {"c": c_val, "phi": phi_val, "log": log}

    # --- VISUALIZER ---
    with col_viz:
        st.subheader("Mohr Circles")
        fig, ax = plt.subplots(figsize=(6, 6))
        
        # Dynamic axis limits
        max_stress = max([t['sig1'] for t in test_data]) if test_data else 100
        limit = max_stress * 1.2
        ax.set_xlim(0, limit)
        ax.set_ylim(0, limit * 0.6) # Y axis is Shear Stress (tau)
        ax.set_aspect('equal')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.set_xlabel("Normal Stress $\sigma'$ (kPa)")
        ax.set_ylabel("Shear Stress $\\tau$ (kPa)")
        
        # Draw Circles
        for t in test_data:
            # Draw top half of circle (Arc)
            arc = patches.Arc((t['center'], 0), t['radius']*2, t['radius']*2, 
                              theta1=0, theta2=180, edgecolor='blue', linewidth=1.5)
            ax.add_patch(arc)
            ax.plot([t['sig3'], t['sig1']], [0, 0], 'bo', markersize=4)
        
        # Draw Envelope
        if "1. Forward" in calc_mode:
            c = global_params['c']
            phi = global_params['phi']
            color = 'red'
        elif len(test_data) == 2:
            res = solve_parameters(test_data)
            c = res['c']
            phi = res['phi']
            color = 'green'
        else:
            c, phi = 0, 0
            color = 'gray'

        if phi >= 0:
            x_vals = np.array([0, limit])
            y_vals = c + x_vals * np.tan(math.radians(phi))
            ax.plot(x_vals, y_vals, color=color, linewidth=2, linestyle='-', label='Failure Envelope')
            ax.text(limit*0.1, c + limit*0.1*np.tan(math.radians(phi)) + limit*0.05, 
                    f"$\\tau = {c:.1f} + \\sigma' \\tan({phi:.1f}^\\circ)$", color=color, fontsize=9)

        st.pyplot(fig)

    # =================================================================
    # 4. RESULTS SECTION
    # =================================================================

    # -------------------------------------------------------------
    # MODE 1: FORWARD ANALYSIS
    # -------------------------------------------------------------
    if "1. Forward" in calc_mode:
        if st.button("Check Safety", type="primary"):
            st.markdown("### Results: Safety Analysis")
            
            # Since we only have 1 test in this mode
            t = test_data[0]
            res = calculate_safety(t, global_params)
            
            c_res, c_calc = st.columns([1, 1])
            
            with c_res:
                if res['status'] == "SAFE":
                    st.success(f"**Status: SAFE**")
                    st.caption("The Mohr circle is completely below the failure envelope.")
                else:
                    st.error(f"**Status: FAILURE**")
                    st.caption("The Mohr circle crosses the failure envelope.")
                
                st.metric("Max Sustainable $\sigma'_1$", f"{res['sig1_max']:.2f} kPa")
            
            with c_calc:
                 with st.expander("Calculation Log"):
                     for line in res['log']:
                         st.write(line)

    # -------------------------------------------------------------
    # MODE 2: BACK ANALYSIS
    # -------------------------------------------------------------
    else:
        if st.button("Calculate Parameters ($c', \phi'$)", type="primary"):
            st.markdown("### Results: Strength Parameters")
            
            if len(test_data) < 2:
                st.error("Please ensure 2 tests are defined.")
            else:
                res = solve_parameters(test_data)
                
                c_res, c_log = st.columns(2)
                
                with c_res:
                    st.success(f"**Parameters Found:**")
                    st.metric("Cohesion ($c'$)", f"{res['c']:.2f} kPa")
                    st.metric("Friction Angle ($\phi'$)", f"{res['phi']:.2f} °")
                
                with c_log:
                    with st.expander("Show Derivation"):
                        for line in res['log']:
                             st.write(line)
                        st.latex(r"\sigma'_1 = \sigma'_3 \tan^2(45 + \phi'/2) + 2c'\tan(45 + \phi'/2)")

if __name__ == "__main__":
    app()
