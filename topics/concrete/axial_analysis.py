import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.interpolate import make_interp_spline # For smooth curve drawing

# ======================================
# 1. HELPER: BAR DISTRIBUTION LOGIC
# ======================================
def distribute_bars_rectangular(b, h, cover, num_bars):
    eff_cover = cover 
    xL, xR = eff_cover, b - eff_cover
    yB, yT = eff_cover, h - eff_cover
    
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
# 2. HELPER: DRAWING FUNCTIONS (SECTION)
# ======================================
def draw_cross_section(shape, dims, num_bars, bar_dia, trans_type, show_ties, cover):
    fig, ax = plt.subplots(figsize=(4, 4))
    bar_r = bar_dia / 2
    draw_cover = cover
    fig.patch.set_alpha(0) 
    ax.patch.set_alpha(0)

    if shape in ["Rectangular", "Square"]:
        b, h = dims
        ax.add_patch(patches.Rectangle((0, 0), b, h, fill=True, facecolor='#e0e0e0', edgecolor='black', linewidth=2))
        ax.set_xlim(-50, b + 50)
        ax.set_ylim(-50, h + 50)
        
        if num_bars > 0:
            positions = distribute_bars_rectangular(b, h, draw_cover + bar_r, num_bars)
            if show_ties:
                tie_inset = draw_cover 
                ax.add_patch(patches.Rectangle((tie_inset, tie_inset), b-2*tie_inset, h-2*tie_inset, fill=False, edgecolor='#555', linewidth=1.5, linestyle='--'))
            for x, y in positions: ax.add_patch(patches.Circle((x, y), bar_r, color="#d32f2f", zorder=10))
            
    else:  # Circular
        D = dims[0]
        cx, cy = D / 2, D / 2
        ax.add_patch(patches.Circle((cx, cy), D/2, fill=True, facecolor='#e0e0e0', edgecolor='black', linewidth=2))
        
        if trans_type == "Spiral" and show_ties:
             core_D = D - 2*draw_cover
             ax.add_patch(patches.Circle((cx, cy), core_D/2, fill=False, edgecolor='#999', linestyle=':', label="Core Limit"))
        
        ax.set_xlim(-50, D + 50)
        ax.set_ylim(-50, D + 50)
        
        if num_bars > 0:
            angles = np.linspace(0, 2 * np.pi, num_bars, endpoint=False)
            r_bars = D/2 - draw_cover - bar_r
            positions = [(cx + r_bars * np.cos(a), cy + r_bars * np.sin(a)) for a in angles]
            if show_ties:
                linestyle = '-' if trans_type == "Spiral" else '--'
                r_tie = D/2 - draw_cover
                ax.add_patch(patches.Circle((cx, cy), r_tie, fill=False, edgecolor='#555', linewidth=1.5, linestyle=linestyle))
            for x, y in positions: ax.add_patch(patches.Circle((x, y), bar_r, color="#d32f2f", zorder=10))

    ax.set_aspect("equal")
    ax.axis("off")
    return fig

