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
        with st.expander(" Standards & Shape", expanded=True):
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
        factor_str = f"$f_{{cd}}={fcd:.2f}, f_{{yd}}={fyd:.2f}$"
    elif "ACI" in code:
        phi = 0.75 if trans_type == "Spiral" else 0.65
        alpha = 0.85 if trans_type == "Spiral" else 0.80
        factor_str = f"$\\phi={phi}, \\alpha={alpha}$"
    else: # EC2
        fcd = 0.85 * fc / 1.5
        fyd = fy / 1.15
        factor_str = "EC2 Factors"

    # RUN DESIGN
    req_Ast = 0
    req_Ag = 0
    
    with col2:
        st.subheader("2. Results")
        
        # --- CASE A: FIND STEEL ---
        if design_mode == "Required Reinforcement (Ast)":
            st.markdown(f"**Target:** Carry {Nd:,.0f} kN with given size.")
            
            if "TS 500" in code:
                # Nd = 0.85 * fcd * (Ag - Ast) + Ast * fyd
                # Nd = 0.85 fcd Ag + Ast (fyd - 0.85 fcd)
                term1 = 0.85 * fcd * Ag
                term2 = fyd - 0.85 * fcd
                req_Ast = (Nd * 1000 - term1) / term2
                
            elif "ACI" in code:
                # Pu = phi * alpha * [0.85 fc (Ag - Ast) + Ast fy]
                Pn = (Nd * 1000) / (phi * alpha)
                term1 = 0.85 * fc * Ag
                term2 = fy - 0.85 * fc
                req_Ast = (Pn - term1) / term2
                
            else: # EC2
                req_Ast = (Nd * 1000 - fcd * Ag) / (fyd - fcd)

            # --- OUTPUT & CHECKS ---
            
            # 1. Negative result -> Concrete strong enough -> Use Min Steel
            if req_Ast <= 0:
                st.success(" **Concrete is strong enough!**")
                st.info("Using Minimum Reinforcement (1%):")
                req_Ast = 0.01 * Ag
                st.metric("Required Steel ($A_{st,min}$)", f"{req_Ast:,.0f} mm²")
            
            # 2. Positive Result -> Check Min/Max
            else:
                rho = req_Ast / Ag
                
                # Check for Min Steel (1% for TS 500)
                if rho < 0.01:
                    st.warning(f"⚠️ Calculated $\\rho = {rho*100:.2f}\\%$ (< 1% Min).")
                    st.info("Increasing to Minimum Reinforcement (1%):")
                    req_Ast = 0.01 * Ag
                    rho = 0.01 # Update for display
                    st.metric("Required Steel ($A_{st,min}$)", f"{req_Ast:,.0f} mm²")
                    st.success(f"Final $\\rho = {rho*100:.2f}\\%$ (OK)")
                
                # Check for Max Steel (4%)
                elif rho > 0.04:
                    st.error(f"**Required Steel ($A_{{st}}$): {req_Ast:,.0f} mm²**")
                    st.warning(f"⚠️ $\\rho = {rho*100:.2f}\\%$ (> 4% Max! Increase Section)")
                
                # OK Range
                else:
                    st.success(f"**Required Steel ($A_{{st}}$): {req_Ast:,.0f} mm²**")
                    st.success(f"$\\rho = {rho*100:.2f}\\%$ (OK)")

            # --- BAR SUGGESTIONS ---
            st.markdown("###  Suggested Bars")
            suggestions = suggest_reinforcement(req_Ast, shape)
            if suggestions:
                # Pick the first one for visualization
                best_opt = suggestions[0]
                n_viz, db_viz, area_viz = best_opt
                
                for n, db, area in suggestions:
                    st.write(f"- **{n} $\phi$ {db}** ($A_s = {area:.0f}$ mm²)")
                
                # Draw
                st.pyplot(draw_design_section(shape, dims, n_viz, db_viz, trans_type, cover))
            else:
                st.warning("Amount of steel is too high for standard bars.")

        # --- CASE B: FIND CONCRETE ---
        else:
            st.markdown(f"**Target:** Carry {Nd:,.0f} kN with $\\rho \\approx {rho_guess*100}\\%$")
            
            # Substitute Ast = rho * Ag into equation
            # TS500: Nd = 0.85 fcd (Ag - rho Ag) + rho Ag fyd
            # Nd = Ag [ 0.85 fcd (1-rho) + rho fyd ]
            
            if "TS 500" in code:
                bracket = 0.85 * fcd * (1 - rho_guess) + rho_guess * fyd
                req_Ag = (Nd * 1000) / bracket
                
            elif "ACI" in code:
                # Pu = phi * alpha * Ag * [0.85 fc (1-rho) + rho fy]
                Pn = (Nd * 1000) / (phi * alpha)
                bracket = 0.85 * fc * (1 - rho_guess) + rho_guess * fy
                req_Ag = Pn / bracket
            
            st.success(f"**Required Area ($A_g$): {req_Ag:,.0f} mm²**")
            
            # Suggest Dimensions
            if shape == "Circular":
                req_D = np.sqrt(4 * req_Ag / np.pi)
                st.metric("Suggested Diameter", f"{req_D:.0f} mm")
                dims = (req_D,)
            else:
                req_side = np.sqrt(req_Ag)
                st.metric("Suggested Square Side", f"{req_side:.0f} mm")
                dims = (req_side, req_side)
                
            # Viz Placeholder
            st.pyplot(draw_design_section(shape, dims, 0, 0, trans_type, cover))

    # --- SPIRAL CHECK (TS 500) ---
    if "TS 500" in code and trans_type == "Spiral" and shape == "Circular":
        st.markdown("---")
        st.subheader(" Spiral Detailing (TS 500)")
        
        # Need Core Diameter
        D_col = dims[0]
        # Use Outer Core Diameter for ratio calculation per slides
        d_core_outer = D_col - 2*cover
        # Use Centerline for volumetric ratio check if strictly following formula derivation,
        # but TS 500 usually references Ack (core area).
        # Let's stick to the Example 1d logic: Ratio = 4 * Asp / (D_core * s)
        # where D_core is outer-to-outer (Ack diameter).
        
        Ach = np.pi * d_core_outer**2 / 4
        Ag_real = np.pi * D_col**2 / 4
        
        # Min Volumetric Ratio Formula
        rho_min = 0.45 * (fc / fy) * ((Ag_real / Ach) - 1)
        # Floor min is 0.12 * fc/fy
        rho_min_floor = 0.12 * (fc / fy)
        final_rho_min = max(rho_min, rho_min_floor)
        
        st.write(f"**Minimum Spiral Ratio ($\\rho_{{s,min}}$):** {final_rho_min:.4f}")
        
        st.markdown("**Suggested Spacing ($s$) for common spiral sizes:**")
        
        c1, c2 = st.columns(2)
        for d_sp in [8, 10, 12]:
            Asp = np.pi * d_sp**2 / 4
            # rho = 4 * Asp / (d_core * s)  ->  s = 4 * Asp / (d_core * rho_min)
            req_s = (4 * Asp) / (d_core_outer * final_rho_min)
            
            # Code Limit s_max
            # TS500: s <= D/5 and s <= 80mm (Conservative)
            s_max = min(80, D_col/5) 
            
            valid = "Valid" if req_s < s_max else "⚠️ (Too large/impractical)"
            st.write(f"- **$\phi${d_sp} Spiral:** s $\le$ **{req_s:.0f} mm**")
