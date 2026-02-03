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
def draw_cross_section(shape, dims, num_bars, bar_dia, trans_type, show_ties):
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
            # ONLY DRAW TIES IF SHOW_TIES IS TRUE
            if show_ties:
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
            
            # ONLY DRAW SPIRAL/TIE IF SHOW_TIES IS TRUE
            if show_ties:
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
        "🎯 Calculation Mode",
        ["Find Capacity", "Find Steel Area (Ast)", "Find Concrete Area (Ag)"],
        horizontal=True
    )
    st.markdown("---")

    col_input, col_viz = st.columns([1.3, 1])

    with col_input:
        st.subheader("1. Design Inputs")
        
        # --- A. CODE & SHAPE ---
        with st.expander("⚙️ Code & Shape Settings", expanded=True):
            design_code = st.selectbox("Design Code", ["ACI 318-19 (USA/Gulf)", "Eurocode 2 (EU)", "TS 500 (Turkey)"])
            shape = st.selectbox("Column Shape", ["Rectangular", "Square", "Circular"])
            if shape == "Circular":
                trans_type = st.radio("Transverse Reinforcement", ["Circular Ties", "Spiral"])
            else:
                trans_type = "Ties"

        # --- B. MATERIALS ---
        st.markdown("**Material Properties**")
        c1, c2 = st.columns(2)
        with c1: 
            label_conc = "Concrete (f_ck)" if "TS 500" in design_code or "Eurocode" in design_code else "Concrete (f'c)"
            fc = st.number_input(f"{label_conc} [MPa]", value=30.0, step=5.0)
        with c2: 
            label_steel = "Steel (f_yk)" if "TS 500" in design_code or "Eurocode" in design_code else "Steel (f_y)"
            fy = st.number_input(f"{label_steel} [MPa]", value=420.0, step=10.0)

        # --- C. GEOMETRY (CONCRETE) ---
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

        # --- D. REINFORCEMENT (STEEL) ---
        st.markdown("**Reinforcement (Steel)**")
        
        # LOGIC: Define Scope for "Find Capacity"
        show_ties = True # Default for diagrams
        if solve_mode == "Find Capacity":
            analysis_scope = st.radio(
                "Output Required:", 
                ["First Peak Only (Theoretical P0)", "Full Analysis (First Peak + Design Limit)"]
            )
            if "First Peak" in analysis_scope:
                st.caption("ℹ️ Calculates pure axial capacity assuming no buckling (Theoretical).")
                show_ties = False
            else:
                st.caption("ℹ️ Adds Transverse Reinforcement to calculate allowable Design Capacity.")
                show_ties = True

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
        
        # --- E. LOAD INPUT ---
        target_load = 0
        if solve_mode != "Find Capacity":
            st.markdown("**Design Load**")
            lc1, lc2 = st.columns(2)
            with lc1:
                load_type = st.selectbox("Load Type", ["Design Value (Nd / Phi Pn)", "Nominal/Theoretical (Pn / P0)"])
            with lc2:
                target_load = st.number_input(f"Enter Load Value [kN]", value=2000.0, step=100.0)

    # --- VISUALIZATION ---
    with col_viz:
        st.subheader("2. Visualization")
        if solve_mode == "Find Concrete Area (Ag)":
            st.warning("⚠️ Calculate first to see the section.")
        else:
            bars_to_draw = num_bars if (solve_mode != "Find Steel Area (Ast)" and not (solve_mode != "Find Steel Area (Ast)" and 'use_direct_Ast' in locals() and locals().get('use_direct_Ast'))) else 0
            
            fig1 = draw_cross_section(shape, dims, bars_to_draw, bar_dia, trans_type, show_ties)
            st.pyplot(fig1)
            plt.close(fig1)
            
            if 'Ag' in locals() and Ag > 0:
                rho_display = (Ast/Ag)*100
                st.caption(f"$A_g$: {Ag:,.0f} mm² | $\\rho$: {rho_display:.2f}%")

    st.markdown("---")

    # ======================================
    # 4. CALCULATION REPORT
    # ======================================
    st.subheader("3. Calculation Report")
    
    if st.button("Run Calculation", type="primary"):
        st.markdown("#### 📝 Step-by-Step Substitution")
        
        is_aci = "ACI" in design_code
        is_ts500 = "TS 500" in design_code
        
        # Factors
        if is_aci:
            if trans_type == "Spiral": phi, alpha = 0.75, 0.85
            else: phi, alpha = 0.65, 0.80
        else:
            gamma_c, gamma_s = 1.5, 1.15
            alpha_cc = 1.0 if is_ts500 else 0.85
            fcd = (alpha_cc * fc) / gamma_c
            fyd = fy / gamma_s
            
            # Show material calc
            c1, c2 = st.columns(2)
            with c1: st.latex(fr"f_{{cd}} = {fcd:.2f}\ MPa")
            with c2: st.latex(fr"f_{{yd}} = {fyd:.2f}\ MPa")

        # ==========================================
        # MODE 1: FIND CAPACITY
        # ==========================================
        if solve_mode == "Find Capacity":
            
            # --- 1. THEORETICAL FIRST PEAK (P0) ---
            # This is calculated regardless of mode, as it's the base
            if is_aci:
                # P0 = 0.85 fc (Ag-Ast) + fy Ast
                P0_kN = (0.85 * fc * (Ag - Ast) + fy * Ast) / 1000
                st.markdown("### Peak 1: Theoretical Capacity ($P_0$)")
                st.caption("Maximum axial load assuming zero eccentricity and perfect stability.")
                
                st.latex(r"P_0 = 0.85 f'_c (A_g - A_{st}) + f_y A_{st}")
                st.latex(fr"P_0 = 0.85({fc})({Ag:,.0f} - {Ast:,.0f}) + {fy}({Ast:,.0f})")
                st.metric("P0 (First Peak)", f"{P0_kN:,.0f} kN")
            
            else: # TS 500
                N0_kN = (fcd * (Ag - Ast) + fyd * Ast) / 1000
                st.markdown("### Peak 1: Axial Strength ($N_0$)")
                st.latex(r"N_0 = f_{cd}(A_g - A_s) + f_{yd} A_s")
                st.metric("N0 (First Peak)", f"{N0_kN:,.0f} kN")

            # --- 2. DESIGN CAPACITY (SECOND PEAK) ---
            if "Full Analysis" in analysis_scope:
                st.markdown("---")
                if is_aci:
                    st.markdown("### Peak 2: Design Capacity ($\phi P_{n(max)}$)")
                    st.caption(f"Includes Transverse Reinforcement ({trans_type}). Limits applied: $\\alpha={alpha}, \\phi={phi}$.")
                    
                    PhiPn_kN = alpha * phi * P0_kN
                    
                    st.latex(r"\phi P_{n(max)} = \alpha \cdot \phi \cdot P_0")
                    st.latex(fr"\phi P_{{n(max)}} = {alpha} \cdot {phi} \cdot {P0_kN:,.0f}")
                    st.metric("Design Limit (Second Peak)", f"{PhiPn_kN:,.0f} kN", delta="Allowed Load")
                else:
                    # For TS500/EC2, usually N0 is the design strength Nd if eccentricity is minimal
                    # But if we strictly mean "Second Peak" as in P-M diagram plateau:
                    st.info("In TS 500 / Eurocode, the Axial Capacity ($N_d$) calculated above is the standard design value used.")


        # ==========================================
        # MODE 2: FIND STEEL AREA
        # ==========================================
        elif solve_mode == "Find Steel Area (Ast)":
            target_P0_kN = target_load
            
            # Convert if Design Load
            if is_aci and "Design" in load_type:
                target_P0_kN = target_load / (alpha * phi)
                st.write(f"**Step 0: Convert to Nominal ($P_n$)**")
                st.latex(fr"P_n = {target_load} / ({alpha} \cdot {phi}) = {target_P0_kN:,.1f}\ kN")
            
            target_P0_N = target_P0_kN * 1000
            
            if is_aci:
                numerator = target_P0_N - 0.85 * fc * Ag
                denominator = fy - 0.85 * fc
                req_Ast = numerator / denominator
                
                st.markdown("**Formula for $A_{st}$:**")
                st.latex(r"A_{st} = \frac{P_n - 0.85 f'_c A_g}{f_y - 0.85 f'_c}")
            else:
                numerator = (target_load * 1000) - fcd * Ag
                denominator = fyd - fcd
                req_Ast = numerator / denominator
                
                st.markdown("**Formula for $A_s$:**")
                st.latex(r"A_s = \frac{N_d - f_{cd} A_g}{f_{yd} - f_{cd}}")
            
            if req_Ast < 0:
                st.error("❌ Negative Result: Concrete alone is strong enough.")
            else:
                st.markdown(f"### ✅ Required Steel: **{req_Ast:,.0f} mm²**")
                st.latex(fr"A_{{st}} = \frac{{{numerator:,.0f}}}{{{denominator:.2f}}}")

        # ==========================================
        # MODE 3: FIND CONCRETE AREA
        # ==========================================
        elif solve_mode == "Find Concrete Area (Ag)":
            target_P0_kN = target_load
            
            if is_aci and "Design" in load_type:
                target_P0_kN = target_load / (alpha * phi)
                st.write(f"**Step 0: Convert to Nominal ($P_n$)**")
                st.latex(fr"P_n = {target_load} / ({alpha} \cdot {phi}) = {target_P0_kN:,.1f}\ kN")
            
            target_P0_N = target_P0_kN * 1000
            
            if is_aci:
                numerator = target_P0_N - Ast * (fy - 0.85*fc)
                denominator = 0.85 * fc
                req_Ag = numerator / denominator
                
                st.markdown("**Formula for $A_g$:**")
                st.latex(r"A_g = \frac{P_n - A_{st}(f_y - 0.85 f'_c)}{0.85 f'_c}")
            else:
                numerator = (target_load * 1000) - Ast * (fyd - fcd)
                denominator = fcd
                req_Ag = numerator / denominator
                
                st.markdown("**Formula for $A_c$:**")
                st.latex(r"A_c = \frac{N_d - A_s(f_{yd} - f_{cd})}{f_{cd}}")

            if req_Ag < 0:
                st.error("❌ Calculation Error: Check inputs.")
            else:
                st.markdown(f"### ✅ Required Concrete: **{req_Ag:,.0f} mm²**")
                st.latex(fr"A_g = \frac{{{numerator:,.0f}}}{{{denominator:.2f}}}")