# ======================================
# 3. HELPER: LOAD-DEFORMATION GRAPH
# ======================================
def plot_load_deformation(N1, N2, trans_type):
    """
    Simulates the First Peak vs Second Peak behavior.
    """
    fig, ax = plt.subplots(figsize=(6, 4))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    
    # X-axis: Axial Shortening (Schematic 0 to 5)
    
    if trans_type == "Spiral":
        if N2 > N1:
            # Case: Confined Strength Gain (The graph you uploaded)
            x_points = np.array([0, 1, 2, 4])
            y_points = np.array([0, N1, 0.85*N1, N2]) # Rise, Dip (spall), Rise again
            
            # Annotations
            ax.annotate('First Peak ($N_{01}$)\n(Cover Spalling)', xy=(1, N1), xytext=(1.5, N1),
                        arrowprops=dict(facecolor='black', arrowstyle='->'))
            ax.annotate('Second Peak ($N_{02}$)\n(Core Failure)', xy=(4, N2), xytext=(2.5, N2),
                        arrowprops=dict(facecolor='black', arrowstyle='->'))
            
            # Dashed lines for peaks
            ax.axhline(y=N1, color='gray', linestyle='--', alpha=0.5)
            ax.axhline(y=N2, color='gray', linestyle='--', alpha=0.5)
            
        else:
            # Case: Confined Strength Loss (Dip and drop)
            x_points = np.array([0, 1, 2, 4])
            y_points = np.array([0, N1, 0.85*N1, N2]) 
            
            ax.annotate('First Peak ($N_{01}$)', xy=(1, N1), xytext=(1.5, N1+N1*0.1),
                        arrowprops=dict(facecolor='black', arrowstyle='->'))
            ax.annotate('Second Peak ($N_{02}$)\n(Spiral too weak)', xy=(4, N2), xytext=(2.5, N2+N2*0.1),
                        arrowprops=dict(facecolor='red', arrowstyle='->'))

    else: # Ties
        # Standard curve: Rise then Drop
        x_points = np.array([0, 1, 3])
        y_points = np.array([0, N1, 0.6*N1])
        ax.annotate('Failure ($N_{max}$)', xy=(1, N1), xytext=(1.5, N1),
                    arrowprops=dict(facecolor='black', arrowstyle='->'))

    # Smooth the curve
    X_Y_Spline = make_interp_spline(x_points, y_points)
    X_smooth = np.linspace(x_points.min(), x_points.max(), 200)
    Y_smooth = X_Y_Spline(X_smooth)

    ax.plot(X_smooth, Y_smooth, color="#1f77b4", linewidth=2.5)
    
    # Styling
    ax.set_xlabel(r"Axial Shortening ($\delta$)", fontsize=10)
    ax.set_ylabel("Axial Load (N)", fontsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylim(bottom=0)
    ax.set_xlim(left=0)
    
    return fig

# ======================================
# 4. MAIN APP
# ======================================
def app():

    solve_mode = st.radio(
        "Calculation Mode",
        ["Find Capacity", "Find Steel Area (Ast)", "Find Concrete Area (Ag)"],
        horizontal=True
    )
    st.markdown("---")

    col_input, col_viz = st.columns([1.3, 1])

    with col_input:
        st.subheader("1. Design Inputs")
        
        with st.expander("Code & Shape Settings", expanded=True):
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
                Ag = st.number_input("Gross Area ($A_g$) [mm²]", value=70650.0, step=1000.0)
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
        cover = st.number_input("Concrete Cover [mm]", value=25.0, min_value=15.0, step=5.0)

        spiral_dia = 8.0
        spiral_pitch = 100.0
        if "TS 500" in design_code and trans_type == "Spiral" and solve_mode == "Find Capacity":
            st.caption("Spiral Details")
            sc1, sc2 = st.columns(2)
            with sc1: spiral_dia = st.number_input("Spiral $\phi$ [mm]", value=8.0)
            with sc2: spiral_pitch = st.number_input("Pitch (s) [mm]", value=80.0)

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
            fig1 = draw_cross_section(shape, dims, bars_to_draw, bar_dia, trans_type, True, cover)
            st.pyplot(fig1)
            plt.close(fig1)
            if 'Ag' in locals() and Ag > 0: st.caption(f"$A_g$: {Ag:,.0f} mm² | Cover: {cover} mm")

    st.markdown("---")

    # ======================================
    # 5. CALCULATION REPORT
    # ======================================
    st.subheader("3. Calculation Report")
    
    if st.button("Run Calculation", type="primary"):
        is_ts500 = "TS 500" in design_code
        is_aci = "ACI" in design_code
        
        if is_aci:
            phi = 0.75 if trans_type == "Spiral" else 0.65
            alpha = 0.85 if trans_type == "Spiral" else 0.80
            st.write(f"**ACI Factors:** $\\phi={phi}, \\alpha={alpha}$")
        else:
            gamma_c, gamma_s = 1.5, 1.15
            fcd = fc / gamma_c
            fyd = fy / gamma_s
            c1, c2 = st.columns(2)
            with c1: st.latex(fr"f_{{cd}} = {fcd:.2f}\ MPa")
            with c2: st.latex(fr"f_{{yd}} = {fyd:.2f}\ MPa")

        if solve_mode == "Find Capacity":
            if is_aci:
                # ACI Logic
                P0_kN = (0.85 * fc * (Ag - Ast) + fy * Ast) / 1000
                Pn_max_kN = alpha * P0_kN
                PhiPn_kN = phi * Pn_max_kN
                
                st.markdown("**Step 1: Theoretical Peak ($P_0$)**")
                st.latex(r"P_0 = 0.85 f'_c (A_g - A_{st}) + f_y A_{st}")
                st.write(f"➝ $P_0$ = {P0_kN:,.0f} kN")
                st.markdown("**Step 2: Design Capacity**")
                st.latex(r"\phi P_{n,max} = \phi \cdot \alpha \cdot P_0")
                st.metric("Design Capacity", f"{PhiPn_kN:,.0f} kN")
                
            elif is_ts500:
                # TS 500 LOGIC
                # Peak 1 (Unconfined)
                Ac_gross_net = Ag - Ast
                Nor_kN = (0.85 * fcd * Ac_gross_net + Ast * fyd) / 1000
                
                # Setup comparison for graph
                graph_N1 = Nor_kN
                graph_N2 = 0 
                
                st.markdown("### Peak 1: Unconfined ($N_{or}$)")
                st.latex(r"N_{or} = 0.85 f_{cd} (A_g - A_{st}) + A_{st} f_{yd}")
                st.latex(fr"N_{{or}} = 0.85({fcd:.2f})({Ag:,.0f} - {Ast:,.0f}) + {Ast:,.0f}({fyd:.2f})")
                st.metric("First Peak", f"{Nor_kN:,.0f} kN")
                
                if trans_type == "Spiral":
                    st.markdown("---")
                    st.markdown("### Peak 2: Confined ($N_{or2}$)")
                    
                    D_col = dims[0]
                    D_core_outer = D_col - 2*cover
                    D_core_centerline = D_col - 2*(cover + spiral_dia/2)
                    Ack = np.pi * D_core_outer**2 / 4 
                    
                    Asp = np.pi * spiral_dia**2 / 4 
                    rho_s = (4 * Asp) / (D_core_centerline * spiral_pitch)
                    
                    # f_ccd
                    f_cc_char = 0.85 * fc + 2 * rho_s * fy
                    f_ccd = f_cc_char / 1.5
                    
                    # Capacity
                    Nor2_kN = (f_ccd * Ack + Ast * fyd) / 1000
                    graph_N2 = Nor2_kN
                    
                    st.write(f"**Spiral Ratio ($\\rho_s$):** {rho_s:.4f}")
                    st.latex(r"f_{ccd} = \frac{0.85 f_{ck} + 2 \rho_s f_{ywk}}{1.5}")
                    st.latex(r"N_{or2} = f_{ccd} A_{ck} + A_{st} f_{yd}")
                    
                    delta = Nor2_kN - Nor_kN
                    if delta > 0:
                        st.metric("Second Peak", f"{Nor2_kN:,.0f} kN", delta=f"+{delta:,.0f} kN (Gain)")
                        st.success("**Confined Behavior Achieved.**")
                    else:
                        st.metric("Second Peak", f"{Nor2_kN:,.0f} kN", delta=f"{delta:,.0f} kN (Loss)")
                        st.error("**Unconfined Governs.** Spiral weak.")
                    
                    # --- PLOT GRAPH ---
                    st.markdown("### Load-Deformation Behavior")
                    fig_graph = plot_load_deformation(graph_N1, graph_N2, "Spiral")
                    st.pyplot(fig_graph)
                    plt.close(fig_graph)

            else: 
                Nd_kN = (fcd * (Ag - Ast) + fyd * Ast) / 1000
                st.metric("Design Capacity", f"{Nd_kN:,.0f} kN")

        else:
             # Reverse Solvers (Keep existing logic)
             target_N = target_load * 1000
             if solve_mode == "Find Steel Area (Ast)":
                 if is_ts500:
                     num = target_N - 0.85 * fcd * Ag
                     den = fyd - 0.85 * fcd
                     req_Ast = num / den
                     st.latex(r"A_{st} = \frac{N_d - 0.85 f_{cd} A_g}{f_{yd} - 0.85 f_{cd}}")
                 else:
                     req_Ast = (target_N - fcd * Ag) / (fyd - fcd)
                 
                 if req_Ast < 0: st.error("Concrete is strong enough.")
                 else: st.markdown(f"### Required Steel: **{req_Ast:,.0f} mm²**")

             elif solve_mode == "Find Concrete Area (Ag)":
                 if is_ts500:
                     num = target_N - Ast * (fyd - 0.85*fcd)
                     den = 0.85 * fcd
                     req_Ag = num / den
                     st.latex(r"A_g = \frac{N_d - A_{st}(f_{yd} - 0.85 f_{cd})}{0.85 f_{cd}}")
                 else:
                     req_Ag = (target_N - Ast*(fyd - fcd)) / fcd
                 
                 st.markdown(f"### Required Concrete: **{req_Ag:,.0f} mm²**")
