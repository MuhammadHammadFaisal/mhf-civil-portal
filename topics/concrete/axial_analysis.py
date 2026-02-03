import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ======================================
# DRAWING FUNCTIONS
# ======================================

def draw_cross_section(shape, dims, num_bars, bar_dia):
    fig, ax = plt.subplots(figsize=(4, 4))

    # Concrete section
    if shape == "Rectangular":
        b, h = dims
        ax.add_patch(patches.Rectangle((0, 0), b, h, fill=False, linewidth=2))
        cx, cy = b / 2, h / 2
        r = min(b, h) / 2.5

    elif shape == "Square":
        a = dims[0]
        ax.add_patch(patches.Rectangle((0, 0), a, a, fill=False, linewidth=2))
        cx, cy = a / 2, a / 2
        r = a / 2.5

    else:  # Circular
        D = dims[0]
        ax.add_patch(patches.Circle((D / 2, D / 2), D / 2, fill=False, linewidth=2))
        cx, cy = D / 2, D / 2
        r = D / 2.5

    # Longitudinal bars (cross-section)
    bar_r = bar_dia / 2
    angles = np.linspace(0, 2 * np.pi, num_bars, endpoint=False)

    for ang in angles:
        x = cx + r * np.cos(ang)
        y = cy + r * np.sin(ang)
        ax.add_patch(patches.Circle((x, y), bar_r, color="black"))

    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Cross-Section (Transverse Reinforcement)")

    return fig


def draw_side_view(num_bars, bar_dia, tie_spacing=150):
    fig, ax = plt.subplots(figsize=(2.5, 5))

    column_height = 3000  # mm (symbolic)
    width = 300

    # Column outline
    ax.add_patch(patches.Rectangle((0, 0), width, column_height, fill=False, linewidth=2))

    # Longitudinal bars
    cover = 40
    bar_r = bar_dia / 2
    bar_x_positions = np.linspace(cover, width - cover, num_bars)

    for x in bar_x_positions:
        ax.plot([x, x], [0, column_height], linewidth=2)

    # Ties (stirrups)
    for y in np.arange(0, column_height, tie_spacing):
        ax.plot([cover, width - cover], [y, y], linewidth=1)

    ax.set_xlim(-20, width + 20)
    ax.set_ylim(0, column_height)
    ax.axis("off")
    ax.set_title("Side View (Longitudinal + Ties)")

    return fig


# ======================================
# MAIN APP
# ======================================

def app():
    st.header("Axial Load Capacity – Column Visualization")
    st.markdown("---")

    # Solver Mode
    solver_mode = st.radio(
        "Select Solver Mode:",
        ["Numeric Calculation", "Symbolic / Formula Finder"],
        horizontal=True
    )

    st.caption(
        "Inputs update the **section & elevation diagrams live**. "
        "Capacity results appear after solving."
    )

    st.markdown("---")

    # ======================================
    # TWO-COLUMN MAIN LAYOUT
    # ======================================
    input_col, diagram_col = st.columns([1.1, 1])

    # ======================================
    # INPUTS (LEFT)
    # ======================================
    with input_col:
        st.markdown("## 1. Inputs")

        design_code = st.selectbox(
            "Design Code",
            ["ACI 318-19", "Eurocode 2"]
        )

        shape = st.selectbox(
            "Column Shape",
            ["Rectangular", "Square", "Circular"]
        )

        st.markdown("### Material Properties")
        fc = st.number_input("Concrete Strength f'c [MPa]", value=30.0)
        fy = st.number_input("Steel Yield Strength fy [MPa]", value=420.0)

        st.markdown("### Geometry")

        if shape == "Rectangular":
            b = st.number_input("Width b [mm]", value=300.0)
            h = st.number_input("Depth h [mm]", value=500.0)
            Ag = b * h
            dims = (b, h)

        elif shape == "Square":
            a = st.number_input("Side a [mm]", value=400.0)
            Ag = a * a
            dims = (a,)

        else:
            D = st.number_input("Diameter D [mm]", value=400.0)
            Ag = np.pi * D**2 / 4
            dims = (D,)

        st.markdown("### Reinforcement")
        bar_dia = st.number_input("Bar Diameter [mm]", value=20.0)
        num_bars = st.number_input("Number of Bars", value=6, step=2)
        tie_spacing = st.number_input("Tie Spacing [mm]", value=150)

        Ast = num_bars * np.pi * (bar_dia / 2) ** 2
        rho = Ast / Ag * 100

        st.info(
            f"**Ag:** {Ag:,.0f} mm² | "
            f"**Ast:** {Ast:,.0f} mm² | "
            f"**ρ:** {rho:.2f}%"
        )

    # ======================================
    # DIAGRAMS (RIGHT)
    # ======================================
    with diagram_col:
        st.markdown("## Input Monitor")

        diag_col1, diag_col2 = st.columns(2)

        with diag_col1:
            fig1 = draw_cross_section(shape, dims, num_bars, bar_dia)
            st.pyplot(fig1)

        with diag_col2:
            fig2 = draw_side_view(num_bars, bar_dia, tie_spacing)
            st.pyplot(fig2)

    # ======================================
    # CALCULATION
    # ======================================
    st.markdown("---")
    st.subheader("2. Axial Capacity")

    if st.button("Calculate Capacity", type="primary"):
        if "ACI" in design_code:
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
