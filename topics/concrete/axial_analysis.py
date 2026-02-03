import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ======================================
# 1. HELPER: BAR DISTRIBUTION LOGIC
# ======================================
def distribute_bars_rectangular(b, h, cover, num_bars):
    """
    Distributes bars for a rectangular section.
    Always places 4 corner bars, then distributes the rest 
    prioritizing the longer faces.
    """
    xL, xR = cover, b - cover
    yB, yT = cover, h - cover

    # Always start with 4 corner bars
    positions = [
        (xL, yB), (xR, yB),
        (xR, yT), (xL, yT)
    ]

    remaining = num_bars - 4
    if remaining <= 0:
        return positions[:num_bars] # Return valid if num_bars < 4 (edge case)

    # Determine face priority (longer faces get bars first)
    # Each 'face' is defined by: (name, fixed_coord, range_start, range_end)
    if h >= b:
        faces = [
            ("left", xL, yB, yT),
            ("right", xR, yB, yT),
            ("bottom", yB, xL, xR),
            ("top", yT, xL, xR),
        ]
    else:
        faces = [
            ("bottom", yB, xL, xR),
            ("top", yT, xL, xR),
            ("left", xL, yB, yT),
            ("right", xR, yB, yT),
        ]

    # Distribute remaining bars one by one to faces in order
    face_counts = [0] * 4
    for i in range(remaining):
        face_counts[i % 4] += 1

    # Calculate coordinates based on counts
    for i, count in enumerate(face_counts):
        if count == 0: continue
        
        face_name, fixed, start, end = faces[i]
        
        # We need (count + 2) points to include corners, then slice off corners
        # internal_points = np.linspace(start, end, count + 2)[1:-1]
        
        # Alternative robust math for spacing
        spacing = (end - start) / (count + 1)
        internal_points = [start + spacing * (j+1) for j in range(count)]
        
        for p in internal_points:
            if face_name in ["left", "right"]:
                positions.append((fixed, p)) # fixed X, varying Y
            else:
                positions.append((p, fixed)) # varying X, fixed Y

    return positions

# ======================================
# 2. HELPER: DRAWING FUNCTIONS
# ======================================
def draw_cross_section(shape, dims, num_bars, bar_dia):
    fig, ax = plt.subplots(figsize=(4, 4))
    cover = 40 # Standard cover for visualization
    bar_r = bar_dia / 2

    # Set background color to match Streamlit dark theme optionally, 
    # or keep white for clarity. Let's keep it clean white/transparent.
    fig.patch.set_alpha(0) 
    ax.patch.set_alpha(0)

    if shape == "Rectangular":
        b, h = dims
        # Draw Concrete
        ax.add_patch(patches.Rectangle((0, 0), b, h, fill=True, facecolor='#e0e0e0', edgecolor='black', linewidth=2))
        ax.set_xlim(-50, b + 50)
        ax.set_ylim(-50, h + 50)
        positions = distribute_bars_rectangular(b, h, cover, num_bars)

    elif shape == "Square":
        a = dims[0]
        ax.add_patch(patches.Rectangle((0, 0), a, a, fill=True, facecolor='#e0e0e0', edgecolor='black', linewidth=2))
        ax.set_xlim(-50, a + 50)
        ax.set_ylim(-50, a + 50)
        positions = distribute_bars_rectangular(a, a, cover, num_bars)

    else:  # Circular
        D = dims[0]
        cx, cy = D / 2, D / 2
        r_col = D / 2
        r_bars = D / 2 - cover
        
        ax.add_patch(patches.Circle((cx, cy), r_col, fill=True, facecolor='#e0e0e0', edgecolor='black', linewidth=2))
        ax.set_xlim(-50, D + 50)
        ax.set_ylim(-50, D + 50)

        angles = np.linspace(0, 2 * np.pi, num_bars, endpoint=False)
        positions = [(cx + r_bars * np.cos(a), cy + r_bars * np.sin(a)) for a in angles]

    # Draw Rebars
    for x, y in positions:
        ax.add_patch(patches.Circle((x, y), bar_r, color="#d32f2f", zorder=10))

    ax.set_aspect("equal")
    ax.axis("off")
    # ax.set_title("Cross-Section", color="white")
    return fig

