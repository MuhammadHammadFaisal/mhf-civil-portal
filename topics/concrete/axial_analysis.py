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
        return positions[:num_bars] 

    # Determine face priority (longer faces get bars first)
    if h >= b:
        faces = [("left", xL, yB, yT), ("right", xR, yB, yT), ("bottom", yB, xL, xR), ("top", yT, xL, xR)]
    else:
        faces = [("bottom", yB, xL, xR), ("top", yT, xL, xR), ("left", xL, yB, yT), ("right", xR, yB, yT)]

    # Distribute remaining bars
    face_counts = [0] * 4
    for i in range(remaining):
        face_counts[i % 4] += 1

    for i, count in enumerate(face_counts):
        if count == 0: continue
        face_name, fixed, start, end = faces[i]
        spacing = (end - start) / (count + 1)
        internal_points = [start + spacing * (j+1) for j in range(count)]
        
        for p in internal_points:
            if face_name in ["left", "right"]:
                positions.append((fixed, p)) 
            else:
                positions.append((p, fixed))

    return positions

# ======================================
# 2. HELPER: DRAWING FUNCTIONS
# ======================================
def draw_cross_section(shape, dims, num_bars, bar_dia, trans_type):
    fig, ax = plt.subplots(figsize=(4, 4))
    cover = 40 
    bar_r = bar_dia / 2
    
    # Transparent Background
    fig.patch.set_alpha(0) 
    ax.patch.set_alpha(0)

    if shape in ["Rectangular", "Square"]:
        if shape == "Rectangular":
            b, h = dims
        else:
            b, h = dims[0], dims[0]
            
        ax.add_patch(patches.Rectangle((0, 0), b, h, fill=True, facecolor='#e0e0e0', edgecolor='black', linewidth=2))
        ax.set_xlim(-50, b + 50)
        ax.set_ylim(-50, h + 50)
        positions = distribute_bars_rectangular(b, h, cover, num_bars)
        
        # Draw Ties (Rough representation)
        ax.add_patch(patches.Rectangle((cover/2, cover/2), b-cover, h-cover, fill=False, edgecolor='#555', linewidth=1.5, linestyle='--'))

    else:  # Circular
        D = dims[0]
        cx, cy = D / 2, D / 2
        
        ax.add_patch(patches.Circle((cx, cy), D/2, fill=True, facecolor='#e0e0e0', edgecolor='black', linewidth=2))
        ax.set_xlim(-50, D + 50)
        ax.set_ylim(-50, D + 50)

        angles = np.linspace(0, 2 * np.pi, num_bars, endpoint=False)
        positions = [(cx + (D/2-cover) * np.cos(a), cy + (D/2-cover) * np.sin(a)) for a in angles]
        
        # Draw Spiral or Tie
        linestyle = '-' if trans_type == "Spiral" else '--'
        ax.add_patch(patches.Circle((cx, cy), D/2 - cover/2, fill=False, edgecolor='#555', linewidth=1.5, linestyle=linestyle))

    # Draw Rebars
    for x, y in positions:
        ax.add_patch(patches.Circle((x, y), bar_r, color="#d32f2f", zorder=10))

    ax.set_aspect("equal")
    ax.axis("off")
    return fig

def draw_side_view(width, num_bars, tie_spacing, trans_type):
    fig, ax = plt.subplots(figsize=(2, 5))
    height = 1500 
    cover = 40
    
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    # Column Outline
    ax.add_patch(patches.Rectangle((0, 0), width, height, fill=True, facecolor='#f5f5f5', edgecolor='black', linewidth=2))

    # Longitudinal Bars
    ax.plot([cover, cover], [0, height], color="#d32f2f", linewidth=2)
    ax.plot([width-cover, width-cover], [0, height], color="#d32f2f", linewidth=2)

    # Transverse Reinforcement
    if trans_type == "Spiral":
        # Draw a sine wave or slanted lines to represent spiral
        y = np.arange(0, height, 10) # Resolution
        # Simple representation: Slanted lines
        for y_start in np.arange(0, height, tie_spacing):
            ax.plot([cover, width-cover], [y_start, y_start + tie_spacing*0.8], color="#333", linewidth=1)
    else:
        # Standard Ties (Horizontal lines)
        for y in np.arange(tie_spacing, height, tie_spacing):
            ax.plot([cover, width - cover], [y, y], color="#333", linewidth=1.5)

    ax.set_xlim(-20, width + 20)
    ax.set_ylim(0, height)
    ax.axis("off")
    return fig

