import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def app():
    st.header("🏗️ Multi-Layer Consolidation Analysis")
    st.markdown("""
    Define the soil stratigraphy and water table. For each clay layer, select the specific laboratory method 
    available ($C_c/C_r$, $m_v$, or $\Delta e$) to calculate total settlement.
    """)
    st.markdown("---")

    # =================================================================
    # 1. GLOBAL PARAMETERS (Water Table & Surcharge)
    # =================================================================
    col_global1, col_global2 = st.columns(2)
    with col_global1:
        water_depth = st.number_input("Water Table Depth (m)", value=2.0, step=0.5, help="Depth from surface")
    with col_global2:
        surcharge_q = st.number_input("Surface Surcharge Δσ (kPa)", value=50.0, step=10.0, help="Applied foundation load")

    st.markdown("---")

    # =================================================================
    # 2. LAYER INPUTS (Dynamic)
    # =================================================================
    col_input, col_viz = st.columns([1.2, 1])

    with col_input:
        st.subheader("Soil Stratigraphy")
        num_layers = st.number_input("Number of Layers", min_value=1, max_value=6, value=2)
        
        layers_data = []
        current_depth = 0.0

        for i in range(int(num_layers)):
            with st.expander(f"Layer {i+1} (Top: {current_depth:.1f}m)", expanded=True):
                # --- Basic Geometry & Weight ---
                c1, c2, c3 = st.columns(3)
                thickness = c1.number_input(f"Thickness (m)", value=4.0, key=f"h_{i}")
                gamma = c2.number_input(f"γ_sat (kN/m³)", value=19.0, key=f"g_{i}")
                soil_type = c3.selectbox("Type", ["Clay", "Sand"], key=f"type_{i}")
                
                mid_depth = current_depth + (thickness / 2)
                
                # --- Settlement Method Selection (Only for Clay) ---
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
                        # Cc/Cr Inputs
                        rc1, rc2, rc3 = st.columns(3)
                        e0 = rc1.number_input("e₀", value=0.8, key=f"e0_{i}")
                        Cc = rc2.number_input("Cc", value=0.3, key=f"cc_{i}")
                        Cr = rc3.number_input("Cr", value=0.05, key=f"cr_{i}")
                        sigma_p = st.number_input("Preconsolidation Stress σ'p (kPa)", value=100.0, key=f"sigp_{i}")
                        params = {"e0": e0, "Cc": Cc, "Cr": Cr, "sigma_p": sigma_p}
                        
                    elif "Method B" in method:
                        # mv Inputs
                        mv = st.number_input("Coeff. Volume Compressibility m_v (1/kPa or m²/kN)", value=0.0005, format="%.5f", key=f"mv_{i}")
                        params = {"mv": mv}
                        
                    elif "Method C" in method:
                        # Delta e Inputs
                        rc1, rc2 = st.columns(2)
                        e0 = rc1.number_input("Initial e₀", value=0.9, key=f"e0_c_{i}")
                        e_final = rc2.number_input("Final e₁", value=0.82, key=f"ef_c_{i}")
                        params = {"e0": e0, "e_final": e_final}

                # Store Layer Data
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
        st.subheader("Soil Profile")
        fig, ax = plt.subplots(figsize=(6, 8))
        
        # Colors
        colors = {"Clay": "#B0A494", "Sand": "#E6D690"}
        
        # Draw Layers
        for l in layers_data:
            color = colors.get(l['type'], "grey")
            rect = patches.Rectangle((0, l['top']), 5, l['thickness'], facecolor=color, edgecolor='black', linewidth=1)
            ax.add_patch(rect)
            
            # Label Layer
            mid_y = l['mid']
            ax.text(2.5, mid_y, f"{l['type']}\nH={l['thickness']}m", ha='center', va='center', fontweight='bold', fontsize=9)
            
            # Label Depth on Left
            ax.text(-0.2, l['bottom'], f"{l['bottom']:.1f}m", ha='right', va='center', fontsize=8)

        # Draw Water Table
        ax.axhline(water_depth, color='blue', linestyle='--', linewidth=2)
        ax.text(5.1, water_depth, "▽ WT", color='blue', va='center', fontweight='bold')
        
        # Draw Surcharge Arrow
        if surcharge_q > 0:
            for x in np.linspace(0.5, 4.5, 6):
                ax.arrow(x, -0.5, 0, 0.5, head_width=0.15, head_length=0.1, fc='red', ec='red')
            ax.text(2.5, -0.7, f"q = {surcharge_q} kPa", color='red', ha='center')

        # Formatting
        ax.set_ylim(current_depth * 1.1, -1.5) # Invert Y axis
        ax.set_xlim(0, 5)
        ax.set_xticks([])
        ax.set_ylabel("Depth (m)")
        ax.set_title("Stratigraphy & Input Parameters")
        
        st.pyplot(fig)

    # =================================================================
    # 4. CALCULATION LOGIC
    # =================================================================
    st.markdown("---")
    if st.button("Calculate Total Settlement", type="primary"):
        
        total_settlement = 0.0
        
        # Loop through layers to calculate stress and settlement
        
        for l in layers_data:
            st.markdown(f"### 🧮 Layer {l['id']} Analysis ({l['type']})")
            
            # --- A. Effective Stress Calculation ---
            # 1. Calculate Sigma_v0 (Total Stress) at mid-height
            # Weight of layers above
            weight_above = 0.0
            for above_l in layers_data:
                if above_l['id'] < l['id']:
                    weight_above += above_l['thickness'] * above_l['gamma']
            
            # Weight of half current layer
            weight_self = (l['thickness'] / 2) * l['gamma']
            sigma_total_mid = weight_above + weight_self
            
            # 2. Calculate Pore Pressure at mid-height
            if l['mid'] > water_depth:
                u_mid = (l['mid'] - water_depth) * 9.81
            else:
                u_mid = 0.0
            
            # 3. Effective Stress
            sigma_eff_0 = sigma_total_mid - u_mid
            
            # 4. Final Stress (Initial + Surcharge)
            # Assumption: Surcharge is constant with depth (1D loading)
            sigma_eff_final = sigma_eff_0 + surcharge_q
            
            # Display Stress State
            c_stress1, c_stress2, c_stress3 = st.columns(3)
            c_stress1.metric("Mid-Depth", f"{l['mid']:.2f} m")
            c_stress2.metric("Initial σ'₀", f"{sigma_eff_0:.2f} kPa")
            c_stress3.metric("Final σ'₁", f"{sigma_eff_final:.2f} kPa", delta=f"+{surcharge_q} kPa")

            # --- B. Settlement Calculation ---
            settlement_layer = 0.0
            
            if l['type'] == "Sand":
                st.info("Immediate settlement of sand is typically calculated using Elastic methods, not Consolidation. Skipped.")
                settlement_layer = 0.0
            else:
                H = l['thickness']
                
                # METHOD A: Cc / Cr
                if "Method A" in l['method']:
                    Cc = l['params']['Cc']
                    Cr = l['params']['Cr']
                    e0 = l['params']['e0']
                    sig_p = l['params']['sigma_p']
                    
                    # Logic Check (NC vs OC)
                    if sigma_eff_0 >= sig_p: # NC
                        formula = r"S_c = \frac{C_c H}{1+e_0} \log \left( \frac{\sigma'_f}{\sigma'_0} \right)"
                        settlement_layer = (Cc * H / (1 + e0)) * np.log10(sigma_eff_final / sigma_eff_0)
                        case_str = "Normally Consolidated (NC)"
                    elif sigma_eff_final < sig_p: # OC Case 1
                        formula = r"S_c = \frac{C_r H}{1+e_0} \log \left( \frac{\sigma'_f}{\sigma'_0} \right)"
                        settlement_layer = (Cr * H / (1 + e0)) * np.log10(sigma_eff_final / sigma_eff_0)
                        case_str = "OC (Recompression Only)"
                    else: # OC Case 2
                        formula = r"S_c = \frac{C_r H}{1+e_0} \log \left( \frac{\sigma'_p}{\sigma'_0} \right) + \frac{C_c H}{1+e_0} \log \left( \frac{\sigma'_f}{\sigma'_p} \right)"
                        term1 = (Cr * H / (1 + e0)) * np.log10(sig_p / sigma_eff_0)
                        term2 = (Cc * H / (1 + e0)) * np.log10(sigma_eff_final / sig_p)
                        settlement_layer = term1 + term2
                        case_str = "OC (Recompression + Compression)"

                    st.latex(formula)
                    st.caption(f"Case: {case_str}")

                # METHOD B: mv
                elif "Method B" in l['method']:
                    mv = l['params']['mv']
                    formula = r"S_c = m_v \cdot \Delta\sigma \cdot H"
                    settlement_layer = mv * surcharge_q * H
                    st.latex(formula)
                    st.caption(f"Using Linear Compressibility coefficient")

                # METHOD C: Delta e
                elif "Method C" in l['method']:
                    e0 = l['params']['e0']
                    ef = l['params']['e_final']
                    delta_e = e0 - ef
                    formula = r"S_c = \frac{\Delta e}{1+e_0} \cdot H"
                    settlement_layer = (delta_e / (1 + e0)) * H
                    st.latex(formula)
                    st.caption(f"Using direct void ratio change (Δe = {delta_e:.3f})")

            # Display Result for Layer
            st.success(f"Layer {l['id']} Settlement: **{settlement_layer*1000:.2f} mm**")
            total_settlement += settlement_layer
            st.markdown("---")

        # --- Final Total ---
        st.metric("TOTAL CONSOLIDATION SETTLEMENT", f"{total_settlement*1000:.2f} mm", f"{total_settlement:.4f} m")

if __name__ == "__main__":
    app()
