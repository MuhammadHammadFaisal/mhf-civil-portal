import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def app():
    st.header("🏗️ Multi-Layer Consolidation Analysis")
    st.markdown("""
    **Scope:** Calculate Ultimate Primary Settlement ($S_c$) and Time-Rate Settlement ($t$) for multi-layered soil profiles.
    """)
    st.markdown("---")

    # =================================================================
    # 1. GLOBAL PARAMETERS
    # =================================================================
    col_global1, col_global2 = st.columns(2)
    with col_global1:
        water_depth = st.number_input("Water Table Depth (m)", value=2.0, step=0.5, help="Depth from surface")
    with col_global2:
        surcharge_q = st.number_input("Surface Surcharge Δσ (kPa)", value=50.0, step=10.0, help="Applied foundation load (Wide Fill)")

    st.markdown("---")

    # =================================================================
    # 2. LAYER INPUTS
    # =================================================================
    col_input, col_viz = st.columns([1.2, 1])

    with col_input:
        st.subheader("A. Soil Stratigraphy")
        num_layers = st.number_input("Number of Layers", min_value=1, max_value=6, value=2)
        
        layers_data = []
        current_depth = 0.0

        for i in range(int(num_layers)):
            with st.expander(f"Layer {i+1} (Top: {current_depth:.1f}m)", expanded=True):
                # Geometry & Unit Weight
                c1, c2, c3 = st.columns(3)
                thickness = c1.number_input(f"Thickness (m)", value=4.0, key=f"h_{i}")
                gamma = c2.number_input(f"γ_sat (kN/m³)", value=19.0, key=f"g_{i}")
                soil_type = c3.selectbox("Type", ["Clay", "Sand"], key=f"type_{i}")
                
                mid_depth = current_depth + (thickness / 2)
                
                # Method Selection (Clay Only)
                method = "None (Sand)"
                params = {}
                
                if soil_type == "Clay":
                    st.markdown("##### Settlement Parameters")
                    method = st.radio(
                        "Calculation Method:",
                        ["Method A: Cc/Cr (Logarithmic)", "Method B: mv (Linear)", "Method C: Δe (Direct Void Ratio)"],
                        key=f"method_{i}"
                    )
                    
                    if "Method A" in method:
                        # Case 1/2 Logic (Preconsolidation)
                        rc1, rc2, rc3 = st.columns(3)
                        e0 = rc1.number_input("e₀", value=0.850, format="%.3f", key=f"e0_{i}")
                        Cc = rc2.number_input("Cc", value=0.320, format="%.3f", key=f"cc_{i}")
                        Cr = rc3.number_input("Cr", value=0.050, format="%.3f", key=f"cr_{i}")
                        sigma_p = st.number_input("Preconsolidation Stress σ'p (kPa)", value=100.0, key=f"sigp_{i}")
                        params = {"e0": e0, "Cc": Cc, "Cr": Cr, "sigma_p": sigma_p}
                        
                    elif "Method B" in method:
                        # mv method
                        mv = st.number_input("m_v (1/kPa)", value=0.0005, format="%.5f", key=f"mv_{i}")
                        params = {"mv": mv}
                        
                    elif "Method C" in method:
                        # Delta e method
                        rc1, rc2 = st.columns(2)
                        e0 = rc1.number_input("Initial e₀", value=0.9, key=f"e0_c_{i}")
                        e_final = rc2.number_input("Final e₁", value=0.82, key=f"ef_c_{i}")
                        params = {"e0": e0, "e_final": e_final}

                layers_data.append({
                    "id": i+1,
                    "type": soil_type,
                    "thickness": thickness,
                    "gamma": gamma,
                    "top": current_depth,
                    "bottom": current_depth + thickness,
                    "mid": mid_depth,
                    "method": method,
                    "params": params
                })
                current_depth += thickness

    # =================================================================
    # 3. DYNAMIC VISUALIZATION
    # =================================================================
    with col_viz:
        st.subheader("B. Profile Visualizer")
        fig, ax = plt.subplots(figsize=(6, 8))
        
        # Colors & Drawing
        colors = {"Clay": "#D7CCC8", "Sand": "#FFF9C4"}
        for l in layers_data:
            color = colors.get(l['type'], "grey")
            rect = patches.Rectangle((0, l['top']), 5, l['thickness'], facecolor=color, edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            ax.text(2.5, l['mid'], f"{l['type']}\n{l['thickness']}m", ha='center', va='center', fontsize=9, fontweight='bold')
            ax.text(-0.2, l['bottom'], f"{l['bottom']:.1f}m", ha='right', va='center', fontsize=8)

        # Water Table & Load
        ax.axhline(water_depth, color='blue', linestyle='--', linewidth=2)
        ax.text(5.1, water_depth, "▽ WT", color='blue', va='center')
        
        if surcharge_q > 0:
            for x in np.linspace(0.5, 4.5, 6):
                ax.arrow(x, -0.6, 0, 0.5, head_width=0.15, head_length=0.1, fc='red', ec='red')
            ax.text(2.5, -0.8, f"q = {surcharge_q} kPa", color='red', ha='center')

        ax.set_ylim(current_depth * 1.1, -1.5)
        ax.set_xlim(0, 5)
        ax.axis('off')
        st.pyplot(fig)

    # =================================================================
    # 4. SETTLEMENT CALCULATIONS
    # =================================================================
    st.markdown("---")
    if st.button("Calculate Results", type="primary"):
        st.subheader("C. Results Summary")
        
        total_settlement = 0.0
        
        for l in layers_data:
            # --- Effective Stress Calculation ---
            # 1. Weight above mid-point
            sigma_total = 0.0
            for above in layers_data:
                if above['id'] < l['id']:
                    sigma_total += above['thickness'] * above['gamma']
            
            # 2. Add half of self-weight
            sigma_total += (l['thickness']/2) * l['gamma']
            
            # 3. Pore pressure
            u = (l['mid'] - water_depth) * 9.81 if l['mid'] > water_depth else 0.0
            
            # 4. Effective Stresses
            sigma_0 = sigma_total - u
            sigma_f = sigma_0 + surcharge_q
            
            settlement = 0.0
            
            # --- Settlement Logic ---
            if l['type'] == "Clay":
                H = l['thickness']
                if "Method A" in l['method']:
                    p = l['params']
                    # NC Case
                    if sigma_0 >= p['sigma_p']: 
                        settlement = (p['Cc'] * H / (1 + p['e0'])) * np.log10(sigma_f / sigma_0)
                        status = "NC (Virgin Compression)"
                    # OC Case 1 (Recompression only)
                    elif sigma_f <= p['sigma_p']:
                        settlement = (p['Cr'] * H / (1 + p['e0'])) * np.log10(sigma_f / sigma_0)
                        status = "OC (Recompression)"
                    # OC Case 2 (Recompression + Virgin)
                    else:
                        term1 = (p['Cr'] * H / (1 + p['e0'])) * np.log10(p['sigma_p'] / sigma_0)
                        term2 = (p['Cc'] * H / (1 + p['e0'])) * np.log10(sigma_f / p['sigma_p'])
                        settlement = term1 + term2
                        status = "OC (Recomp. + Virgin)"
                        
                elif "Method B" in l['method']:
                    settlement = l['params']['mv'] * surcharge_q * H
                    status = "mv Method"
                    
                elif "Method C" in l['method']:
                    de = l['params']['e0'] - l['params']['e_final']
                    settlement = (de / (1 + l['params']['e0'])) * H
                    status = "Δe Method"
            else:
                status = "Sand (Skipped)"

            if settlement > 0:
                st.success(f"**Layer {l['id']} ({status}):** Settlement = {settlement*1000:.2f} mm")
                with st.expander(f"Layer {l['id']} Detailed Stress"):
                    st.write(f"$\sigma'_0$ (mid) = {sigma_0:.2f} kPa")
                    st.write(f"$\sigma'_f$ (mid) = {sigma_f:.2f} kPa")
            
            total_settlement += settlement

        st.metric("TOTAL PRIMARY SETTLEMENT", f"{total_settlement*1000:.2f} mm", f"{total_settlement:.4f} m")

        # =================================================================
        # 5. TIME RATE ANALYSIS (Restored!)
        # =================================================================
        st.markdown("---")
        st.subheader("D. Time Rate of Consolidation")
        st.info("Calculate how long settlement will take. Choose a critical clay layer for analysis.")
        
        c_time1, c_time2 = st.columns(2)
        with c_time1:
            # Inputs
            cv = st.number_input("Coefficient of Consolidation ($c_v$) [m²/year]", value=2.0)
            drainage_path = st.number_input("Drainage Path ($d$ or $H_{dr}$) [m]", value=2.0, help="Enter H for single drainage, H/2 for double.")
            
            calc_mode = st.radio("Calculate:", ["Time for X% Settlement", "Settlement at Time t"])
            
        with c_time2:
            if calc_mode == "Time for X% Settlement":
                U_target = st.slider("Target U%", 10, 95, 90)
                U_dec = U_target / 100.0
                
                # Tv Calculation [cite: 428-429]
                if U_dec <= 0.6:
                    Tv = (np.pi/4) * (U_dec**2)
                else:
                    Tv = -0.933 * np.log10(1 - U_dec) - 0.085
                
                if cv > 0:
                    t_req = (Tv * drainage_path**2) / cv
                    st.metric(f"Time for {U_target}% Settlement", f"{t_req:.2f} years")
                    st.latex(rf"T_v = {Tv:.3f} \rightarrow t = \frac{{T_v d^2}}{{c_v}}")
            
            else:
                t_input = st.number_input("Time (years)", value=1.0)
                if cv > 0:
                    Tv = (cv * t_input) / (drainage_path**2)
                    
                    # Inverse Tv (Approx)
                    if Tv < 0.283:
                        U_calc = np.sqrt((4*Tv)/np.pi)
                    else:
                        U_calc = 1 - 10**((Tv + 0.085)/-0.933)
                    
                    if U_calc > 1.0: U_calc = 1.0
                    
                    settlement_t = total_settlement * U_calc
                    st.metric(f"Settlement at {t_input} years", f"{settlement_t*1000:.2f} mm")
                    st.write(f"Degree of Consolidation $U = {U_calc*100:.1f}\%$")

if __name__ == "__main__":
    app()
