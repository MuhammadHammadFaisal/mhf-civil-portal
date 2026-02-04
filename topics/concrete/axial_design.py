import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ======================================
# 1. HELPER: SUGGEST BARS
# ======================================
def suggest_reinforcement(required_Ast, shape):
    """
    Suggests real bar configurations based on required area.
    """
    bar_opts = [14, 16, 20, 25, 32]
    suggestions = []
    
    min_bars = 6 if shape == "Circular" else 4
    
    for db in bar_opts:
        ab = np.pi * db**2 / 4
        n_req = int(np.ceil(required_Ast / ab))
        
        # Enforce minimums
        if n_req < min_bars: n_req = min_bars
        
        # Enforce even numbers for rect (usually preferred)
        if shape != "Circular" and n_req % 2 != 0:
            n_req += 1
            
        total_area = n_req * ab
        # Filter: Don't suggest if it's way too much steel (>25% extra)
        if total_area < required_Ast * 1.5:
            suggestions.append((n_req, db, total_area))
            
    return suggestions

# ======================================
# 2. HELPER: DRAWING (SIMPLIFIED FOR DESIGN)
# ======================================
def draw_design_section(shape, dims, n_bars, db, trans_type, cover):
    fig, ax = plt.subplots(figsize=(4, 4))
    fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    
    # Draw Concrete
    if shape in ["Rectangular", "Square"]:
        b, h = dims
        ax.add_patch(patches.Rectangle((0, 0), b, h, facecolor='#e0e0e0', edgecolor='black', lw=2))
        ax.set_xlim(-50, b+50); ax.set_ylim(-50, h+50)
        
        # Draw Ties
        tie_x = cover; tie_y = cover
        ax.add_patch(patches.Rectangle((tie_x, tie_y), b-2*cover, h-2*cover, fill=False, edgecolor='#555', linestyle='--'))
        
        # Draw Bars (Simple distribution)
        if n_bars > 0:
            # 4 Corners
            bars = [(cover, cover), (b-cover, cover), (b-cover, h-cover), (cover, h-cover)]
            # Remaining
            rem = n_bars - 4
            if rem > 0:
                # Add equally to vertical sides for simplicity in viz
                spacing_y = (h - 2*cover) / (rem//2 + 1)
                for i in range(rem//2):
                    y = cover + spacing_y*(i+1)
                    bars.append((cover, y))
                    bars.append((b-cover, y))
            
            for (bx, by) in bars:
                ax.add_patch(patches.Circle((bx, by), db/2, color='#d32f2f'))

    else: # Circular
        D = dims[0]
        cx, cy = D/2, D/2
        ax.add_patch(patches.Circle((cx, cy), D/2, facecolor='#e0e0e0', edgecolor='black', lw=2))
        ax.set_xlim(-50, D+50); ax.set_ylim(-50, D+50)
        
        # Spiral/Tie
        r_tie = D/2 - cover
        style = '-' if trans_type == "Spiral" else '--'
        ax.add_patch(patches.Circle((cx, cy), r_tie, fill=False, edgecolor='#555', linestyle=style))
        
        # Bars
        if n_bars > 0:
            r_bar = D/2 - cover - db/2 # Center of bar
            for i in range(n_bars):
                angle = 2*np.pi * i / n_bars
                bx = cx + r_bar * np.cos(angle)
                by = cy + r_bar * np.sin(angle)
                ax.add_patch(patches.Circle((bx, by), db/2, color='#d32f2f'))

    ax.set_aspect('equal'); ax.axis('off')
    return fig

# ======================================
# 3. MAIN APP
# ======================================
def app():
    st.header("📐 Design of Axial Members")
    st.markdown("---")

    # 1. DESIGN GOAL
    design_mode = st.radio("What are you solving for?", 
                           ["Required Reinforcement (Ast)", "Required Concrete Area (Ag)"], horizontal=True)

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("1. Parameters")
        with st.expander("⚙️ Standards & Shape", expanded=True):
            code = st.selectbox("Design Code", ["TS 500 (Lecture Notes)", "ACI 318-19", "Eurocode 2"])
            shape = st.selectbox("Column Shape", ["Rectangular", "Square", "Circular"])
            
            trans_type = "Ties"
            if shape == "Circular":
                trans_type = st.radio("Confinement", ["Circular Ties", "Spiral"])

        st.markdown("**Loads & Materials**")
        Nd = st.number_input("Design Axial Load ($N_d$) [kN]", value=2000.0, step=50.0)
        fc = st.number_input("Concrete ($f_{ck}$/$f'_c$) [MPa]", value=25.0)
        fy = st.number_input("Steel ($f_{yk}$/$f_y$) [MPa]", value=420.0)
        
        st.markdown("**Geometry**")
        cover = st.number_input("Cover [mm]", value=25.0)
        
        Ag = 0; dims = (0,0)
        if design_mode == "Required Reinforcement (Ast)":
            if shape == "Rectangular":
                b = st.number_input("Width (b) [mm]", value=300.0)
                h = st.number_input("Depth (h) [mm]", value=400.0)
                Ag = b*h; dims = (b, h)
            elif shape == "Square":
                a = st.number_input("Side (a) [mm]", value=350.0)
                Ag = a**2; dims = (a, a)
            else:
                D = st.number_input("Diameter (D) [mm]", value=400.0)
                Ag = np.pi * D**2 / 4; dims = (D,)
        else:
            st.info("Dimensions will be calculated.")
            # Assume min steel ratio for initial guess if finding Ag
            rho_guess = st.slider("Assumed Steel Ratio ($\\rho$)", 0.01, 0.04, 0.015, format="%.3f")

    # --- CALCULATION LOGIC ---
    # Factors
    if "TS 500" in code:
        gamma_c, gamma_s = 1.5, 1.15
        fcd = fc / gamma_c
        fyd = fy / gamma_s
        # factor_str is used in rendering
    elif "ACI" in code:
        phi = 0.75 if trans_type == "Spiral" else 0.65
        alpha = 0.85 if trans_type == "Spiral" else 0.80
    else: # EC2
        fcd = 0.85 * fc / 1.5
        fyd = fy / 1.15

    # RUN DESIGN
    req_Ast = 0
    req_Ag = 0
    
    with col2:
        st.subheader("2. Results")
        
        if st.button("Run Design Calculation", type="primary"):
            st.markdown("#### 📝 Step-by-Step Substitution")
            
            # --- SHOW MATERIAL STRENGTHS ---
            if "ACI" in code:
                st.write(f"**Factors:** $\\phi={phi}, \\alpha={alpha}$")
            else:
                st.write(f"**Design Strengths:**")
                st.latex(fr"f_{{cd}} = {fc}/{gamma_c} = {fcd:.2f} \text{{ MPa}}")
                st.latex(fr"f_{{yd}} = {fy}/{gamma_s} = {fyd:.2f} \text{{ MPa}}")

            # --- CASE A: FIND STEEL ---
            if design_mode == "Required Reinforcement (Ast)":
                
                if "TS 500" in code:
                    # Formula: Ast = (Nd - 0.85 fcd Ag) / (fyd - 0.85 fcd)
                    term_load = Nd * 1000
                    term_conc_cap = 0.85 * fcd * Ag
                    denom = fyd - 0.85 * fcd
                    
                    calc_Ast = (term_load - term_conc_cap) / denom
                    
                    st.markdown("**1. Formula:**")
                    st.latex(r"A_{st} = \frac{N_d - 0.85 f_{cd} A_g}{f_{yd} - 0.85 f_{cd}}")
                    
                    st.markdown("**2. Substitution:**")
                    num_str = fr"{term_load:.0f} - 0.85({fcd:.2f})({Ag:.0f})"
                    den_str = fr"{fyd:.2f} - 0.85({fcd:.2f})"
                    st.latex(fr"A_{{st}} = \frac{{{num_str}}}{{{den_str}}}")
                    
                elif "ACI" in code:
                    # Convert Pu to Pn
                    Pn = (Nd * 1000) / (phi * alpha)
                    
                    st.markdown("**1. Convert Design Load to Nominal:**")
                    st.latex(fr"P_n = \frac{{P_u}}{{\phi \alpha}} = \frac{{{Nd * 1000:.0f}}}{{{phi} \cdot {alpha}}} = {Pn:.0f} \text{{ N}}")
                    
                    # Formula: Ast = (Pn - 0.85 fc Ag) / (fy - 0.85 fc)
                    term_conc_cap = 0.85 * fc * Ag
                    denom = fy - 0.85 * fc
                    calc_Ast = (Pn - term_conc_cap) / denom
                    
                    st.markdown("**2. Solve for Steel:**")
                    st.latex(r"A_{st} = \frac{P_n - 0.85 f'_c A_g}{f_y - 0.85 f'_c}")
                    st.latex(fr"A_{{st}} = \frac{{{Pn:.0f} - 0.85({fc})({Ag:.0f})}}{{{fy} - 0.85({fc})}}")

                else: # EC2
                    calc_Ast = (Nd * 1000 - fcd * Ag) / (fyd - fcd)
                    st.latex(r"A_{s} = \frac{N_{Ed} - f_{cd} A_c}{f_{yd} - f_{cd}}")

                # --- CHECK RESULT ---
                if calc_Ast <= 0:
                    st.markdown("### Result Analysis")
                    st.info(f"Calculated $A_{{st}}$ is negative ({calc_Ast:.0f} mm²).")
                    st.write("This means **Concrete alone is stronger than the load**.")
                    st.latex(fr"N_{{conc}} = 0.85 f_{{cd}} A_g = {0.85*fcd*Ag/1000:.0f} \text{{ kN}} > {Nd:.0f} \text{{ kN}}")
                    
                    st.warning("⚠️ **Action:** Use Minimum Reinforcement.")
                    req_Ast = 0.01 * Ag
                    st.metric("Min Reinforcement (1%)", f"{req_Ast:,.0f} mm²")
                    
                else:
                    rho = calc_Ast / Ag
                    st.markdown(f"**Calculated Area:** {calc_Ast:.0f} mm² ($\\rho={rho*100:.2f}\\%$)")
                    
                    # Enforce Min/Max
                    if rho < 0.01:
                        st.warning(f"⚠️ Calculated $\\rho < 1\%$. Increasing to minimum.")
                        req_Ast = 0.01 * Ag
                        st.metric("Final Required Steel (Min 1%)", f"{req_Ast:,.0f} mm²")
                    elif rho > 0.04:
                        st.error(f"⚠️ $\\rho = {rho*100:.2f}\\%$ (> 4% Max). Section is too small!")
                        req_Ast = calc_Ast
                    else:
                        st.success(f"✅ $\\rho$ is within limits (1-4%).")
                        req_Ast = calc_Ast
                        st.metric("Required Steel", f"{req_Ast:,.0f} mm²")

                # --- BAR SUGGESTIONS ---
                st.markdown("---")
                st.markdown("### 🛠️ Suggested Bars")
                suggestions = suggest_reinforcement(req_Ast, shape)
                if suggestions:
                    best_opt = suggestions[0]
                    n_viz, db_viz, area_viz = best_opt
                    for n, db, area in suggestions:
                        st.write(f"- **{n} $\phi$ {db}** ($A_s = {area:.0f}$ mm²)")
                    st.pyplot(draw_design_section(shape, dims, n_viz, db_viz, trans_type, cover))
                else:
                    st.warning("Steel demand too high for standard bars.")

            # --- CASE B: FIND CONCRETE ---
            else:
                st.markdown(f"**Target:** Carry {Nd:,.0f} kN with $\\rho \\approx {rho_guess*100}\\%$")
                
                if "TS 500" in code:
                    # Nd = Ag [ 0.85 fcd (1-rho) + rho fyd ]
                    bracket = 0.85 * fcd * (1 - rho_guess) + rho_guess * fyd
                    req_Ag = (Nd * 1000) / bracket
                    
                    st.latex(r"A_g = \frac{N_d}{0.85 f_{cd} (1-\rho) + \rho f_{yd}}")
                    st.latex(fr"A_g = \frac{{{Nd*1000:.0f}}}{{0.85({fcd:.2f})(1-{rho_guess}) + {rho_guess}({fyd:.2f})}}")
                    
                elif "ACI" in code:
                    Pn = (Nd * 1000) / (phi * alpha)
                    bracket = 0.85 * fc * (1 - rho_guess) + rho_guess * fy
                    req_Ag = Pn / bracket
                    st.latex(r"A_g = \frac{P_n}{0.85 f'_c (1-\rho) + \rho f_y}")
                
                st.metric("Required Concrete Area", f"{req_Ag:,.0f} mm²")
                
                # Suggest Dimensions
                if shape == "Circular":
                    req_D = np.sqrt(4 * req_Ag / np.pi)
                    st.write(f"➝ Min Diameter: **{req_D:.0f} mm**")
                    dims = (req_D,)
                else:
                    req_side = np.sqrt(req_Ag)
                    st.write(f"➝ Min Square Side: **{req_side:.0f} mm**")
                    dims = (req_side, req_side)
                    
                st.pyplot(draw_design_section(shape, dims, 0, 0, trans_type, cover))

        # --- SPIRAL CHECK (TS 500) ---
        if "TS 500" in code and trans_type == "Spiral" and shape == "Circular":
            st.markdown("---")
            st.subheader("🌀 Spiral Detailing (TS 500)")
            
            D_col = dims[0]
            if D_col > 0:
                d_core_outer = D_col - 2*cover
                Ach = np.pi * d_core_outer**2 / 4
                Ag_real = np.pi * D_col**2 / 4
                
                rho_min = 0.45 * (fc / fy) * ((Ag_real / Ach) - 1)
                rho_min_floor = 0.12 * (fc / fy)
                final_rho_min = max(rho_min, rho_min_floor)
                
                st.latex(r"\rho_{s,min} = \max \left( 0.45 \frac{f_{ck}}{f_{yk}} (\frac{A_c}{A_{ck}}-1) , \ 0.12 \frac{f_{ck}}{f_{yk}} \right)")
                st.write(f"**Required Volumetric Ratio:** {final_rho_min:.4f}")
                
                st.markdown("**Max Spacing ($s_{max}$):**")
                s_max_code = min(80, D_col/5)
                st.write(f"Min(80mm, D/5) = **{s_max_code:.0f} mm**")
                
                st.markdown("**Suggested Spiral Spacing:**")
                c1, c2 = st.columns(2)
                for d_sp in [8, 10, 12]:
                    Asp = np.pi * d_sp**2 / 4
                    # s = 4 * Asp / (d_core * rho_min)
                    req_s = (4 * Asp) / (d_core_outer * final_rho_min)
                    
                    if req_s < 40:
                        st.write(f"- $\phi${d_sp}: **Too Tight (<40mm)**")
                    elif req_s > s_max_code:
                        st.write(f"- $\phi${d_sp}: Limit to **{s_max_code:.0f} mm**")
                    else:
                        st.write(f"- $\phi${d_sp}: Use **{req_s:.0f} mm**")
