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
            if show_ties:
                ax.add_patch(patches.Rectangle((cover/2, cover/2), b-cover, h-cover, fill=False, edgecolor='#555', linewidth=1.5, linestyle='--'))
            for x, y in positions: ax.add_patch(patches.Circle((x, y), bar_r, color="#d32f2f", zorder=10))
            
    else:  # Circular
        D = dims[0]
        cx, cy = D / 2, D / 2
        ax.add_patch(patches.Circle((cx, cy), D/2, fill=True, facecolor='#e0e0e0', edgecolor='black', linewidth=2))
        
        # Draw Core for Spiral Visualization
        if trans_type == "Spiral" and show_ties:
             core_D = D - 2*cover # Approx core
             ax.add_patch(patches.Circle((cx, cy), core_D/2, fill=False, edgecolor='#999', linestyle=':', label="Core"))
        
        ax.set_xlim(-50, D + 50)
        ax.set_ylim(-50, D + 50)
        if num_bars > 0:
            angles = np.linspace(0, 2 * np.pi, num_bars, endpoint=False)
            positions = [(cx + (D/2-cover) * np.cos(a), cy + (D/2-cover) * np.sin(a)) for a in angles]
            
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
    st.header("Analysis of Axial Load Capacity")
    st.markdown("---")

    solve_mode = st.radio(
        " Calculation Mode",
        ["Find Capacity", "Find Steel Area (Ast)", "Find Concrete Area (Ag)"],
        horizontal=True
    )
    st.markdown("---")

    col_input, col_viz = st.columns([1.3, 1])

    with col_input:
        st.subheader("1. Design Inputs")
        
        with st.expander(" Code & Shape Settings", expanded=True):
            design_code = st.selectbox("Design Code", ["TS 500 (Lecture Notes)", "ACI 318-19", "Eurocode 2"])
            shape = st.selectbox("Column Shape", ["Rectangular", "Square", "Circular"])
            
            trans_type = "Ties"
            if shape == "Circular":
                trans_type = st.radio("Transverse Reinforcement", ["Circular Ties", "Spiral"])

        st.markdown("**Material Properties**")
        c1, c2 = st.columns(2)
        with c1: 
            label_conc = "Concrete (f_ck)" if "TS 500" in design_code or "Eurocode" in design_code else "Concrete (f'c)"
            fc = st.number_input(f"{label_conc} [MPa]", value=20.0, step=5.0)
        with c2: 
            label_steel = "Steel (f_yk)" if "TS 500" in design_code or "Eurocode" in design_code else "Steel (f_y)"
            fy = st.number_input(f"{label_steel} [MPa]", value=420.0, step=10.0)

        st.markdown("**Geometry (Concrete)**")
        if solve_mode == "Find Concrete Area (Ag)":
            st.info("Calculating required Area.")
            Ag = 0; dims = (300, 300) 
        else:
            use_direct_Ag = st.checkbox("Enter Concrete Area ($A_g$) directly?", value=False)
            if use_direct_Ag:
                Ag = st.number_input("Gross Area ($A_g$) [mm²]", value=75000.0, step=1000.0)
                if shape == "Circular": D = np.sqrt(4*Ag/np.pi); dims=(D,)
                else: side = np.sqrt(Ag); dims=(side, side)
            else:
                if shape == "Rectangular":
                    cc1, cc2 = st.columns(2)
                    with cc1: b = st.number_input("Width (b) [mm]", value=300.0, step=50.0)
                    with cc2: h = st.number_input("Depth (h) [mm]", value=250.0, step=50.0)
                    Ag = b * h; dims = (b, h)
                elif shape == "Square":
                    a = st.number_input("Side (a) [mm]", value=400.0, step=50.0)
                    Ag = a * a; dims = (a, a)
                else: 
                    D = st.number_input("Diameter (D) [mm]", value=300.0, step=50.0)
                    Ag = np.pi * D**2 / 4; dims = (D,)

        st.markdown("**Reinforcement (Steel)**")
        
        # New inputs for Spiral Analysis (TS 500)
        spiral_dia = 8.0
        spiral_pitch = 100.0
        cover = 25.0 # Default
        
        if "TS 500" in design_code and trans_type == "Spiral" and solve_mode == "Find Capacity":
            st.caption(" Spiral Details (for Confined Strength)")
            sc1, sc2, sc3 = st.columns(3)
            with sc1: spiral_dia = st.number_input("Spiral $\phi$ [mm]", value=8.0)
            with sc2: spiral_pitch = st.number_input("Pitch (s) [mm]", value=80.0)
            with sc3: cover = st.number_input("Cover [mm]", value=25.0)

        if solve_mode == "Find Steel Area (Ast)":
            st.info("Calculating required Steel.")
            Ast = 0; num_bars = 0; bar_dia = 20 
        else:
            use_direct_Ast = st.checkbox("Enter Steel Area ($A_{st}$) directly?", value=False)
            if use_direct_Ast:
                Ast = st.number_input("Total Steel Area ($A_{st}$) [mm²]", value=1600.0, step=100.0)
                num_bars = 0; bar_dia = 20 
            else:
                rc1, rc2 = st.columns(2)
                with rc1:
                    bar_dia = st.number_input("Bar Dia [mm]", value=16.0, step=2.0)
                    num_bars = st.number_input("Total Bars", value=8, min_value=4)
                Ast = num_bars * np.pi * (bar_dia / 2) ** 2
        
        target_load = 0
        if solve_mode != "Find Capacity":
            st.markdown("**Design Load**")
            lc1, lc2 = st.columns(2)
            with lc1: load_type = st.selectbox("Load Type", ["Design (Nd)", "Nominal (P0)"])
            with lc2: target_load = st.number_input(f"Enter Load [kN]", value=1400.0, step=100.0)

    with col_viz:
        st.subheader("2. Visualization")
        if solve_mode == "Find Concrete Area (Ag)":
            st.warning("Calculate first.")
        else:
            bars_to_draw = num_bars if (solve_mode != "Find Steel Area (Ast)" and not (solve_mode != "Find Steel Area (Ast)" and 'use_direct_Ast' in locals() and locals().get('use_direct_Ast'))) else 0
            fig1 = draw_cross_section(shape, dims, bars_to_draw, bar_dia, trans_type, True)
            st.pyplot(fig1)
            plt.close(fig1)

    st.markdown("---")

    # ======================================
    # 4. CALCULATION REPORT
    # ======================================
    st.subheader("3. Calculation Report")
    
    if st.button("Run Calculation", type="primary"):
        st.markdown("####  Step-by-Step Substitution")
        
        is_ts500 = "TS 500" in design_code
        is_aci = "ACI" in design_code
        
        # --- MATERIAL STRENGTHS ---
        if is_aci:
            phi = 0.75 if trans_type == "Spiral" else 0.65
            alpha = 0.85 if trans_type == "Spiral" else 0.80
            st.write(f"**Factors:** $\\alpha={alpha}, \\phi={phi}$")
        else:
            gamma_c, gamma_s = 1.5, 1.15
            fcd = fc / gamma_c
            fyd = fy / gamma_s
            
            c1, c2 = st.columns(2)
            with c1: st.latex(fr"f_{{cd}} = {fc} / {gamma_c} = {fcd:.2f}\ MPa")
            with c2: st.latex(fr"f_{{yd}} = {fy} / {gamma_s} = {fyd:.2f}\ MPa")

        # ==========================================
        # MODE 1: FIND CAPACITY
        # ==========================================
        if solve_mode == "Find Capacity":
            
            if is_aci:
                # ACI Logic (Standard)
                Pn_kN = (0.85 * fc * (Ag - Ast) + fy * Ast) / 1000
                PhiPn_kN = alpha * phi * Pn_kN
                st.markdown(f"**Design Capacity ($\phi P_{{n(max)}}$): {PhiPn_kN:,.0f} kN**")
                
            elif is_ts500:
                # TS 500 LOGIC (FROM LECTURE NOTES)
                # 1. Unconfined Capacity (First Peak)
                # Formula: Nor = 0.85 * fcd * Ac + Ast * fyd (Using Net Area for Ac)
                Ac_net = Ag - Ast
                Nor_kN = (0.85 * fcd * Ac_net + Ast * fyd) / 1000
                
                st.markdown("### Peak 1: Unconfined Capacity ($N_{or}$)")
                st.latex(r"N_{or} = 0.85 f_{cd} (A_g - A_{st}) + A_{st} f_{yd}")
                st.latex(fr"N_{{or}} = 0.85({fcd:.2f})({Ag:,.0f} - {Ast:,.0f}) + {Ast:,.0f}({fyd:.2f})")
                st.metric("First Peak Capacity", f"{Nor_kN:,.0f} kN")
                
                # 2. Confined Capacity (Second Peak) - Only for Spirals
                if trans_type == "Spiral":
                    st.markdown("---")
                    st.markdown("### Peak 2: Confined Capacity ($N_{or2}$)")
                    
                    # Core Geometry
                    D_col = dims[0]
                    D_core = D_col - 2*cover
                    Ack = np.pi * D_core**2 / 4
                    
                    # Spiral Ratio Provided
                    Asp = np.pi * spiral_dia**2 / 4 # Area of spiral bar
                    rho_s = (4 * Asp) / (D_core * spiral_pitch)
                    
                    # Minimum Spiral Ratio Check
                    # Formula 1: 0.45 * (fck/fyk) * (Ac/Ack - 1)
                    rho_min_1 = 0.45 * (fc / fy) * ((Ag / Ack) - 1)
                    # Formula 2: 0.12 * (fck/fyk)
                    rho_min_2 = 0.12 * (fc / fy)
                    rho_min = max(rho_min_1, rho_min_2)
                    
                    c1, c2 = st.columns(2)
                    with c1: 
                        st.write(f"**Core Area ($A_{{ck}}$):** {Ack:,.0f} mm²")
                        st.write(f"**Provided $\\rho_s$:** {rho_s:.4f}")
                    with c2:
                        st.write(f"**Min $\\rho_s$:** {rho_min:.4f}")
                        status = " OK" if rho_s >= rho_min else "❌ Insufficient"
                        st.write(f"**Check:** {status}")

                    if rho_s >= rho_min:
                        # Confined Strength Calculation
                        # f_ccd = (0.85*fck + 2*rho_s*fywk) / 1.5
                        # Note: Notes use fywk (yield of spiral). Assuming same as main steel fy for now.
                        f_cc_char = 0.85 * fc + 2 * rho_s * fy
                        f_ccd = f_cc_char / 1.5
                        
                        Nor2_kN = (f_ccd * Ack + Ast * fyd) / 1000
                        
                        st.latex(r"f_{ccd} = \frac{0.85 f_{ck} + 2 \rho_s f_{ywk}}{1.5}")
                        st.write(f"➝ Confined Concrete Strength: **{f_ccd:.2f} MPa**")
                        
                        st.latex(r"N_{or2} = f_{ccd} A_{ck} + A_{st} f_{yd}")
                        st.metric("Second Peak Capacity", f"{Nor2_kN:,.0f} kN", delta=f"{Nor2_kN - Nor_kN:,.0f} kN Gain")
                    else:
                        st.warning("Spiral reinforcement is less than minimum. Second peak cannot be developed.")
                
            else: # Eurocode Generic
                Nd_kN = (fcd * (Ag - Ast) + fyd * Ast) / 1000
                st.metric("Design Capacity", f"{Nd_kN:,.0f} kN")

        # ==========================================
        # MODE 2 & 3: REVERSE SOLVERS
        # ==========================================
        else:
             # Simplified Solver Logic (Focusing on First Peak for TS500)
             target_N = target_load * 1000
             
             if solve_mode == "Find Steel Area (Ast)":
                 if is_ts500:
                     # Nor = 0.85 fcd (Ag - Ast) + Ast fyd
                     # Nor = 0.85 fcd Ag - 0.85 fcd Ast + Ast fyd
                     # Nor - 0.85 fcd Ag = Ast (fyd - 0.85 fcd)
                     # Ast = (Nor - 0.85 fcd Ag) / (fyd - 0.85 fcd)
                     num = target_N - 0.85 * fcd * Ag
                     den = fyd - 0.85 * fcd
                     req_Ast = num / den
                     st.latex(r"A_{st} = \frac{N_d - 0.85 f_{cd} A_g}{f_{yd} - 0.85 f_{cd}}")
                 else:
                     # Generic EC2
                     req_Ast = (target_N - fcd * Ag) / (fyd - fcd)
                 
                 if req_Ast < 0: st.error("Concrete is strong enough.")
                 else: st.markdown(f"### Required Steel: **{req_Ast:,.0f} mm²**")

             elif solve_mode == "Find Concrete Area (Ag)":
                 if is_ts500:
                     # Ag = (Nor - Ast(fyd - 0.85fcd)) / 0.85fcd
                     num = target_N - Ast * (fyd - 0.85*fcd)
                     den = 0.85 * fcd
                     req_Ag = num / den
                     st.latex(r"A_g = \frac{N_d - A_{st}(f_{yd} - 0.85 f_{cd})}{0.85 f_{cd}}")
                 else:
                     req_Ag = (target_N - Ast*(fyd - fcd)) / fcd
                 
                 st.markdown(f"### Required Concrete: **{req_Ag:,.0f} mm²**")
