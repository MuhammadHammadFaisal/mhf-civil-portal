import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_column(shape, dims, num_bars, bar_dia):
    fig, ax = plt.subplots(figsize=(4, 4))

    # ---------- DRAW CONCRETE ----------
    if shape == "Rectangular":
        b, h = dims
        ax.add_patch(patches.Rectangle((0, 0), b, h, fill=False, linewidth=2))
        cx, cy = b / 2, h / 2
        radius = min(b, h) / 2.5

    elif shape == "Square":
        a = dims[0]
        ax.add_patch(patches.Rectangle((0, 0), a, a, fill=False, linewidth=2))
        cx, cy = a / 2, a / 2
        radius = a / 2.5

    else:  # Circular
        D = dims[0]
        ax.add_patch(patches.Circle((D / 2, D / 2), D / 2, fill=False, linewidth=2))
        cx, cy = D / 2, D / 2
        radius = D / 2.5

    # ---------- DRAW REBARS ----------
    bar_r = bar_dia / 2
    angles = np.linspace(0, 2 * np.pi, num_bars, endpoint=False)

    for ang in angles:
        x = cx + radius * np.cos(ang)
        y = cy + radius * np.sin(ang)
        ax.add_patch(patches.Circle((x, y), bar_r, color="black"))

    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Column Cross-Section")

    return fig


def app():
    st.header("Analysis of Axial Load Capacity")
    st.markdown("---")

    # ==============================
    # DESIGN PARAMETERS (MAIN PAGE)
    # ==============================
    st.subheader("Design Parameters")

    col_dp1, col_dp2 = st.columns(2)

    with col_dp1:
        design_code = st.selectbox(
            "Design Code",
            ["ACI 318-19 (USA/Gulf)", "Eurocode 2 (Turkey/EU)"]
        )

    with col_dp2:
        shape = st.selectbox(
            "Column Shape",
            ["Rectangular", "Square", "Circular"]
        )

    st.markdown("---")

    # ==============================
    # INPUT DATA
    # ==============================
    st.subheader("1. Input Data")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Material Properties**")
        fc = st.number_input("Concrete Strength [MPa]", 10.0, value=30.0, step=5.0)
        fy = st.number_input("Steel Yield Strength [MPa]", 200.0, value=420.0, step=10.0)

    with col2:
        st.markdown("**Geometry**")

        if shape == "Rectangular":
            b = st.number_input("Width b [mm]", 100.0, value=300.0, step=50.0)
            h = st.number_input("Depth h [mm]", 100.0, value=500.0, step=50.0)
            Ag = b * h
            dims = (b, h)

        elif shape == "Square":
            a = st.number_input("Side a [mm]", 100.0, value=400.0, step=50.0)
            Ag = a * a
            dims = (a,)

        else:
            D = st.number_input("Diameter D [mm]", 100.0, value=400.0, step=50.0)
            Ag = np.pi * D**2 / 4
            dims = (D,)

    with col3:
        st.markdown("**Reinforcement**")
        bar_dia = st.number_input("Bar Diameter [mm]", 8.0, value=20.0, step=2.0)
        num_bars = st.number_input("Number of Bars", 4, value=6, step=2)

        Ast = num_bars * np.pi * (bar_dia / 2) ** 2
        rho = Ast / Ag * 100

    st.info(
        f"**Ag:** {Ag:,.0f} mm² | "
        f"**Ast:** {Ast:,.0f} mm² | "
        f"**ρ:** {rho:.2f}%"
    )

    # ==============================
    # DYNAMIC DIAGRAM
    # ==============================
    st.subheader("2. Structural Diagram")

    fig = draw_column(shape, dims, num_bars, bar_dia)
    st.pyplot(fig)

    # ==============================
    # CALCULATION
    # ==============================
    st.subheader("3. Detailed Calculation")

    if st.button("Calculate Capacity", type="primary"):
        st.markdown("### Results")

        if "ACI 318" in design_code:
            phi = 0.75 if shape == "Circular" else 0.65
            alpha = 0.85 if shape == "Circular" else 0.80

            Pn = 0.85 * fc * (Ag - Ast) + fy * Ast
            PhiPn = alpha * phi * Pn / 1000

            st.success(f"✅ **Design Axial Capacity:** {PhiPn:,.2f} kN")

        else:
            gamma_c = 1.5
            gamma_s = 1.15
            alpha_cc = 0.85

            fcd = alpha_cc * fc / gamma_c
            fyd = fy / gamma_s

            Nrd = (fcd * (Ag - Ast) + fyd * Ast) / 1000

            st.success(f"✅ **Design Axial Capacity:** {Nrd:,.2f} kN")
