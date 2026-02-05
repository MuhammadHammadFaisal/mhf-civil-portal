import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- SAFE IMPORT FOR CURVE SMOOTHING ---
try:
    from scipy.interpolate import PchipInterpolator
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

# ======================================
# 1. HELPER: DRAWING FUNCTIONS
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

def draw_cross_section(shape, dims, num_bars, bar_dia, trans_type, show_ties, cover):
    fig, ax = plt.subplots(figsize=(4, 4))
    bar_r = bar_dia / 2
    draw_cover = cover
    
    fig.patch.set_alpha(0); ax.patch.set_alpha(0)

    if shape in ["Rectangular", "Square"]:
        b, h = dims
        ax.add_patch(patches.Rectangle((0, 0), b, h, fill=True, facecolor='#e0e0e0', edgecolor='black', linewidth=2))
        ax.set_xlim(-50, b + 50); ax.set_ylim(-50, h + 50)
        
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
             # Spiral calculation usually uses centerline, but visualization looks better with slight inset
             # We assume spiral diameter is small relative to D
             spiral_dia_viz = 10 # approximate for drawing
             core_D = D - 2*draw_cover
             ax.add_patch(patches.Circle((cx, cy), core_D/2, fill=False, edgecolor='#999', linestyle=':', label="Core Limit"))
        
        ax.set_xlim(-50, D + 50); ax.set_ylim(-50, D + 50)
        
        if num_bars > 0:
            angles = np.linspace(0, 2 * np.pi, num_bars, endpoint=False)
            r_bars = D/2 - draw_cover - bar_r
            positions = [(cx + r_bars * np.cos(a), cy + r_bars * np.sin(a)) for a in angles]
            if show_ties:
                linestyle = '-' if trans_type == "Spiral" else '--'
                r_tie = D/2 - draw_cover
                ax.add_patch(patches.Circle((cx, cy), r_tie, fill=False, edgecolor='#555', linewidth=1.5, linestyle=linestyle))
            for x, y in positions: ax.add_patch(patches.Circle((x, y), bar_r, color="#d32f2f", zorder=10))

    ax.set_aspect("equal"); ax.axis("off")
    return fig

# ======================================
# 2. PLOT: LOAD vs DEFORMATION
# ======================================
def plot_load_deformation(N1, N2, trans_type):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    
    # --- STYLING FOR DARK MODE ---
    text_color = "white"
    ax.spines['bottom'].set_color(text_color)
    ax.spines['left'].set_color(text_color)
    ax.spines['top'].set_visible(False); ax.spines['right'].set_visible(False)
    ax.tick_params(axis='x', colors=text_color)
    ax.tick_params(axis='y', colors=text_color)
    ax.yaxis.label.set_color(text_color)
    ax.xaxis.label.set_color(text_color)

    if trans_type == "Spiral":
        if N2 > N1:
            x = np.array([0, 1.0, 2.0, 3.5, 5.5, 6.5]) 
            y = np.array([0, N1,  0.85*N1, N2, N2, N2*0.9]) 
            color = "#00BFFF" 
            ax.annotate('First Peak\n(Shell Spalls)', xy=(1.0, N1), xytext=(0.5, N1+N1*0.1),
                        arrowprops=dict(facecolor=text_color, arrowstyle='->'), ha='center', color=text_color)
            ax.annotate('Second Peak\n(Confined Core)', xy=(3.5, N2), xytext=(3.5, N2+N2*0.1),
                        arrowprops=dict(facecolor=text_color, arrowstyle='->'), ha='center', color=text_color)
            ax.annotate('Ductile Plateau', xy=(5.5, N2), xytext=(5.5, N2-N2*0.15),
                        arrowprops=dict(facecolor=text_color, arrowstyle='->'), ha='center', color=text_color)
            ax.axhline(y=N1, color='gray', linestyle='--', alpha=0.5)
        else:
            x = np.array([0, 1.0, 2.0, 3.5, 5.0])
            y = np.array([0, N1,  0.80*N1, N2, N2*0.8]) 
            color = "#FF4B4B" 
            ax.annotate('First Peak\n(Governs)', xy=(1.0, N1), xytext=(1.5, N1+N1*0.15),
                        arrowprops=dict(facecolor=text_color, arrowstyle='->'), color=text_color)
            ax.annotate('Spiral too weak', xy=(3.5, N2), xytext=(3.5, N2+N2*0.15),
                        arrowprops=dict(facecolor=text_color, arrowstyle='->'), ha='center', color=text_color)
    else: 
        x = np.array([0, 1.0, 2.5, 4.0])
        y = np.array([0, N1, 0.5*N1, 0.3*N1])
        color = "#FFA500" 
        ax.annotate('Failure ($N_{max}$)', xy=(1.0, N1), xytext=(1.5, N1),
                    arrowprops=dict(facecolor=text_color, arrowstyle='->'), color=text_color)

    if HAS_SCIPY:
        try:
            interpolator = PchipInterpolator(x, y)
            x_smooth = np.linspace(x.min(), x.max(), 300)
            y_smooth = interpolator(x_smooth)
            ax.plot(x_smooth, y_smooth, color=color, linewidth=3)
        except:
            ax.plot(x, y, color=color, linewidth=3)
    else:
        ax.plot(x, y, color=color, linewidth=3, linestyle='-')
    
    ax.set_xlabel(r"Axial Shortening ($\delta$)", fontsize=11)
    ax.set_ylabel("Axial Load (N)", fontsize=11)
    ax.set_ylim(bottom=0, top=max(N1, N2)*1.3)
    ax.set_xlim(left=0)
    return fig

