import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def app():

    # =================================================================
    # 1. MODE SELECTION
    # =================================================================
    calc_mode = st.radio(
        "**What do you want to calculate?**",
        ["1. Final Ultimate Settlement ($S_{final}$)", "2. Average Degree of Consolidation ($U_{av}$) & Time Rate"],
        horizontal=True
    )
    st.markdown("---")

    # =================================================================
    # 2. GLOBAL PARAMETERS
    # =================================================================
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        water_depth = st.number_input("Water Table Depth [m]", value=2.0, step=0.5)
    with col_g2:
        surcharge_q = st.number_input("Surface Surcharge $\Delta\sigma$ [kPa]", value=50.0, step=10.0)

    # =================================================================
    # 3. SPLIT LAYOUT
    # =================================================================
    col_input, col_viz = st.columns([1.2, 1])

    layers_data = []
    
    with col_input:
        st.subheader("Soil Stratigraphy")
        num_layers = st.number_input("Number of Layers", 1, 6, 2)
        
        current_depth = 0.0

        for i in range(int(num_layers)):
            with st.expander(f"Layer {i+1} (Top: {current_depth:.1f}m)", expanded=True):
                c1, c2, c3 = st.columns(3)
                thickness = c1.number_input(f"Thickness [m]", value=4.0, key=f"h_{i}")
                gamma = c2.number_input(f"$\gamma_{{sat}}$ [kN/m³]", value=19.0, key=f"g_{i}")
                soil_type = c3.selectbox("Type", ["Clay", "Sand"], key=f"type_{i}")
                
                mid_depth = current_depth + (thickness / 2)
                method = "None"
                params = {}
                
                if soil_type == "Clay":
                    st.caption("Settlement Parameters")
                    method = st.radio(
                        f"Method for Layer {i+1}:",
                        ["Method A: Cc/Cr", "Method B: mv", "Method C: Δe"],
                        key=f"m_{i}", horizontal=True
                    )
                    
                    if "Method A" in method:
                        rc1, rc2, rc3 = st.columns(3)
                        e0 = rc1.number_input("Initial $e_0$", 0.85, key=f"e0_{i}")
                        Cc = rc2.number_input("Index $C_c$", 0.32, key=f"cc_{i}")
                        Cr = rc3.number_input("Index $C_r$", 0.05, key=f"cr_{i}")
                        sig_p = st.number_input("Precons. $\sigma'_p$ [kPa]", 100.0, key=f"sp_{i}")
                        params = {"e0": e0, "Cc": Cc, "Cr": Cr, "sigma_p": sig_p}
                    elif "Method B" in method:
                        mv = st.number_input("Coeff. $m_v$ [1/kPa]", 0.0005, format="%.5f", key=f"mv_{i}")
                        params = {"mv": mv}
                    elif "Method C" in method:
                        rc1, rc2 = st.columns(2)
                        e0 = rc1.number_input("Initial $e_0$", 0.9, key=f"e0c_{i}")
                        ef = rc2.number_input("Final $e_{final}$", 0.82, key=f"efc_{i}")
                        params = {"e0": e0, "e_final": ef}
                
                layers_data.append({
                    "id": i+1, "type": soil_type, "thickness": thickness, "gamma": gamma,
                    "top": current_depth, "bottom": current_depth+thickness, "mid": mid_depth,
                    "method": method, "params": params
                })
                current_depth += thickness

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

        max_depth = max(current_depth * 1.1, 5.0) 
        ax.set_ylim(max_depth, -1.5)
        ax.set_xlim(0, 5)
        ax.axis('off')
        st.pyplot(fig)

    # =================================================================
    # HELPER: DETAILED CALCULATION ENGINE
    # =================================================================
    def calculate_layer(l, all_layers, w_depth, q_surf):
        # 1. Stress Calculation
        sigma_str = []
        sigma_val = 0.0
        
        # Stress from layers above
        for above in all_layers:
            if above['id'] < l['id']:
                sigma_str.append(f"({above['thickness']}m × {above['gamma']})")
                sigma_val += above['thickness'] * above['gamma']
        
        # Stress from self (mid-point)
        sigma_str.append(f"({l['thickness']/2}m × {l['gamma']})")
        sigma_val += (l['thickness']/2) * l['gamma']
        
        # Pore Pressure
        u_val = (l['mid'] - w_depth) * 9.81 if l['mid'] > w_depth else 0.0
        if l['mid'] > w_depth:
            u_str = f"({l['mid']}m - {w_depth}m) × 9.81 = {u_val:.2f} kPa"
        else:
            u_str = "0 kPa (Above WT)"
            
        sig_0 = sigma_val - u_val
        sig_f = sig_0 + q_surf
        
        # Math Log String
        math_log = [
            "**1. Effective Stress Calculation:**",
            f"$\sigma_{{total}} = {' + '.join(sigma_str)} = {sigma_val:.2f}$ kPa",
            f"$u = {u_str}$",
            f"$\sigma'_0 = {sigma_val:.2f} - {u_val:.2f} = \\mathbf{{{sig_0:.2f} \\text{{ kPa}}}}$",
            f"$\sigma'_f = {sig_0:.2f} + {q_surf} = \\mathbf{{{sig_f:.2f} \\text{{ kPa}}}}$"
        ]

        # 2. Settlement Calculation
        settlement = 0.0
        status = "Skipped"
        
        if l['type'] == "Clay":
            H = l['thickness']
            math_log.append("**2. Settlement Formula:**")
            
            if "Method A" in l['method']:
                p = l['params']
                math_log.append(f"Parameters: $C_c={p['Cc']}, C_r={p['Cr']}, e_0={p['e0']}, \sigma'_p={p['sigma_p']}$")
                
                if sig_0 >= p['sigma_p']: 
                    status = "NC"
                    settlement = (p['Cc']*H/(1+p['e0'])) * np.log10(sig_f/sig_0)
                    math_log.append(f"Case: NC ($\sigma'_0 \ge \sigma'_p$)")
                    math_log.append(f"$S = \\frac{{{p['Cc']} \cdot {H}}}{{1+{p['e0']}}} \log\\left(\\frac{{{sig_f:.1f}}}{{{sig_0:.1f}}}\\right)$")
                
                elif sig_f <= p['sigma_p']:
                    status = "OC (Recomp)"
                    settlement = (p['Cr']*H/(1+p['e0'])) * np.log10(sig_f/sig_0)
                    math_log.append(f"Case: OC Recompression ($\sigma'_f \le \sigma'_p$)")
                    math_log.append(f"$S = \\frac{{{p['Cr']} \cdot {H}}}{{1+{p['e0']}}} \log\\left(\\frac{{{sig_f:.1f}}}{{{sig_0:.1f}}}\\right)$")
                
                else:
                    status = "OC (Mixed)"
                    s1 = (p['Cr']*H/(1+p['e0'])) * np.log10(p['sigma_p']/sig_0)
                    s2 = (p['Cc']*H/(1+p['e0'])) * np.log10(sig_f/p['sigma_p'])
                    settlement = s1 + s2
                    math_log.append(f"Case: OC Mixed ($\sigma'_0 < \sigma'_p < \sigma'_f$)")
                    math_log.append(f"$S_1 = \\frac{{{p['Cr']} \cdot {H}}}{{1+{p['e0']}}} \log\\left(\\frac{{{p['sigma_p']}}}{{{sig_0:.1f}}}\\right)$")
                    math_log.append(f"$S_2 = \\frac{{{p['Cc']} \cdot {H}}}{{1+{p['e0']}}} \log\\left(\\frac{{{sig_f:.1f}}}{{{p['sigma_p']}}}\\right)$")
                    math_log.append(f"$S = S_1 + S_2$")
            
            elif "Method B" in l['method']:
                status = "mv"
                settlement = l['params']['mv'] * q_surf * H
                math_log.append(f"$S = m_v \cdot \Delta\sigma \cdot H = {l['params']['mv']} \cdot {q_surf} \cdot {H}$")
            
            elif "Method C" in l['method']:
                status = "Δe"
                de = l['params']['e0'] - l['params']['e_final']
                settlement = (de/(1+l['params']['e0'])) * H
                math_log.append(f"$S = \\frac{{\Delta e}}{{1+e_0}} \cdot H = \\frac{{{de:.3f}}}{{1+{l['params']['e0']}}} \cdot {H}$")
        
        math_log.append(f"**Result: $S = {settlement:.4f}$ m**")
        
        return {
            "settlement": settlement,
            "status": status,
            "sig_0": sig_0,
            "sig_f": sig_f,
            "log": math_log,
            "params": params if l['type'] == "Clay" else {}
        }

    # =================================================================
    # 5. MODE SPECIFIC LOGIC
    # =================================================================
    
    # -------------------------------------------------------------
    # MODE 1: FINAL SETTLEMENT
    # -------------------------------------------------------------
    if "1. Final" in calc_mode:
        st.markdown("---")
        if st.button("Calculate $S_{final}$", type="primary"):
            st.markdown("### 📊 Results: Final Settlement")
            
            total_settlement = 0.0
            calculated_layers = [] # For plotting

            c_res, c_path = st.columns([1.1, 0.9])

            with c_res:
                for l in layers_data:
                    # CALL CALCULATION ENGINE
                    res = calculate_layer(l, layers_data, water_depth, surcharge_q)
                    
                    # Add plot data
                    l['sig_0'] = res['sig_0']
                    l['sig_f'] = res['sig_f']
                    l['params'] = res['params']
                    calculated_layers.append(l)

                    if res['settlement'] > 0:
                        st.success(f"**Layer {l['id']} ({res['status']}):** {res['settlement']*1000:.2f} mm")
                        with st.expander(f"Show Calculations (Layer {l['id']})"):
                            for line in res['log']:
                                st.write(line)
                    
                    total_settlement += res['settlement']
                
                st.metric("Total Final Settlement ($S_{final}$)", f"{total_settlement*1000:.2f} mm")

            with c_path:
                clay_layers = [l for l in calculated_layers if l['type'] == "Clay" and "Method A" in l['method']]
                if clay_layers:
                    st.markdown("#### Stress Path ($e - \log \sigma'$)")
                    layer_opts = [f"Layer {l['id']}" for l in clay_layers]
                    if len(layer_opts) > 1:
                        choice = st.selectbox("Select Layer to Plot:", layer_opts)
                        pl_layer = next(l for l in clay_layers if f"Layer {l['id']}" == choice)
                    else:
                        pl_layer = clay_layers[0]

                    fig, ax = plt.subplots(figsize=(5, 3.5))
                    p = pl_layer['params']
                    s0 = pl_layer['sig_0']
                    sf = pl_layer['sig_f']
                    sp = p['sigma_p']
                    e0 = p['e0']
                    Cc = p['Cc']
                    Cr = p['Cr']

                    x = np.logspace(np.log10(min(10, s0/2)), np.log10(max(sf*2, 1000)), 100)
                    
                    if s0 >= sp: 
                        y_virgin = e0 - Cc * np.log10(x / s0)
                        path_x = [s0, sf]
                        path_y = [e0, e0 - Cc * np.log10(sf/s0)]
                        ax.plot(x, y_virgin, 'r--', alpha=0.3, label="Virgin")
                    else: 
                        y_recomp = e0 - Cr * np.log10(x / s0)
                        ax.plot(x, y_recomp, 'g--', alpha=0.3, label="Recomp")
                        ep = e0 - Cr * np.log10(sp / s0)
                        x_vir = x[x>=sp]
                        y_vir = ep - Cc * np.log10(x_vir / sp)
                        ax.plot(x_vir, y_vir, 'r--', alpha=0.3, label="Virgin")

                        if sf <= sp:
                            path_x = [s0, sf]
                            path_y = [e0, e0 - Cr * np.log10(sf/s0)]
                        else:
                            ef = ep - Cc * np.log10(sf/sp)
                            path_x = [s0, sp, sf]
                            path_y = [e0, ep, ef]

                    ax.plot(path_x, path_y, 'bo-', label="Path")
                    ax.set_xscale('log')
                    ax.set_xlabel("Effective Stress $\sigma'$ (kPa)")
                    ax.set_ylabel("Void Ratio $e$")
                    ax.grid(True, which="both", alpha=0.2)
                    st.pyplot(fig)

    # -------------------------------------------------------------
    # MODE 2: TIME RATE
    # -------------------------------------------------------------
    else:
        st.markdown("---")
        st.subheader("Time Rate Parameters")
        
        clay_layers = [l for l in layers_data if l['type'] == "Clay"]
        
        if not clay_layers:
            st.error("You need at least one Clay layer to calculate Consolidation Time.")
        else:
            clay_opts = [f"Layer {l['id']}" for l in clay_layers]
            crit_choice = st.selectbox("Select Critical Clay Layer", clay_opts)
            crit_layer = next(l for l in clay_layers if f"Layer {l['id']}" == crit_choice)
            
            c_t1, c_t2 = st.columns(2)
            cv = c_t1.number_input("Coeff. of Consolidation ($c_v$) [m²/year]", value=2.0)
            dr_path = c_t2.number_input("Drainage Path ($d$ or $H_{dr}$) [m]", value=crit_layer['thickness']/2)
            
            time_goal = st.radio("Goal:", ["Find Time ($t$) for specific $U_{av}$", "Find Settlement ($S_t$) at specific Time ($t$)"])
            
            if st.button("Calculate Time Rate", type="primary"):
                # 1. Calculate Total S_final first (using our helper)
                total_s_final = 0.0
                st.markdown("#### 1. Total Settlement Calculation")
                for l in layers_data:
                    res = calculate_layer(l, layers_data, water_depth, surcharge_q)
                    total_s_final += res['settlement']
                    if res['settlement'] > 0:
                         with st.expander(f"Layer {l['id']} Calc (S = {res['settlement']*1000:.1f} mm)"):
                             for line in res['log']: st.write(line)

                st.info(f"**Total Ultimate Settlement ($S_{{final}}$) = {total_s_final*1000:.2f} mm**")
                
                st.markdown("#### 2. Time Rate Calculation")
                if "Find Time" in time_goal:
                    U_target = st.slider("Target $U_{av}$ (%)", 0, 100, 90)
                    U_dec = U_target / 100.0
                    
                    if U_dec <= 0.6: Tv = (np.pi/4) * (U_dec**2)
                    else: Tv = -0.933 * np.log10(1 - U_dec) - 0.085
                        
                    if cv > 0:
                        t_req = (Tv * dr_path**2) / cv
                        st.success(f"**Time required: {t_req:.2f} years**")
                        st.latex(rf"T_v = {Tv:.4f} \quad (\text{{from }} U_{{av}}={U_target}\%)")
                        st.latex(rf"t = \frac{{T_v d^2}}{{c_v}} = \frac{{{Tv:.4f} \cdot ({dr_path})^2}}{{{cv}}} = {t_req:.2f} \text{{ years}}")

                else:
                    t_val = st.number_input("Time (years)", 1.0)
                    
                    if cv > 0:
                        Tv = (cv * t_val) / (dr_path**2)
                        if Tv <= 0.28:
                            U_calc = 2 * np.sqrt(Tv / np.pi)
                            eq_label = r"U_{av} = 2\sqrt{T_v / \pi}"
                        else:
                            exponent = -(Tv + 0.085) / 0.933
                            U_calc = 1 - (10 ** exponent)
                            eq_label = r"U_{av} = 1 - 10^{-\frac{T_v + 0.085}{0.933}}"
                        
                        if U_calc > 1.0: U_calc = 1.0
                        s_t = total_s_final * U_calc
                        
                        st.success(f"**Settlement at {t_val} years: {s_t*1000:.2f} mm**")
                        st.write(f"**Calculation Steps:**")
                        st.latex(rf"T_v = \frac{{c_v t}}{{d^2}} = \frac{{{cv} \cdot {t_val}}}{{{dr_path}^2}} = {Tv:.4f}")
                        st.write(f"Using equation for $T_v$:")
                        st.latex(eq_label)
                        st.metric("Average Degree of Consolidation ($U_{av}$)", f"{U_calc*100:.1f} %")

if __name__ == "__main__":
    app()
