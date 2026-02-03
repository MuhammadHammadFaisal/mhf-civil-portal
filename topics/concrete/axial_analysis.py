import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ======================================
# 1. HELPER: BAR DISTRIBUTION LOGIC
# ======================================
def distribute_bars_rectangular(b, h, cover, num_bars):
    xL, xR = cover, b - cover
    yB, yT = cover, h - cover
    positions = [(xL, yB), (xR, yB), (xR, yT), (xL, yT)]
    remaining = num_bars - 4
    if remaining <= 0: return positions[:num_bars] 

    if h >= b:
        faces = [("left", xL, yB, yT), ("right", xR, yB, yT), ("bottom", yB, xL, xR), ("top", yT, xL, xR)]
    else:
        faces = [("bottom", yB, xL, xR), ("top", yT, xL, xR), ("left", xL, yB, yT), ("right", xR, yB, yT)]

    face_counts = [0] * 4
    for i in range(remaining): face_counts[i % 4] += 1

    for i, count in enumerate(face_counts):
        if count == 0: continue
        face_name, fixed, start, end = faces[i]
        spacing = (end - start) / (count + 1)
        internal_points = [start + spacing * (j+1) for j in range(count)]
        for p in internal_points:
            if face_name in ["left", "right"]: positions.append((fixed, p)) 
            else: positions.append((p, fixed))
    return positions

# ======================================
# 2. HELPER: DRAWING FUNCTIONS
# ======================================
def draw_cross_section(shape, dims, num_bars, bar_dia, trans_type, has_transverse):
    fig, ax = plt.subplots(figsize=(4, 4))
    cover = 40 
    bar_r = bar_dia / 2
    fig.patch.set_alpha(0) 
    ax.patch.set_alpha(0)

    if shape in ["Rectangular", "Square"]:
        b, h = dims
        ax.add_patch(patches.Rectangle((0, 0), b, h, fill=True, facecolor='#e0e0e0', edgecolor='black', linewidth=2))
        ax.set_xlim(-50, b + 50)
        ax.set_ylim(-50, h + 50)
        
        if num_bars > 0:
            positions = distribute_bars_rectangular(b, h, cover, num_bars)
            # ONLY DRAW TIES IF HAS_TRANSVERSE IS TRUE
            if has_transverse:
                ax.add_patch(patches.Rectangle((cover/2, cover/2), b-cover, h-cover, fill=False, edgecolor='#555', linewidth=1.5, linestyle='--'))
            
            for x, y in positions: ax.add_patch(patches.Circle((x, y), bar_r, color="#d32f2f", zorder=10))
            
    else:  # Circular
        D = dims[0]
        cx, cy = D / 2, D / 2
        ax.add_patch(patches.Circle((cx, cy), D/2, fill=True, facecolor='#e0e0e0', edgecolor='black', linewidth=2))
        ax.set_xlim(-50, D + 50)
        ax.set_ylim(-50, D + 50)
        if num_bars > 0:
            angles = np.linspace(0, 2 * np.pi, num_bars, endpoint=False)
            positions = [(cx + (D/2-cover) * np.cos(a), cy + (D/2-cover) * np.sin(a)) for a in angles]
            
            # ONLY DRAW SPIRAL/TIE IF HAS_TRANSVERSE IS TRUE
            if has_transverse:
                linestyle = '-' if trans_type == "Spiral" else '--'
                ax.add_patch(patches.Circle((cx, cy), D/2 - cover/2, fill=False, edgecolor='#555', linewidth=1.5, linestyle=linestyle))
            
            for x, y in positions: ax.add_patch(patches.Circle((x, y), bar_r, color="#d32f2f", zorder=10))

    ax.set_aspect("equal")
    ax.axis("off")
    return fig

