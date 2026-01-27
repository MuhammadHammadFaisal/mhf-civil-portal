import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def app():
    st.header("🏗️ Multi-Layer Consolidation Analysis")
    st.markdown("""
    **Scope:** Calculate Ultimate Primary Settlement ($S_c$) for multiple layers and analyze Time-Rate ($t$) for the critical clay layer.
    """)
    st.markdown("---")

    # =================================================================
    # 1. GLOBAL PARAMETERS
    # =================================================================
    col_global1, col_global2 = st.columns(2)
    with col_global1:
        water_depth = st.number_input("Water Table Depth (m)", value=2.0, step=0.5)
    with col_global2:
        surcharge_q = st.number_input("Surface Surcharge Δσ (kPa)", value=50.0, step=10.0)

    st.markdown("---")

    # =================================================================
    # 2. STRATIGRAPHY INPUTS
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
                        rc1, rc2, rc3 = st.columns(3)
                        e0 = rc1.number_input("e₀", value=0.850, format="%.3f", key=f"e0_{i}")
                        Cc = rc2.number_input("Cc", value=0.320, format="%.3f", key=f"cc_{i}")
                        Cr = rc3.number_input("Cr", value=0.050, format="%.3f", key=f"cr_{i}")
                        sigma_p = st.number_input("Preconsolidation Stress σ'p (kPa)", value=100.0, key=f"sigp_{i}")
                        params = {"e0": e0, "Cc": Cc, "Cr": Cr, "sigma_p": sigma_p}
                        
                    elif "Method B" in method:
                        mv = st.number_input("m_v (1/kPa)", value=0.0005, format="%.5f", key=f"mv_{i}")
                        params = {"mv": mv}
                        
                    elif "Method C" in method:
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
    # 3. TIME RATE PARAMETERS (Now Visible!)
    # =================================================================
    with col_input:
        st.markdown("---")
        st.subheader("B. Time Rate Parameters")
        st.info("Select the Critical Clay Layer to analyze for consolidation time.")
        
        # Filter only Clay layers for the dropdown
        clay_indices = [l['id'] for l in layers_data if l['type'] == "Clay"]
        
        if clay_indices:
            crit_layer_id = st.selectbox("Select Critical Layer", clay_indices)
            # Find selected layer data to get its thickness
            crit_layer = next((l for l in layers_data if l['id'] == crit_layer_id), None)
            
            ct1, ct2 = st.columns(2)
            cv = ct1.number_input("Coeff. of Consolidation ($c_v$) [m²/year]", value=2.0)
            
            # Smart drainage path default
            default_dr = crit_layer['thickness'] / 2 if crit_layer else 1.0
            drainage_path = ct2.number_input("Drainage Path ($d$ or $H_{dr}$) [m]", value=default_dr, help="Usually H/2 for double drainage")
            
            calc_mode = st.radio("Time Analysis Mode:", ["Calculate Time for X% Settlement", "Calculate Settlement at Time t"])
            
            if calc_mode == "Calculate Time for X% Settlement":
                U_target = st.slider("Target Degree of Consolidation (U%)", 10, 99, 90)
                t_user = None
            else:
                t_user = st.number_input("Time Elapsed (years)", value=1.0)
                U_target = None
        else:
            st.warning("Add a Clay layer to enable Time Rate analysis.")
            crit_layer = None

    # =================================================================
    # 4. VISUALIZATION
    # =================================================================
    with col_viz:
        st.subheader("Soil Profile")
        fig, ax = plt.subplots(figsize=(6, 8))
        colors = {"Clay": "#D7CCC8", "Sand": "#FFF9C4"}
        
        for l in layers_data:
            color = colors.get(l['type'], "grey")
            rect = patches.Rectangle((0, l['top']), 5, l['thickness'], facecolor=color, edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            ax.text(2.5, l['mid'], f"Layer {l['id']}: {l['type']}\n{l['thickness']}m", ha='center', va='center', fontsize=9, fontweight='bold')
            ax.text(-0.2, l['bottom'], f"{l['bottom']:.1f}m", ha='right', va='center', fontsize=8)

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
    # 5. CALCULATION & RESULTS
    # =================================================================
    st.markdown("---")
    if st.button("Calculate Results", type="primary"):
        st.header("📊 Results")
        
        # --- Part 1: Total Settlement ---
        total_settlement = 0.0
        
        st.subheader("1. Ultimate Primary Settlement")
        
        for l in layers_data:
            # Effective Stress Calcs
            sigma_total = 0.0
            for above in layers_data:
                if above['id'] < l['id']:
                    sigma_total += above['thickness'] * above['gamma']
            sigma_total += (l['thickness']/2) * l['gamma']
            
            u = (l['mid'] - water_depth) * 9.81 if l['mid'] > water_depth else 0.0
            sigma_0 = sigma_total - u
            sigma_f = sigma_0 + surcharge_q
            
            settlement = 0.0
            status = "Skipped"
            
            if l['type'] == "Clay":
                H = l['thickness']
                if "Method A" in l['method']:
                    p = l['params']
                    if sigma_0 >= p['sigma_p']: 
                        settlement = (p['Cc'] * H / (1 + p['e0'])) * np.log10(sigma_f / sigma_0)
                        status = "NC"
                    elif sigma_f <= p['sigma_p']:
                        settlement = (p['Cr'] * H / (1 + p['e0'])) * np.log10(sigma_f / sigma_0)
                        status = "OC (Recomp)"
                    else:
                        term1 = (p['Cr'] * H / (1 + p['e0'])) * np.log10(p['sigma_p'] / sigma_0)
                        term2 = (p['Cc'] * H / (1 + p['e0'])) * np.log10(sigma_f / p['sigma_p'])
                        settlement = term1 + term2
                        status = "OC (Mixed)"
                elif "Method B" in l['method']:
                    settlement = l['params']['mv'] * surcharge_q * H
                    status = "mv Method"
                elif "Method C" in l['method']:
                    de = l['params']['e0'] - l['params']['e_final']
                    settlement = (de / (1 + l['params']['e0'])) * H
                    status = "Δe Method"

            if settlement > 0:
                st.write(f"**Layer {l['id']} ({status}):** {settlement*1000:.2f} mm")
            
            total_settlement += settlement

        st.success(f"**TOTAL SETTLEMENT ($S_{{total}}$): {total_settlement*1000:.2f} mm**")

        # --- Part 2: Time Rate Analysis ---
        if crit_layer:
            st.subheader(f"2. Time Rate Analysis (Critical Layer {crit_layer_id})")
            
            # We are analyzing specifically the settlement of the chosen critical layer for time
            # But usually, Total Settlement U% applies to the whole if layers are similar.
            # Here we provide the time for the chosen layer.
            
            if calc_mode == "Calculate Time for X% Settlement":
                U_dec = U_target / 100.0
                if U_dec <= 0.6:
                    Tv = (np.pi/4) * (U_dec**2)
                else:
                    Tv = -0.933 * np.log10(1 - U_dec) - 0.085
                
                if cv > 0:
                    t_req = (Tv * drainage_path**2) / cv
                    st.metric(f"Time for {U_target}% Consolidation", f"{t_req:.2f} years")
                    st.latex(rf"T_v = {Tv:.3f} \rightarrow t = \frac{{T_v d^2}}{{c_v}}")
                else:
                    st.error("Cv must be > 0")

            else: # Calculate Settlement at Time t
                if cv > 0:
                    Tv = (cv * t_user) / (drainage_path**2)
                    
                    if Tv < 0.283:
                        U_calc = np.sqrt((4*Tv)/np.pi)
                    else:
                        U_calc = 1 - 10**((Tv + 0.085)/-0.933)
                    
                    if U_calc > 1.0: U_calc = 1.0
                    
                    # Apply this U% to the TOTAL settlement (Simplification for user utility)
                    settlement_t = total_settlement * U_calc
                    
                    c_res1, c_res2 = st.columns(2)
                    c_res1.metric(f"Degree of Consolidation ($U$)", f"{U_calc*100:.1f} %")
                    c_res2.metric(f"Settlement at {t_user} years", f"{settlement_t*1000:.2f} mm")
                else:
                    st.error("Cv must be > 0")

if __name__ == "__main__":
    app()
