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
def draw_cross_section(shape, dims, num_bars, bar_dia, trans_type):
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

    # --- TOP LEVEL: SOLVER MODE SELECTOR ---
    solve_mode = st.radio(
        "🎯 What do you want to calculate?",
        ["Find Capacity (Standard)", "Find Steel Area (Ast)", "Find Concrete Area (Ag)"],
        horizontal=True
    )
    st.markdown("---")

    col_input, col_viz = st.columns([1.3, 1])

    with col_input:
        st.subheader("1. Design Inputs")
        
        # --- A. SETTINGS ---
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

        # --- C. GEOMETRY INPUT ---
        st.markdown("**Geometry (Concrete)**")
        
        # LOGIC: If solving for Concrete Area, we don't input dimensions (unless we assume one to find the other, but let's keep it simple)
        if solve_mode == "Find Concrete Area (Ag)":
            st.info("💡 You are calculating the required Concrete Area. Dimensions are the output.")
            Ag = 0 # Placeholder
            dims = (300, 300) # Placeholder for viz
            
        else:
            # OPTION: Direct Area Input
            use_direct_area = st.checkbox("Enter Area ($A_g$) directly?", value=False)
            
            if use_direct_area:
                Ag = st.number_input("Gross Concrete Area ($A_g$) [mm²]", value=90000.0, step=1000.0)
                # Approximation for viz
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
                else: # Circular
                    D = st.number_input("Diameter (D) [mm]", value=400.0, step=50.0)
                    Ag = np.pi * D**2 / 4
                    dims = (D,)

        # --- D. REINFORCEMENT / LOAD INPUT ---
        st.markdown("**Reinforcement & Load**")
        
        # CASE 1: SOLVING FOR CAPACITY (Standard)
        if solve_mode == "Find Capacity (Standard)":
            rc1, rc2 = st.columns(2)
            with rc1:
                bar_dia = st.number_input("Bar Dia [mm]", value=20.0, step=2.0)
                num_bars = st.number_input("Total Bars", value=6, min_value=4)
            with rc2:
                # Option to input Ast directly? Let's keep bar count for now for standard mode
                pass
            Ast = num_bars * np.pi * (bar_dia / 2) ** 2
            
            target_load = 0 # Not used

        # CASE 2: SOLVING FOR UNKNOWNS (Reverse)
        else:
            # We need the Load Input
            lc1, lc2 = st.columns(2)
            with lc1:
                load_type = st.selectbox("Known Load Type", ["Design Value (Nd / Phi Pn)", "Theoretical Peak (P0 / Pn)"])
            with lc2:
                target_load = st.number_input(f"Enter Load Value [kN]", value=2000.0, step=100.0)
            
            if solve_mode == "Find Steel Area (Ast)":
                st.info("💡 Calculating required Steel Area ($A_{st}$).")
                Ast = 0 # Placeholder
                num_bars = 0 # Placeholder
                bar_dia = 20 # Just for viz scaling
                
            elif solve_mode == "Find Concrete Area (Ag)":
                # We need Steel for this
                sc1, sc2 = st.columns(2)
                with sc1:
                    st.write("Define Steel:")
                    bar_dia = st.number_input("Bar Dia [mm]", value=20.0)
                    num_bars = st.number_input("Total Bars", value=8)
                Ast = num_bars * np.pi * (bar_dia / 2) ** 2

    # --- VISUALIZATION BLOCK ---
    with col_viz:
        st.subheader("2. Visualization")
        if solve_mode == "Find Concrete Area (Ag)":
            st.warning("⚠️ Calculate first to see the section.")
        else:
            fig1 = draw_cross_section(shape, dims, num_bars, bar_dia, trans_type)
            st.pyplot(fig1)
            plt.close(fig1)
            st.caption(f"Config: {shape} | $A_g$: {Ag:,.0f} mm²")

    st.markdown("---")

    # ======================================
    # 4. CALCULATION LOGIC
    # ======================================
    st.subheader("3. Calculation Report")
    
    if st.button("Run Calculation", type="primary"):
        
        # --- PREPARE CONSTANTS ---
        is_aci = "ACI" in design_code
        is_ts500 = "TS 500" in design_code
        
        # Factors
        if is_aci:
            if trans_type == "Spiral": phi, alpha = 0.75, 0.85
            else: phi, alpha = 0.65, 0.80
            safety_factor_str = f"$\\alpha={alpha}, \\phi={phi}$"
        else:
            # EC2 / TS500
            gamma_c, gamma_s = 1.5, 1.15
            alpha_cc = 1.0 if is_ts500 else 0.85
            
            fcd = (alpha_cc * fc) / gamma_c
            fyd = fy / gamma_s
            safety_factor_str = f"$f_{{cd}}={fcd:.2f}, f_{{yd}}={fyd:.2f}$"

        # ==========================================
        # LOGIC BRANCH 1: FIND CAPACITY (Standard)
        # ==========================================
        if solve_mode == "Find Capacity (Standard)":
            if is_aci:
                Pn_kN = (0.85 * fc * (Ag - Ast) + fy * Ast) / 1000
                PhiPn_kN = alpha * phi * Pn_kN
                
                c1, c2 = st.columns(2)
                c1.metric("Theoretical Peak (P0)", f"{Pn_kN:,.0f} kN")
                c2.metric("Design Capacity (Phi Pn)", f"{PhiPn_kN:,.0f} kN")
                
                st.latex(r"\phi P_{n(max)} = \alpha \phi [0.85 f'_c (A_g - A_{st}) + f_y A_{st}]")
                
            else: # TS500 / EC2
                # N_d = fcd(Ag-Ast) + fyd*Ast
                Nd_kN = (fcd * (Ag - Ast) + fyd * Ast) / 1000
                st.metric("Design Axial Strength (Nd)", f"{Nd_kN:,.0f} kN")
                st.latex(r"N_d = f_{cd}(A_g - A_s) + f_{yd}A_s")

        # ==========================================
        # LOGIC BRANCH 2: FIND STEEL AREA (Ast)
        # ==========================================
        elif solve_mode == "Find Steel Area (Ast)":
            # 1. Determine Target Theoretical Load (P0_target)
            target_P0_kN = target_load
            
            if is_aci and "Design" in load_type:
                # User gave PhiPn, we need Pn (P0)
                # PhiPn = alpha * phi * P0  ->  P0 = PhiPn / (alpha * phi)
                target_P0_kN = target_load / (alpha * phi)
                st.write(f"Converting Design Load to Nominal: $P_0 = {target_load} / ({alpha} \\cdot {phi}) = {target_P0_kN:,.1f}$ kN")
            
            # 2. Solve Equation
            target_P0_N = target_P0_kN * 1000
            
            if is_aci:
                # P0 = 0.85 fc Ag + Ast(fy - 0.85 fc)  <-- (Approximation using gross/net)
                # Exact: P0 = 0.85 fc (Ag - Ast) + fy Ast
                # P0 = 0.85 fc Ag - 0.85 fc Ast + fy Ast
                # P0 - 0.85 fc Ag = Ast (fy - 0.85 fc)
                term1 = 0.85 * fc * Ag
                term2 = fy - 0.85 * fc
                req_Ast = (target_P0_N - term1) / term2
                
            else: # TS500
                # Nd = fcd Ag + Ast(fyd - fcd)
                # If target is P0 (Theoretical), we use fck/fyk? usually TS500 reverse designs use design values.
                # Assuming input is Nd always for TS500 reverse calc essentially.
                term1 = fcd * Ag
                term2 = fyd - fcd
                req_Ast = (target_load * 1000 - term1) / term2
            
            if req_Ast < 0:
                st.error("❌ Impossible! The concrete alone is stronger than the load. Use minimum reinforcement.")
            else:
                st.success(f"✅ Required Steel Area ($A_{{st}}$): **{req_Ast:,.0f} mm²**")
                rho_req = (req_Ast / Ag) * 100
                st.info(f"Required Reinforcement Ratio ($\\rho$): **{rho_req:.2f}%**")

        # ==========================================
        # LOGIC BRANCH 3: FIND CONCRETE AREA (Ag)
        # ==========================================
        elif solve_mode == "Find Concrete Area (Ag)":
            target_P0_kN = target_load
            if is_aci and "Design" in load_type:
                target_P0_kN = target_load / (alpha * phi)
            
            target_P0_N = target_P0_kN * 1000
            
            if is_aci:
                # P0 = 0.85 fc Ag - 0.85 fc Ast + fy Ast
                # P0 - Ast(fy - 0.85 fc) = 0.85 fc Ag
                # Ag = [P0 - Ast(fy - 0.85 fc)] / 0.85 fc
                numerator = target_P0_N - Ast * (fy - 0.85*fc)
                denominator = 0.85 * fc
                req_Ag = numerator / denominator
            else:
                # Nd = fcd Ag - fcd Ast + fyd Ast
                # Nd - Ast(fyd - fcd) = fcd Ag
                numerator = (target_load * 1000) - Ast * (fyd - fcd)
                denominator = fcd
                req_Ag = numerator / denominator
                
            if req_Ag < 0:
                st.error("Error in calculation inputs.")
            else:
                st.success(f"✅ Required Gross Concrete Area ($A_g$): **{req_Ag:,.0f} mm²**")
                # Suggest dimensions
                side = np.sqrt(req_Ag)
                st.write(f"Equivalent Square Side: **{side:.0f} mm**")
                st.write(f"Equivalent Circle Diameter: **{np.sqrt(4*req_Ag/np.pi):.0f} mm**")