# ======================================
# 3. MAIN APP
# ======================================
def app():
    st.header("🏗️ Analysis of Axial Load Capacity")
    st.markdown("---")

    solve_mode = st.radio(
        "🎯 What do you want to calculate?",
        ["Find Capacity (Standard)", "Find Steel Area (Ast)", "Find Concrete Area (Ag)"],
        horizontal=True
    )
    st.markdown("---")

    col_input, col_viz = st.columns([1.3, 1])

    with col_input:
        st.subheader("1. Design Inputs")
        
        with st.expander("⚙️ Code & Shape Settings", expanded=True):
            design_code = st.selectbox("Design Code", ["ACI 318-19 (USA/Gulf)", "Eurocode 2 (EU)", "TS 500 (Turkey)"])
            shape = st.selectbox("Column Shape", ["Rectangular", "Square", "Circular"])
            if shape == "Circular":
                trans_type = st.radio("Transverse Reinforcement", ["Circular Ties", "Spiral"])
            else:
                trans_type = "Ties"

        st.markdown("**Material Properties**")
        c1, c2 = st.columns(2)
        with c1: 
            label_conc = "Concrete (f_ck)" if "TS 500" in design_code or "Eurocode" in design_code else "Concrete (f'c)"
            fc = st.number_input(f"{label_conc} [MPa]", value=30.0, step=5.0)
        with c2: 
            label_steel = "Steel (f_yk)" if "TS 500" in design_code or "Eurocode" in design_code else "Steel (f_y)"
            fy = st.number_input(f"{label_steel} [MPa]", value=420.0, step=10.0)

        st.markdown("**Geometry (Concrete)**")
        if solve_mode == "Find Concrete Area (Ag)":
            st.info("💡 Calculating required Concrete Area ($A_g$).")
            Ag = 0 
            dims = (300, 300) 
        else:
            use_direct_Ag = st.checkbox("Enter Concrete Area ($A_g$) directly?", value=False)
            if use_direct_Ag:
                Ag = st.number_input("Gross Concrete Area ($A_g$) [mm²]", value=90000.0, step=1000.0)
                if shape == "Circular": D = np.sqrt(4*Ag/np.pi); dims=(D,)
                else: side = np.sqrt(Ag); dims=(side, side)
            else:
                if shape == "Rectangular":
                    cc1, cc2 = st.columns(2)
                    with cc1: b = st.number_input("Width (b) [mm]", value=300.0, step=50.0)
                    with cc2: h = st.number_input("Depth (h) [mm]", value=500.0, step=50.0)
                    Ag = b * h
                    dims = (b, h)
                elif shape == "Square":
                    a = st.number_input("Side (a) [mm]", value=400.0, step=50.0)
                    Ag = a * a
                    dims = (a, a)
                else: 
                    D = st.number_input("Diameter (D) [mm]", value=400.0, step=50.0)
                    Ag = np.pi * D**2 / 4
                    dims = (D,)

        st.markdown("**Reinforcement (Steel)**")
        
        # --- NEW: TRANSVERSE CHECK ---
        has_transverse = st.checkbox("✅ Is Transverse Reinforcement (Ties/Spirals) provided?", value=True)
        if not has_transverse:
            st.error("⚠️ Warning: Without ties, longitudinal bars will buckle. Steel contribution ($f_y A_{st}$) will be ignored!")

        if solve_mode == "Find Steel Area (Ast)":
            st.info("💡 Calculating required Steel Area ($A_{st}$).")
            Ast = 0 
            num_bars = 0 
            bar_dia = 20 
        else:
            use_direct_Ast = st.checkbox("Enter Steel Area ($A_{st}$) directly?", value=False)
            if use_direct_Ast:
                Ast = st.number_input("Total Steel Area ($A_{st}$) [mm²]", value=2000.0, step=100.0)
                num_bars = 0 
                bar_dia = 20 
            else:
                rc1, rc2 = st.columns(2)
                with rc1:
                    bar_dia = st.number_input("Bar Dia [mm]", value=20.0, step=2.0)
                    num_bars = st.number_input("Total Bars", value=6, min_value=4)
                Ast = num_bars * np.pi * (bar_dia / 2) ** 2
        
        target_load = 0
        if solve_mode != "Find Capacity (Standard)":
            st.markdown("**Design Load**")
            lc1, lc2 = st.columns(2)
            with lc1:
                load_type = st.selectbox("Load Type", ["Design Value (Nd / Phi Pn)", "Nominal/Theoretical (Pn / P0)"])
            with lc2:
                target_load = st.number_input(f"Enter Load Value [kN]", value=2000.0, step=100.0)

    with col_viz:
        st.subheader("2. Visualization")
        if solve_mode == "Find Concrete Area (Ag)":
            st.warning("⚠️ Calculate first to see the section.")
        else:
            bars_to_draw = num_bars if (solve_mode != "Find Steel Area (Ast)" and not (solve_mode != "Find Steel Area (Ast)" and 'use_direct_Ast' in locals() and locals().get('use_direct_Ast'))) else 0
            # Pass the check value to drawing function
            fig1 = draw_cross_section(shape, dims, bars_to_draw, bar_dia, trans_type, has_transverse)
            st.pyplot(fig1)
            plt.close(fig1)
            if not has_transverse:
                st.caption("❌ No Confinement (Ties Hidden)")
            elif 'Ag' in locals():
                st.caption(f"Config: {shape} | $A_g$: {Ag:,.0f} mm²")

    st.markdown("---")

    # ======================================
    # 4. CALCULATION REPORT (DETAILED)
    # ======================================
    st.subheader("3. Calculation Report")
    
    if st.button("Run Calculation", type="primary"):
        st.markdown("#### 📝 Step-by-Step Substitution")
        
        is_aci = "ACI" in design_code
        is_ts500 = "TS 500" in design_code
        
        # --- CONSTANTS SETUP ---
        if is_aci:
            if trans_type == "Spiral": phi, alpha = 0.75, 0.85
            else: phi, alpha = 0.65, 0.80
            st.write(f"**Factors:** $\\alpha = {alpha}$ (Eccentricity), $\\phi = {phi}$ ({trans_type})")
        else:
            gamma_c, gamma_s = 1.5, 1.15
            alpha_cc = 1.0 if is_ts500 else 0.85
            fcd = (alpha_cc * fc) / gamma_c
            fyd = fy / gamma_s
            
            c1, c2 = st.columns(2)
            with c1: 
                st.latex(fr"f_{{cd}} = \frac{{{alpha_cc} \cdot {fc}}}{{\ {gamma_c} }} = {fcd:.2f}\ MPa")
            with c2: 
                st.latex(fr"f_{{yd}} = \frac{{{fy}}}{{\ {gamma_s} }} = {fyd:.2f}\ MPa")

        # --- LOGIC: HANDLE NO TRANSVERSE REINFORCEMENT ---
        # If no transverse reinforcement, Steel contribution is ZERO.
        # Effectively, we set Ast_effective to 0 for strength calcs, but keep Ast real for Area calcs?
        # Actually, if finding Area, we can't really find Steel Area if it does nothing.
        
        if not has_transverse:
            st.warning("⚠️ **Physics Note:** Since no transverse reinforcement is provided, the longitudinal bars ($A_{st}$) are assumed to buckle and provide **0 Strength**.")
            effective_Ast_strength = 0 # Strength contribution is zero
        else:
            effective_Ast_strength = 1 # Multiplier (1 = normal, 0 = ignore)

        # ==========================================
        # MODE 1: FIND CAPACITY
        # ==========================================
        if solve_mode == "Find Capacity (Standard)":
            if not has_transverse:
                # Ast term becomes 0
                term_steel = 0
            else:
                term_steel = Ast # Normal behavior
            
            if is_aci:
                # Pn = 0.85 fc (Ag - Ast) + fy * Ast_effective
                # Note: Ag - Ast is net concrete. Even without ties, the holes for bars exist.
                Pn_kN = (0.85 * fc * (Ag - Ast) + fy * term_steel) / 1000
                PhiPn_kN = alpha * phi * Pn_kN
                
                st.markdown("**Step 1: Nominal Strength ($P_n$)**")
                if not has_transverse:
                    st.latex(r"P_n = 0.85 f'_c (A_g - A_{st}) + \cancel{f_y A_{st}}")
                else:
                    st.latex(r"P_n = 0.85 f'_c (A_g - A_{st}) + f_y A_{st}")
                
                st.latex(fr"P_n = 0.85({fc})({Ag:,.0f} - {Ast:,.0f}) + {fy}({term_steel:,.0f})")
                st.write(f"➝ $P_n$ = {Pn_kN:,.0f} kN")
                
                st.markdown("**Step 2: Design Strength ($\phi P_{n(max)}$)**")
                st.latex(r"\phi P_{n(max)} = \alpha \cdot \phi \cdot P_n")
                st.latex(fr"\phi P_{{n(max)}} = {alpha} \cdot {phi} \cdot {Pn_kN:,.0f}")
                st.markdown(f"### ✅ Capacity: **{PhiPn_kN:,.0f} kN**")
                
            else: # TS 500
                Nd_kN = (fcd * (Ag - Ast) + fyd * term_steel) / 1000
                
                st.markdown("**Step 1: Calculate Design Load ($N_d$)**")
                if not has_transverse:
                    st.latex(r"N_d = f_{cd}(A_g - A_s) + \cancel{f_{yd} A_s}")
                else:
                    st.latex(r"N_d = f_{cd}(A_g - A_s) + f_{yd} A_s")
                    
                st.latex(fr"N_d = {fcd:.2f}({Ag:,.0f} - {Ast:,.0f}) + {fyd:.2f}({term_steel:,.0f})")
                st.markdown(f"### ✅ Capacity: **{Nd_kN:,.0f} kN**")

        # ==========================================
        # MODE 2: FIND STEEL AREA
        # ==========================================
        elif solve_mode == "Find Steel Area (Ast)":
            if not has_transverse:
                st.error("❌ **Impossible Calculation:** You cannot calculate required steel area if there are no ties/spirals to support it. The steel would effectively do nothing.")
            else:
                # PREP LOAD
                target_P0_kN = target_load
                if is_aci and "Design" in load_type:
                    target_P0_kN = target_load / (alpha * phi)
                    st.write(f"**Step 0: Convert to Nominal Load**")
                    st.latex(fr"P_n = \frac{{P_u}}{{\alpha \phi}} = \frac{{{target_load}}}{{{alpha} \cdot {phi}}} = {target_P0_kN:,.1f}\ kN")
                
                target_P0_N = target_P0_kN * 1000
                
                if is_aci:
                    term_conc = 0.85 * fc * Ag
                    term_steel_stress = fy - 0.85 * fc
                    req_Ast = (target_P0_N - term_conc) / term_steel_stress
                    
                    st.markdown("**Step 1: Rearrange Formula for $A_{st}$**")
                    st.latex(r"A_{st} = \frac{P_n - 0.85 f'_c A_g}{f_y - 0.85 f'_c}")
                    
                    st.markdown("**Step 2: Substitute**")
                    numerator_str = fr"{target_P0_N:,.0f} - 0.85({fc})({Ag:,.0f})"
                    denom_str = fr"{fy} - 0.85({fc})"
                    st.latex(fr"A_{{st}} = \frac{{{numerator_str}}}{{{denom_str}}}")
                    
                else: # TS 500
                    load_N = target_load * 1000
                    term_conc = fcd * Ag
                    term_steel_stress = fyd - fcd
                    req_Ast = (load_N - term_conc) / term_steel_stress

                    st.markdown("**Step 1: Rearrange Formula for $A_s$**")
                    st.latex(r"A_s = \frac{N_d - f_{cd} A_g}{f_{yd} - f_{cd}}")
                    
                    st.markdown("**Step 2: Substitute**")
                    num_str = fr"{load_N:,.0f} - {fcd:.2f}({Ag:,.0f})"
                    den_str = fr"{fyd:.2f} - {fcd:.2f}"
                    st.latex(fr"A_s = \frac{{{num_str}}}{{{den_str}}}")

                if req_Ast < 0:
                    st.error("❌ Result is negative. The concrete section alone is stronger than the load.")
                else:
                    st.markdown(f"### ✅ Required Steel: **{req_Ast:,.0f} mm²**")
                    st.info(f"Ratio $\\rho = {(req_Ast/Ag)*100:.2f}\\%$")

        # ==========================================
        # MODE 3: FIND CONCRETE AREA
        # ==========================================
        elif solve_mode == "Find Concrete Area (Ag)":
            # PREP LOAD
            target_P0_kN = target_load
            if is_aci and "Design" in load_type:
                target_P0_kN = target_load / (alpha * phi)
                st.write(f"**Step 0: Convert to Nominal Load**")
                st.latex(fr"P_n = \frac{{{target_load}}}{{{alpha} \cdot {phi}}} = {target_P0_kN:,.1f}\ kN")
            
            target_P0_N = target_P0_kN * 1000
            
            # If No Transverse, Ast term is ignored in strength
            eff_Ast = Ast if has_transverse else 0
            
            if is_aci:
                # Pn = 0.85fc(Ag - Ast) + fy*eff_Ast
                # Pn = 0.85fc*Ag - 0.85fc*Ast + fy*eff_Ast
                # Ag = (Pn + 0.85fc*Ast - fy*eff_Ast) / 0.85fc
                
                # If has_transverse: Ag = (Pn - Ast(fy - 0.85fc)) / 0.85fc
                # If NO transverse:  Ag = (Pn + 0.85fc*Ast) / 0.85fc  (Steel is just holes)
                
                if has_transverse:
                    numerator = target_P0_N - Ast * (fy - 0.85*fc)
                    st.markdown("**Formula (With Ties):**")
                    st.latex(r"A_g = \frac{P_n - A_{st}(f_y - 0.85 f'_c)}{0.85 f'_c}")
                else:
                    numerator = target_P0_N + 0.85*fc*Ast
                    st.markdown("**Formula (No Ties - Steel ignored):**")
                    st.latex(r"A_g = \frac{P_n + 0.85 f'_c A_{st}}{0.85 f'_c}")
                    
                denominator = 0.85 * fc
                req_Ag = numerator / denominator
                
                st.markdown("**Substitution**")
                st.latex(fr"A_g = \frac{{{numerator:,.0f}}}{{{denominator:.2f}}}")
                
            else: # TS500
                # Nd = fcd(Ag - Ast) + fyd*eff_Ast
                # Nd = fcd*Ag - fcd*Ast + fyd*eff_Ast
                # Ag = (Nd + fcd*Ast - fyd*eff_Ast) / fcd
                
                if has_transverse:
                    numerator = (target_load * 1000) - Ast * (fyd - fcd)
                    st.markdown("**Formula (With Ties):**")
                    st.latex(r"A_c = \frac{N_d - A_s(f_{yd} - f_{cd})}{f_{cd}}")
                else:
                    numerator = (target_load * 1000) + fcd * Ast
                    st.markdown("**Formula (No Ties - Steel ignored):**")
                    st.latex(r"A_c = \frac{N_d + f_{cd} A_s}{f_{cd}}")

                denominator = fcd
                req_Ag = numerator / denominator
                
                st.markdown("**Substitution**")
                st.latex(fr"A_c = \frac{{{numerator:,.0f}}}{{{denominator:.2f}}}")

            if req_Ag < 0:
                st.error("❌ Calculation Error: Check inputs.")
            else:
                st.markdown(f"### ✅ Required Concrete: **{req_Ag:,.0f} mm²**")
                side = np.sqrt(req_Ag)
                st.write(f"➝ Equivalent Square: **{side:.0f} x {side:.0f} mm**")