# ======================================
# 3. MAIN APP
# ======================================
def app():
    st.header("🏗️ Analysis of Axial Load Capacity")
    st.markdown("---")

    col_input, col_viz = st.columns([1.2, 1])

    with col_input:
        st.subheader("1. Design Inputs")
        
        # --- A. Settings ---
        with st.expander("⚙️ General Settings", expanded=True):
            design_code = st.selectbox("Design Code", ["ACI 318-19 (USA/Gulf)", "Eurocode 2 (EU/Turkey)"])
            shape = st.selectbox("Column Shape", ["Rectangular", "Square", "Circular"])
            
            if shape == "Circular":
                trans_type = st.radio("Transverse Reinforcement", ["Circular Ties", "Spiral"])
                st.caption(r"Spirals provide higher ductility ($\phi=0.75$) than Ties ($\phi=0.65$).")
            else:
                trans_type = "Ties"
                st.caption("Rectangular/Square columns use Ties.")

        # --- B. Materials ---
        st.markdown("**Material Properties**")
        c1, c2 = st.columns(2)
        with c1: fc = st.number_input("Concrete (f'c) [MPa]", value=30.0, step=5.0)
        with c2: fy = st.number_input("Steel (fy) [MPa]", value=420.0, step=10.0)

        # --- C. Dimensions ---
        st.markdown("**Geometry**")
        if shape == "Rectangular":
            cc1, cc2 = st.columns(2)
            with cc1: b = st.number_input("Width (b) [mm]", value=300.0, step=50.0)
            with cc2: h = st.number_input("Depth (h) [mm]", value=500.0, step=50.0)
            Ag = b * h
            dims = (b, h)
            viz_width = b 
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
            tie_spacing = st.number_input(f"{trans_type} Spacing [mm]", value=150, step=25)

        # Quick Calcs
        Ast = num_bars * np.pi * (bar_dia / 2) ** 2
        rho = (Ast / Ag) * 100
        
        if rho < 1.0: st.warning(f"⚠️ Low Reinforcement: {rho:.2f}% (Min 1%)")
        elif rho > 8.0: st.warning(f"⚠️ High Reinforcement: {rho:.2f}% (Max 8%)")
        else: st.info(f"✅ Ratio: **{rho:.2f}%** ($A_s={Ast:,.0f}$ mm²)")

    with col_viz:
        st.subheader("2. Visualization")
        tab1, tab2 = st.tabs(["Cross-Section", "Elevation"])
        with tab1:
            fig1 = draw_cross_section(shape, dims, num_bars, bar_dia, trans_type)
            st.pyplot(fig1)
            plt.close(fig1)
            st.caption(f"Configuration: {shape} with {trans_type}")
        with tab2:
            fig2 = draw_side_view(viz_width, num_bars, tie_spacing, trans_type)
            st.pyplot(fig2)
            plt.close(fig2)

    st.markdown("---")

    # ======================================
    # 4. DETAILED CALCULATION LOGIC
    # ======================================
    st.subheader("3. Calculation Report")
    
    if st.button("Calculate Capacity", type="primary"):
        
        # --- ACI 318 LOGIC ---
        if "ACI 318" in design_code:
            st.success(f"Selected: **ACI 318-19** ({trans_type} Column)")

            # ACI Factors determination
            if trans_type == "Spiral":
                phi = 0.75
                alpha = 0.85
                acc_ecc_msg = "Spirals = 0.85"
            else:
                # Includes Circular with Ties AND Rectangular/Square
                phi = 0.65
                alpha = 0.80
                acc_ecc_msg = "Ties = 0.80"

            # 1. Theoretical Pure Axial (First Peak)
            Pn_conc = 0.85 * fc * (Ag - Ast)
            Pn_steel = fy * Ast
            Pn_newton = Pn_conc + Pn_steel
            Pn_kN = Pn_newton / 1000 
            
            # 2. Design Axial (Second Peak / Practical Limit)
            PhiPn_kN = alpha * phi * Pn_kN

            # --- OUTPUT ---
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown(r"### Peak 1: Theoretical Limit ($P_0$)")
                st.caption("Nominal Strength at zero eccentricity (The 'Pure' Peak)")
                st.latex(r"P_0 = 0.85 f'_c (A_g - A_{st}) + f_y A_{st}")
                st.write(f"This is the maximum load if the column is **perfectly** straight.")
                st.metric(label="Nominal Capacity (Pn)", value=f"{Pn_kN:,.0f} kN")
            
            with c2:
                st.markdown(r"### Peak 2: Design Limit ($\phi P_{n(max)}$)")
                st.caption("Practical limit considering safety & accidental eccentricity")
                st.latex(r"\phi P_{n(max)} = \alpha \cdot \phi \cdot P_0")
                
                st.write(f"**Factors Used:**")
                st.write(f"- $\\alpha = {alpha}$ ({acc_ecc_msg})")
                st.write(f"- $\\phi = {phi}$ ({trans_type})")
                
                # Double brackets for latex f-string to prevent NameError
                st.latex(fr"\phi P_{{n(max)}} = {alpha} \cdot {phi} \cdot {Pn_kN:.0f}")
                
                st.metric(label="Design Capacity", value=f"{PhiPn_kN:,.0f} kN", delta="Final Value")

        # --- EUROCODE 2 LOGIC ---
        else:
            st.success("Selected Standard: **Eurocode 2**")
            
            gamma_c, gamma_s = 1.5, 1.15
            alpha_cc = 0.85 
            
            fcd = (alpha_cc * fc) / gamma_c
            fyd = fy / gamma_s
            
            Ac = Ag - Ast
            Nrd_kN = (fcd * Ac + fyd * Ast) / 1000
            
            st.markdown(f"### Design Capacity ($N_{{Rd}}$): **{Nrd_kN:,.2f} kN**")
            st.caption("Eurocode applies safety factors to materials, not the final load.")
            st.latex(r"N_{Rd} = f_{cd} A_c + f_{yd} A_s")