def draw_side_view(width, num_bars, tie_spacing):
    fig, ax = plt.subplots(figsize=(2, 5))
    height = 1500 # Arbitrary cut height
    cover = 40
    
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    # Column Outline
    ax.add_patch(patches.Rectangle((0, 0), width, height, fill=True, facecolor='#f5f5f5', edgecolor='black', linewidth=2))

    # Longitudinal Bars (Projected)
    # Just show 2 outer bars and maybe 1 center for visualization depth
    bar_x_positions = [cover, width-cover] 
    if num_bars > 4: 
        bar_x_positions.append(width/2)
        
    for x in bar_x_positions:
        ax.plot([x, x], [0, height], color="#d32f2f", linewidth=2, linestyle='-')

    # Ties (Stirrups)
    for y in np.arange(tie_spacing, height, tie_spacing):
        ax.plot([cover, width - cover], [y, y], color="#333", linewidth=1.5)

    ax.set_xlim(-20, width + 20)
    ax.set_ylim(0, height)
    ax.axis("off")
    # ax.set_title(f"Elevation (@{tie_spacing}mm)", color="white")
    return fig

# ======================================
# 3. MAIN APP
# ======================================
def app():
    st.header("🏗️ Analysis of Axial Load Capacity")
    st.markdown("---")

    # Layout: Left for Inputs, Right for Visuals
    col_input, col_viz = st.columns([1.2, 1])

    with col_input:
        st.subheader("1. Design Inputs")
        
        # --- A. Settings ---
        with st.expander("⚙️ General Settings", expanded=True):
            design_code = st.selectbox("Design Code", ["ACI 318-19 (USA/Gulf)", "Eurocode 2 (EU/Turkey)"])
            shape = st.selectbox("Column Shape", ["Rectangular", "Square", "Circular"])

        # --- B. Materials ---
        st.markdown("**Material Properties**")
        c1, c2 = st.columns(2)
        with c1:
            fc = st.number_input("Concrete (f'c) [MPa]", value=30.0, step=5.0)
        with c2:
            fy = st.number_input("Steel (fy) [MPa]", value=420.0, step=10.0)

        # --- C. Dimensions ---
        st.markdown("**Geometry**")
        if shape == "Rectangular":
            cc1, cc2 = st.columns(2)
            with cc1: b = st.number_input("Width (b) [mm]", value=300.0, step=50.0)
            with cc2: h = st.number_input("Depth (h) [mm]", value=500.0, step=50.0)
            Ag = b * h
            dims = (b, h)
            viz_width = b # for side view
        elif shape == "Square":
            a = st.number_input("Side (a) [mm]", value=400.0, step=50.0)
            Ag = a * a
            dims = (a,)
            viz_width = a
        else: # Circular
            D = st.number_input("Diameter (D) [mm]", value=400.0, step=50.0)
            Ag = np.pi * D**2 / 4
            dims = (D,)
            viz_width = D

        # --- D. Reinforcement ---
        st.markdown("**Reinforcement**")
        rc1, rc2 = st.columns(2)
        with rc1:
            bar_dia = st.number_input("Bar Dia [mm]", value=20.0, step=2.0)
            num_bars = st.number_input("Total Bars", value=6, min_value=4, step=1)
        with rc2:
            tie_spacing = st.number_input("Tie Spacing [mm]", value=150, step=25)

        # Quick Calcs
        Ast = num_bars * np.pi * (bar_dia / 2) ** 2
        rho = (Ast / Ag) * 100
        
        # Warning if Rho is out of spec (1% to 8%)
        if rho < 1.0:
            st.warning(f"⚠️ Low Reinforcement: {rho:.2f}% (Min 1% recommended)")
        elif rho > 8.0:
            st.warning(f"⚠️ High Reinforcement: {rho:.2f}% (Max 8% recommended)")
        else:
            st.info(f"✅ Ratio: **{rho:.2f}%** ($A_s={Ast:,.0f}$ mm²)")

    with col_viz:
        st.subheader("2. Visualization")
        # Tabs for different views
        tab1, tab2 = st.tabs(["Cross-Section", "Elevation"])
        
        with tab1:
            st.pyplot(draw_cross_section(shape, dims, num_bars, bar_dia))
            st.caption("Auto-distribution of bars based on side length.")
            
        with tab2:
            st.pyplot(draw_side_view(viz_width, num_bars, tie_spacing))
            st.caption(f"Ties spaced at {tie_spacing} mm c/c")

    st.markdown("---")

    # ======================================
    # 4. DETAILED CALCULATION LOGIC
    # ======================================
    st.subheader("3. Calculation Report")
    
    if st.button("Calculate Capacity", type="primary"):
        
        # --- ACI 318 LOGIC ---
        if "ACI 318" in design_code:
            st.success("Selected Standard: **ACI 318-19**")

            # ACI Factors
            if shape == "Circular":
                confinement = "Spiral"
                phi, alpha = 0.75, 0.85
            else:
                confinement = "Tied"
                phi, alpha = 0.65, 0.80

            # Math
            Pn_conc = 0.85 * fc * (Ag - Ast)
            Pn_steel = fy * Ast
            Pn_kN = (Pn_conc + Pn_steel) / 1000
            PhiPn_kN = alpha * phi * Pn_kN

            # Display
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Step A: Nominal Strength ($P_n$)**")
                st.latex(r"P_n = 0.85 f'_c (A_g - A_{st}) + f_y A_{st}")
                st.write(f"$P_n = 0.85({fc})({Ag:,.0f} - {Ast:,.0f}) + {fy}({Ast:,.0f})$")
                st.write(f"**$P_n$ = {Pn_kN:,.2f} kN**")
            
            with c2:
                st.markdown("**Step B: Design Strength ($\phi P_n$)**")
                st.latex(r"\phi P_{n(max)} = \alpha \cdot \phi \cdot P_n")
                st.write(f"Factors: $\\alpha={alpha}$ ({confinement}), $\phi={phi}$")
                # Fix for latex f-string issue using double brackets
                st.latex(fr"\phi P_{{n(max)}} = {alpha} \cdot {phi} \cdot {Pn_kN:.2f}")
                st.markdown(f"### Capacity: **{PhiPn_kN:,.2f} kN**")

        # --- EUROCODE 2 LOGIC ---
        else:
            st.success("Selected Standard: **Eurocode 2**")
            
            # EC2 Factors
            gamma_c, gamma_s = 1.5, 1.15
            alpha_cc = 0.85 
            
            fcd = (alpha_cc * fc) / gamma_c
            fyd = fy / gamma_s
            
            Ac = Ag - Ast
            Nrd_kN = (fcd * Ac + fyd * Ast) / 1000
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Step A: Design Strengths**")
                st.latex(r"f_{cd} = \frac{\alpha_{cc} f_{ck}}{\gamma_c}, \quad f_{yd} = \frac{f_{yk}}{\gamma_s}")
                st.write(f"$f_{{cd}} = {fcd:.2f}$ MPa, $f_{{yd}} = {fyd:.2f}$ MPa")
                
            with c2:
                st.markdown("**Step B: Resistance ($N_{Rd}$)**")
                st.latex(r"N_{Rd} = f_{cd} A_c + f_{yd} A_s")
                st.latex(fr"N_{{Rd}} = {fcd:.2f}({Ac:,.0f}) + {fyd:.2f}({Ast:,.0f})")
                st.markdown(f"### Capacity: **{Nrd_kN:,.2f} kN**")
