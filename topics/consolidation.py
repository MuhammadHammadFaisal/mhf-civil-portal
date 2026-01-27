import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def app():
    st.header("Consolidation Analysis")
    st.markdown("Select your calculation goal below. The input fields will adjust based on your choice.")
    st.markdown("---")

    # =================================================================
    # 1. MODE SELECTION
    # =================================================================
    calc_mode = st.radio(
        "**What do you want to calculate?**",
        ["1. Final Ultimate Settlement (S_final)", "2. Average Degree of Consolidation (U_av) & Time Rate"],
        horizontal=True
    )
    st.markdown("---")

    # =================================================================
    # 2. GLOBAL PARAMETERS (Always needed)
    # =================================================================
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        water_depth = st.number_input("Water Table Depth (m)", value=2.0, step=0.5)
    with col_g2:
        surcharge_q = st.number_input("Surface Surcharge Δσ (kPa)", value=50.0, step=10.0)

    # =================================================================
    # 3. LAYER INPUTS (Common for both, but simplified if needed)
    # =================================================================
    st.subheader("Soil Stratigraphy")
    num_layers = st.number_input("Number of Layers", 1, 6, 2)
    
    layers_data = []
    current_depth = 0.0

    for i in range(int(num_layers)):
        with st.expander(f"Layer {i+1} (Top: {current_depth:.1f}m)", expanded=True):
            c1, c2, c3 = st.columns(3)
            thickness = c1.number_input(f"Thickness (m)", value=4.0, key=f"h_{i}")
            gamma = c2.number_input(f"γ_sat (kN/m³)", value=19.0, key=f"g_{i}")
            soil_type = c3.selectbox("Type", ["Clay", "Sand"], key=f"type_{i}")
            
            mid_depth = current_depth + (thickness / 2)
            method = "None"
            params = {}
            
            # Settlement parameters are needed for BOTH modes (to get S_final)
            if soil_type == "Clay":
                st.caption("Settlement Parameters")
                method = st.radio(
                    f"Method for Layer {i+1}:",
                    ["Method A: Cc/Cr", "Method B: mv", "Method C: Δe"],
                    key=f"m_{i}", horizontal=True
                )
                
                if "Method A" in method:
                    rc1, rc2, rc3 = st.columns(3)
                    e0 = rc1.number_input("e₀", 0.85, key=f"e0_{i}")
                    Cc = rc2.number_input("Cc", 0.32, key=f"cc_{i}")
                    Cr = rc3.number_input("Cr", 0.05, key=f"cr_{i}")
                    sig_p = st.number_input("σ'p (kPa)", 100.0, key=f"sp_{i}")
                    params = {"e0": e0, "Cc": Cc, "Cr": Cr, "sigma_p": sig_p}
                elif "Method B" in method:
                    mv = st.number_input("m_v (1/kPa)", 0.0005, format="%.5f", key=f"mv_{i}")
                    params = {"mv": mv}
                elif "Method C" in method:
                    rc1, rc2 = st.columns(2)
                    e0 = rc1.number_input("e₀", 0.9, key=f"e0c_{i}")
                    ef = rc2.number_input("e_final", 0.82, key=f"efc_{i}")
                    params = {"e0": e0, "e_final": ef}
            
            layers_data.append({
                "id": i+1, "type": soil_type, "thickness": thickness, "gamma": gamma,
                "top": current_depth, "bottom": current_depth+thickness, "mid": mid_depth,
                "method": method, "params": params
            })
            current_depth += thickness

    # =================================================================
    # 4. MODE SPECIFIC INPUTS & LOGIC
    # =================================================================
    
    # -------------------------------------------------------------
    # MODE 1: FINAL SETTLEMENT ONLY
    # -------------------------------------------------------------
    if "1. Final" in calc_mode:
        if st.button("Calculate S_final", type="primary"):
            st.markdown("### Results: Final Settlement")
            
            total_settlement = 0.0
            
            for l in layers_data:
                # --- Stress Calc ---
                sigma_tot = sum([lx['thickness']*lx['gamma'] for lx in layers_data if lx['id'] < l['id']])
                sigma_tot += (l['thickness']/2) * l['gamma']
                u = (l['mid'] - water_depth)*9.81 if l['mid'] > water_depth else 0.0
                sig_0 = sigma_tot - u
                sig_f = sig_0 + surcharge_q
                
                # --- Settlement Calc ---
                settlement = 0.0
                status = "Skipped"
                
                if l['type'] == "Clay":
                    H = l['thickness']
                    if "Method A" in l['method']:
                        p = l['params']
                        if sig_0 >= p['sigma_p']:
                            settlement = (p['Cc']*H/(1+p['e0'])) * np.log10(sig_f/sig_0)
                            status = "NC"
                        elif sig_f <= p['sigma_p']:
                            settlement = (p['Cr']*H/(1+p['e0'])) * np.log10(sig_f/sig_0)
                            status = "OC (Recomp)"
                        else:
                            s1 = (p['Cr']*H/(1+p['e0'])) * np.log10(p['sigma_p']/sig_0)
                            s2 = (p['Cc']*H/(1+p['e0'])) * np.log10(sig_f/p['sigma_p'])
                            settlement = s1 + s2
                            status = "OC (Mixed)"
                    elif "Method B" in l['method']:
                        settlement = l['params']['mv'] * surcharge_q * H
                        status = "mv"
                    elif "Method C" in l['method']:
                        de = l['params']['e0'] - l['params']['e_final']
                        settlement = (de/(1+l['params']['e0'])) * H
                        status = "Δe"
                
                if settlement > 0:
                    st.success(f"**Layer {l['id']} ({status}):** {settlement*1000:.2f} mm")
                total_settlement += settlement
                
            st.metric("TOTAL S_final", f"{total_settlement*1000:.2f} mm", help=f"{total_settlement:.4f} m")

    # -------------------------------------------------------------
    # MODE 2: AVERAGE DEGREE (U_av) & TIME
    # -------------------------------------------------------------
    else:
        st.markdown("---")
        st.subheader("Time Rate Parameters")
        
        # Identify Critical Layer
        clay_layers = [l for l in layers_data if l['type'] == "Clay"]
        
        if not clay_layers:
            st.error("You need at least one Clay layer to calculate Consolidation Time.")
        else:
            # Select Critical Layer
            clay_opts = [f"Layer {l['id']}" for l in clay_layers]
            crit_choice = st.selectbox("Select Critical Clay Layer", clay_opts)
            crit_layer = next(l for l in clay_layers if f"Layer {l['id']}" == crit_choice)
            
            c_t1, c_t2 = st.columns(2)
            cv = c_t1.number_input("Coeff. of Consolidation ($c_v$) [m²/year]", value=2.0)
            dr_path = c_t2.number_input("Drainage Path ($d$ or $H_{dr}$) [m]", value=crit_layer['thickness']/2)
            
            # Sub-Choice: Find Time OR Find Settlement
            time_goal = st.radio("Goal:", ["Find Time (t) for specific U%", "Find Settlement (S_t) at specific Time (t)"])
            
            if st.button("Calculate Time Rate", type="primary"):
                
                # 1. First, Calculate S_final (Hidden Step)
                total_s_final = 0.0
                for l in layers_data:
                    # (Simplified Stress Calc for speed)
                    sigma_tot = sum([lx['thickness']*lx['gamma'] for lx in layers_data if lx['id'] < l['id']])
                    sigma_tot += (l['thickness']/2) * l['gamma']
                    u = (l['mid'] - water_depth)*9.81 if l['mid'] > water_depth else 0.0
                    sig_0 = sigma_tot - u
                    sig_f = sig_0 + surcharge_q
                    
                    s_l = 0.0
                    if l['type'] == "Clay":
                        H = l['thickness']
                        if "Method A" in l['method']:
                            p = l['params']
                            if sig_0 >= p['sigma_p']: s_l = (p['Cc']*H/(1+p['e0'])) * np.log10(sig_f/sig_0)
                            elif sig_f <= p['sigma_p']: s_l = (p['Cr']*H/(1+p['e0'])) * np.log10(sig_f/sig_0)
                            else: s_l = (p['Cr']*H/(1+p['e0']))*np.log10(p['sigma_p']/sig_0) + (p['Cc']*H/(1+p['e0']))*np.log10(sig_f/p['sigma_p'])
                        elif "Method B" in l['method']: s_l = l['params']['mv'] * surcharge_q * H
                        elif "Method C" in l['method']: s_l = ((l['params']['e0']-l['params']['e_final'])/(1+l['params']['e0'])) * H
                    total_s_final += s_l

                st.info(f"**Step 1:** Calculated Total $S_{{final}} = {total_s_final*1000:.2f}$ mm")
                
                # 2. Perform Time Calculation
                if time_goal == "Find Time (t) for specific U%":
                    # Logic: User gives U -> We find Tv -> We find t
                    U_target = st.slider("Target U%", 0, 100, 90) # Slider is safer
                    U_dec = U_target / 100.0
                    
                    # Equations from your Handout [cite: 660, 672]
                    # Note: We need Inverse relations for U -> Tv
                    # Approx inverse for U < 60% (Tv < 0.283) is Tv = (pi/4) * U^2
                    # Approx inverse for U > 60% is Tv = -0.933 * log(1-U) - 0.085
                    
                    if U_dec <= 0.6:
                        Tv = (np.pi/4) * (U_dec**2)
                    else:
                        Tv = -0.933 * np.log10(1 - U_dec) - 0.085
                        
                    if cv > 0:
                        t_req = (Tv * dr_path**2) / cv
                        st.success(f"**Time required: {t_req:.2f} years**")
                        st.latex(rf"T_v = {Tv:.4f} \quad (\text{{from }} U_{{av}}={U_target}\%)")
                        st.latex(rf"t = \frac{{T_v d^2}}{{c_v}} = \frac{{{Tv:.4f} \cdot {dr_path}^2}}{{{cv}}} = {t_req:.2f} \text{{ years}}")

                else:
                    # Logic: User gives t -> We find Tv -> We find U -> We find St
                    t_val = st.number_input("Time (years)", 1.0)
                    
                    if cv > 0:
                        Tv = (cv * t_val) / (dr_path**2)
                        
                        # Exact Equations from Handout 
                        if Tv <= 0.28: # Approx boundary for U=60%
                            U_calc = 2 * np.sqrt(Tv / np.pi)
                            eq_label = r"U_{av} = 2\sqrt{T_v / \pi}"
                        else:
                            # 1 - 10^stuff
                            exponent = -(Tv + 0.085) / 0.933
                            U_calc = 1 - (10 ** exponent)
                            eq_label = r"U_{av} = 1 - 10^{-\frac{T_v + 0.085}{0.933}}"
                        
                        if U_calc > 1.0: U_calc = 1.0
                        
                        s_t = total_s_final * U_calc
                        
                        st.success(f"**Settlement at {t_val} years: {s_t*1000:.2f} mm**")
                        st.latex(rf"T_v = \frac{{c_v t}}{{d^2}} = {Tv:.4f}")
                        st.write(f"Using Handout Equation for $T_v {'le' if Tv<=0.28 else '>'} 0.28$:")
                        st.latex(eq_label)
                        st.metric("Average Degree of Consolidation (U_av)", f"{U_calc*100:.1f} %")

if __name__ == "__main__":
    app()
