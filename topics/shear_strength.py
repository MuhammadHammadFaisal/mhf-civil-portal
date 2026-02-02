import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import math

def app():
    # =================================================================
    # 1. HEADER & MODE
    # =================================================================

    calc_mode = st.radio(
        "**Calculation Goal:**",
        ["1. Calculate Shear Strength (Forward)", "2. Find Parameters from Lab Data (Back Analysis)"],
        horizontal=True
    )
    st.markdown("---")

    # =================================================================
    # 2. GLOBAL PARAMETERS (Generic)
    # =================================================================
    # We use generic 'c' and 'phi' variables so they work for BOTH
    # Drained (c', phi') and Undrained (Cu, phi_u) problems.
    
    global_params = {}
    
    col_g1, col_g2 = st.columns(2)
    
    if "1. Calculate" in calc_mode:
        with col_g1:
            # Generic label: Works for c' (effective) or Cu (undrained)
            c_val = st.number_input("Cohesion ($c$) [kPa]", value=10.0, step=1.0)
        with col_g2:
            # Generic label: Works for phi' (effective) or phi_u (undrained)
            phi_val = st.number_input("Friction Angle ($\phi$) [deg]", value=30.0, step=1.0)
        
        global_params = {"c": c_val, "phi": phi_val}
        
    else:
        with col_g1:
             st.info("Enter results from **2 Failure Tests** (e.g., Triaxial) to find $c$ and $\phi$.")
        # No globals for Mode 2, they are calculated results.

    # =================================================================
    # 3. LAYOUT: INPUTS (Left) - VISUALIZATION (Right)
    # =================================================================
    col_input, col_viz = st.columns([1.5, 1])

    test_data = []
    
    with col_input:
        st.subheader("Stress State Data")
        
        # Mode 1: User enters ONE state to check strength
        # Mode 2: User enters TWO states to find the line
        num_tests = 1 if "1. Calculate" in calc_mode else 2
        
        for i in range(num_tests):
            title = "State of Stress" if num_tests == 1 else f"Test Sample #{i+1} (Failure)"
            expanded_state = True
            
            with st.expander(title, expanded=expanded_state):
                c1, c2 = st.columns(2)
                
                # Inputs are generic "Minor" and "Major" stresses
                sig3 = c1.number_input(f"$\sigma_3$ (Confining) [kPa]", value=50.0 + (i*50), key=f"s3_{i}")
                
                if "1. Calculate" in calc_mode:
                    # In this mode, we calculate the max strength based on sig3
                    # But we also let the user enter a sig1 if they want to check a specific Mohr circle against the limit
                    sig1 = c2.number_input(f"$\sigma_1$ (Applied) [kPa]", value=120.0, key=f"s1_{i}", help="Enter the axial stress applied to the soil.")
                else:
                    # In back analysis, these are failure stresses from the lab
                    sig1 = c2.number_input(f"$\sigma_{{1f}}$ (Failure) [kPa]", value=150.0 + (i*150), key=f"s1f_{i}")

                # Calculate center and radius for visualization
                center = (sig1 + sig3) / 2
                radius = (sig1 - sig3) / 2
                
                test_data.append({
                    "id": i+1,
                    "sig3": sig3,
                    "sig1": sig1,
                    "center": center,
                    "radius": radius
                })

    # =================================================================
    # HELPER: CALCULATION ENGINE
    # =================================================================
    def calculate_strength_at_state(test, g_params):
        # Unpack
        s3 = test['sig3'] # Confining
        s1_applied = test['sig1'] # Actual applied
        c = g_params['c']
        phi = g_params['phi']
        
        # 1. Calculate Max Shear Strength on the failure plane
        # For a given Normal Stress on the failure plane, tau = c + sigma_n * tan(phi)
        
        # 2. More usefully for students: Calculate the Max Principal Stress (Sigma1) possible
        # This answers: "At confining pressure X, what axial load breaks the soil?"
        # Formula: sig1 = sig3 * tan^2(45 + phi/2) + 2*c*tan(45 + phi/2)
        
        tan_term = math.tan(math.radians(45 + phi/2))
        sig1_failure = (s3 * (tan_term**2)) + (2 * c * tan_term)
        
        # Max shear stress (radius of the failure circle)
        tau_max_possible = (sig1_failure - s3) / 2
        
        # Current shear stress applied (radius of current circle)
        tau_current = (s1_applied - s3) / 2
        
        # Safety Factor (Strength / Applied Stress)
        # We can compare the max possible sig1 to the applied sig1
        is_safe = s1_applied < sig1_failure
        
        math_log = [
            f"**1. Input Parameters:**",
            f"$c = {c}$ kPa, $\phi = {phi}^\circ$",
            f"Confining Stress $\sigma_3 = {s3}$ kPa",
            f"**2. Calculation (Mohr-Coulomb):**",
            f"The max axial stress $\sigma_1$ before failure is:",
            f"$\sigma_{{1,max}} = \sigma_3 \\tan^2(45+\phi/2) + 2c\\tan(45+\phi/2)$",
            f"$\sigma_{{1,max}} = {s3:.1f} ({tan_term:.2f})^2 + 2({c:.1f})({tan_term:.2f})$",
            f"$\\mathbf{{\sigma_{{1,max}} = {sig1_failure:.2f} \\text{{ kPa}}}}$"
        ]
        
        return {
            "status": "SAFE" if is_safe else "FAILURE",
            "sig1_failure": sig1_failure,
            "log": math_log
        }

    def solve_parameters(tests):
        # Solves for c and phi given two failure circles
        t1 = tests[0]
        t2 = tests[1]
        
        dy = t2['sig1'] - t1['sig1']
        dx = t2['sig3'] - t1['sig3']
        
        log = ["**Back Calculation Steps:**"]
        
        if dx == 0:
            return {"c": 0, "phi": 0, "log": ["Error: Confining pressures must be different."]}
            
        # Slope of the sig1 vs sig3 line
        m = dy / dx 
        
        # m = tan^2(45 + phi/2)
        if m < 1:
            phi_val = 0
            log.append("Slope < 1 (Physics error: Material cannot have negative friction).")
        else:
            # math.atan returns radians
            term = math.atan(math.sqrt(m)) 
            # term = 45 + phi/2 (in radians term, 45 deg is pi/4)
            # phi/2 = term - pi/4
            phi_rad = 2 * (term - (math.pi/4))
            phi_val = math.degrees(phi_rad)
        
        # Intercept b = sig1 - m*sig3
        # b = 2*c*sqrt(m)
        b = t1['sig1'] - (m * t1['sig3'])
        c_val = b / (2 * math.sqrt(m))
        
        log.append(f"1. Slope $m = ({t2['sig1']}-{t1['sig1']}) / ({t2['sig3']}-{t1['sig3']}) = {m:.3f}$")
        log.append(f"2. $\phi = 2(\\tan^{{-1}}(\\sqrt{{m}}) - 45^\circ) = {phi_val:.2f}^\circ$")
        log.append(f"3. $c = \\text{{Intercept}} / (2\\sqrt{{m}}) = {c_val:.2f}$ kPa")
        
        return {"c": c_val, "phi": phi_val, "log": log}

    # --- VISUALIZER ---
    with col_viz:
        st.subheader("Mohr Circle Diagram")
        fig, ax = plt.subplots(figsize=(6, 6))
        
        # Dynamic axis limits
        max_stress = max([t['sig1'] for t in test_data]) if test_data else 100
        limit = max_stress * 1.2
        ax.set_xlim(0, limit)
        ax.set_ylim(0, limit * 0.6) # Y axis (Shear) is usually smaller scale
        ax.set_aspect('equal')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.set_xlabel("Normal Stress $\sigma$ (kPa)")
        ax.set_ylabel("Shear Stress $\\tau$ (kPa)")
        
        # Draw Circles
        for t in test_data:
            # Draw top half of circle
            arc = patches.Arc((t['center'], 0), t['radius']*2, t['radius']*2, 
                              theta1=0, theta2=180, edgecolor='blue', linewidth=1.5)
            ax.add_patch(arc)
            # Mark the principal stresses
            ax.plot([t['sig3'], t['sig1']], [0, 0], 'bo', markersize=4)
        
        # Determine envelope parameters for plotting
        if "1. Calculate" in calc_mode:
            c_plot = global_params['c']
            phi_plot = global_params['phi']
            color = 'red'
        elif len(test_data) == 2:
            res = solve_parameters(test_data)
            c_plot = res['c']
            phi_plot = res['phi']
            color = 'green'
        else:
            c_plot, phi_plot = 0, 0
            color = 'gray'

        # Plot Failure Envelope Line
        if phi_plot >= 0:
            x_vals = np.array([0, limit])
            # y = c + x * tan(phi)
            y_vals = c_plot + x_vals * np.tan(math.radians(phi_plot))
            ax.plot(x_vals, y_vals, color=color, linewidth=2, linestyle='-', label='Failure Envelope')
            
            # Label the line
            label_x = limit * 0.5
            label_y = c_plot + label_x * np.tan(math.radians(phi_plot))
            ax.text(label_x, label_y + (limit*0.02), 
                    f"$\\tau = {c_plot:.1f} + \\sigma \\tan({phi_plot:.1f}^\\circ)$", 
                    color=color, fontsize=10, fontweight='bold')

        st.pyplot(fig)

    # =================================================================
    # 4. RESULTS SECTION
    # =================================================================

    # -------------------------------------------------------------
    # MODE 1: FORWARD CALCULATION
    # -------------------------------------------------------------
    if "1. Calculate" in calc_mode:
        if st.button("Calculate Strength", type="primary"):
            st.markdown("### Results")
            
            t = test_data[0]
            res = calculate_strength_at_state(t, global_params)
            
            c_res, c_log = st.columns([1, 1.2])
            
            with c_res:
                st.metric("Max Sustainable $\sigma_1$", f"{res['sig1_failure']:.2f} kPa")
                
                if res['status'] == "SAFE":
                    st.success("Current State: **STABLE**")
                    st.caption("Applied stress is less than strength.")
                else:
                    st.error("Current State: **FAILURE**")
                    st.caption("Applied stress exceeds soil strength.")

            with c_log:
                 with st.expander("Show Step-by-Step Calculation", expanded=True):
                     for line in res['log']:
                         st.write(line)

    # -------------------------------------------------------------
    # MODE 2: BACK ANALYSIS
    # -------------------------------------------------------------
    else:
        if st.button("Calculate Soil Parameters", type="primary"):
            st.markdown("### Results")
            
            if len(test_data) < 2:
                st.error("You need 2 tests to find the parameters.")
            else:
                res = solve_parameters(test_data)
                
                c_res, c_log = st.columns(2)
                
                with c_res:
                    st.metric("Cohesion ($c$)", f"{res['c']:.2f} kPa")
                    st.metric("Friction Angle ($\phi$)", f"{res['phi']:.2f} °")
                
                with c_log:
                    with st.expander("Show Derivation"):
                        for line in res['log']:
                             st.write(line)
                        st.latex(r"\text{Using } \sigma_1 = \sigma_3 \tan^2(45 + \phi/2) + 2c\tan(45 + \phi/2)")

if __name__ == "__main__":
    app()