# ======================================
# 3. MAIN APP
# ======================================
def app():

    col_input, col_viz = st.columns([1.3, 1])

    with col_input:
        st.subheader("1. System Properties")
        with st.expander("Code & Geometry", expanded=True):
            design_code = st.selectbox("Design Code", ["TS 500 (Lecture Notes)", "ACI 318-19", "Eurocode 2"])
            shape = st.selectbox("Column Shape", ["Rectangular", "Square", "Circular"])
            
            trans_type = "Ties"
            if shape == "Circular":
                trans_type = st.radio("Confinement", ["Circular Ties", "Spiral"])

        st.markdown("**Materials**")
        c1, c2 = st.columns(2)
        with c1: fc = st.number_input("Concrete ($f_{ck}$/$f'_c$) [MPa]", value=20.0, step=5.0)
        with c2: fy = st.number_input("Steel ($f_{yk}$/$f_y$) [MPa]", value=420.0, step=10.0)

        st.markdown("**Dimensions**")
        cover = st.number_input("Cover [mm]", value=25.0)
        
        Ag = 0; dims = (0,0)
        if shape == "Rectangular":
            cc1, cc2 = st.columns(2)
            with cc1: b = st.number_input("Width (b) [mm]", value=300.0)
            with cc2: h = st.number_input("Depth (h) [mm]", value=400.0)
            Ag = b*h; dims = (b, h)
        elif shape == "Square":
            a = st.number_input("Side (a) [mm]", value=350.0)
            Ag = a**2; dims = (a, a)
        else: 
            D = st.number_input("Diameter (D) [mm]", value=300.0)
            Ag = np.pi * D**2 / 4; dims = (D,)

        st.markdown("**Longitudinal Reinforcement**")
        rc1, rc2 = st.columns(2)
        with rc1: bar_dia = st.number_input("Bar Dia [mm]", value=16.0, step=2.0)
        with rc2: num_bars = st.number_input("Total Bars", value=8, min_value=4)
        Ast = num_bars * np.pi * (bar_dia / 2) ** 2
        
        # Spiral Inputs
        spiral_dia = 8.0
        spiral_spacing = 80.0
        if "TS 500" in design_code and trans_type == "Spiral":
            st.markdown("**Spiral Reinforcement**")
            sc1, sc2 = st.columns(2)
            with sc1: spiral_dia = st.number_input("Spiral $\phi$ [mm]", value=8.0)
            with sc2: spiral_spacing = st.number_input("Spacing (s) [mm]", value=80.0)

    with col_viz:
        st.subheader("2. Visualization")
        fig1 = draw_cross_section(shape, dims, num_bars, bar_dia, trans_type, True, cover)
        st.pyplot(fig1)
        plt.close(fig1)
        st.caption(f"**Section Data:** $A_g = {Ag:,.0f}$ mm², $\\rho = {(Ast/Ag)*100:.2f}\\%$")

    st.markdown("---")

    # ======================================
    # 4. CALCULATION REPORT
    # ======================================
    st.subheader("3. Calculation Report")
    
    if st.button("Analyze Capacity", type="primary"):
        st.markdown("#### Step-by-Step Analysis")
        
        # --- CONSTANTS ---
        if "TS 500" in design_code:
            gamma_c, gamma_s = 1.5, 1.15
            fcd = fc / gamma_c
            fyd = fy / gamma_s
            st.write("**Material Design Strengths:**")
            st.latex(fr"f_{{cd}} = {fc}/{gamma_c} = {fcd:.2f} \text{{ MPa}}")
            st.latex(fr"f_{{yd}} = {fy}/{gamma_s} = {fyd:.2f} \text{{ MPa}}")
            
        elif "ACI" in design_code:
            # Check for spiral vs tied
            phi = 0.75 if trans_type == "Spiral" else 0.65
            alpha = 0.85 if trans_type == "Spiral" else 0.80
            st.write(f"**ACI Factors:** $\\phi={phi}, \\alpha={alpha}$")

        # --- ACI ANALYSIS ---
        if "ACI" in design_code:
            P0 = 0.85 * fc * (Ag - Ast) + fy * Ast
            Pn_max = alpha * P0
            PhiPn = phi * Pn_max
            
            st.markdown("### ACI Capacity")
            st.latex(r"\phi P_{n,max} = \phi \cdot \alpha [0.85 f'_c (A_g - A_{st}) + f_y A_{st}]")
            term_conc = f"0.85({fc})({Ag:.0f}-{Ast:.0f})"
            term_steel = f"{fy}({Ast:.0f})"
            st.latex(fr"\phi P_{{n}} = {phi} \cdot {alpha} [{term_conc} + {term_steel}]")
            st.metric("Design Capacity ($\phi P_n$)", f"{PhiPn/1000:,.0f} kN")

        # --- TS 500 ANALYSIS (Detailed) ---
        elif "TS 500" in design_code:
            # 1. Unconfined
            st.markdown("### Peak 1: Unconfined Capacity ($N_{or}$)")
            term_conc = 0.85 * fcd * (Ag - Ast)
            term_steel = Ast * fyd
            Nor1 = term_conc + term_steel
            
            st.latex(r"N_{or} = 0.85 f_{cd} (A_g - A_{st}) + A_{st} f_{yd}")
            st.latex(fr"N_{{or}} = 0.85({fcd:.2f})({Ag:.0f} - {Ast:.0f}) + {Ast:.0f}({fyd:.2f}) = \mathbf{{{Nor1/1000:.0f} \text{{ kN}}}}")
            
            graph_N1 = Nor1 / 1000
            graph_N2 = 0
            
            if trans_type == "Spiral":
                st.markdown("---")
                st.markdown("### Peak 2: Confined Capacity ($N_{or2}$)")
                
                # --- FIXED VARIABLES HERE ---
                D_col = dims[0]
                d_core_outer = D_col - 2*cover
                d_core_center = D_col - 2*(cover + spiral_dia/2)
                
                Ack = np.pi * d_core_outer**2 / 4 
                Asp = np.pi * spiral_dia**2 / 4
                
                rho_s = (4 * Asp) / (d_core_center * spiral_spacing)
                
                c1, c2 = st.columns(2)
                c1.write(f"Core Dia (Centerline): **{d_core_center:.1f} mm**")
                c2.write(f"Spiral Ratio ($\\rho_s$): **{rho_s:.4f}**")
                
                rho_min_calc = 0.45 * (fc/fy) * ((Ag/Ack)-1)
                rho_min_abs = 0.12 * (fc/fy)
                rho_min_req = max(rho_min_calc, rho_min_abs)
                
                if rho_s < rho_min_req:
                    st.error(f"⚠️ $\\rho_s$ ({rho_s:.4f}) < Min ({rho_min_req:.4f}). Second peak will not develop!")
                else:
                    st.success(f"✅ $\\rho_s$ ({rho_s:.4f}) > Min ({rho_min_req:.4f})")

                f_cc_char = 0.85 * fc + 2 * rho_s * fy
                f_ccd = f_cc_char / 1.5
                st.latex(fr"f_{{ccd}} = \frac{{0.85({fc}) + 2({rho_s:.4f})({fy})}}{{1.5}} = \mathbf{{{f_ccd:.2f} \text{{ MPa}}}}")
                
                term_core = f_ccd * Ack
                term_steel_2 = Ast * fyd
                Nor2 = term_core + term_steel_2
                
                st.latex(r"N_{or2} = f_{ccd} A_{ck} + A_{st} f_{yd}")
                st.latex(fr"N_{{or2}} = {f_ccd:.2f}({Ack:.0f}) + {Ast:.0f}({fyd:.2f}) = \mathbf{{{Nor2/1000:.0f} \text{{ kN}}}}")
                
                graph_N2 = Nor2 / 1000
                delta = graph_N2 - graph_N1
                
                if delta > 0:
                    st.success(f"**Confined Peak is Higher.** Gain = +{delta:.0f} kN.")
                else:
                    st.warning(f"⚠️ **Unconfined Peak Governs.** Loss = {delta:.0f} kN.")

            st.markdown("### Load-Deformation Behavior")
            fig = plot_load_deformation(graph_N1, graph_N2, trans_type)
            st.pyplot(fig)
            plt.close(fig)
            
        else:
            st.info("Eurocode detailed substitution not implemented in this view.")
