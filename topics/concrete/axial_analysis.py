import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ======================================
# DRAWING FUNCTIONS
# ======================================

def draw_cross_section(shape, dims, num_bars, bar_dia):
    fig, ax = plt.subplots(figsize=(4, 4))

    cover = 40  # mm
    bar_r = bar_dia / 2

    # ----------------------------
    # Concrete section
    # ----------------------------
    if shape == "Rectangular":
        b, h = dims
        ax.add_patch(patches.Rectangle((0, 0), b, h, fill=False, linewidth=2))
        ax.set_xlim(-20, b + 20)
        ax.set_ylim(-20, h + 20)

        # Bar positions along perimeter
        bars_per_side = num_bars // 4
        rem = num_bars % 4

        x_left = cover
        x_right = b - cover
        y_bot = cover
        y_top = h - cover

        xs = np.linspace(x_left, x_right, bars_per_side + 2)[1:-1]
        ys = np.linspace(y_bot, y_top, bars_per_side + 2)[1:-1]

        positions = []

        positions += [(x, y_bot) for x in xs]        # bottom
        positions += [(x_right, y) for y in ys]      # right
        positions += [(x, y_top) for x in xs[::-1]]  # top
        positions += [(x_left, y) for y in ys[::-1]] # left

        positions = positions[:num_bars]

    elif shape == "Square":
        a = dims[0]
        ax.add_patch(patches.Rectangle((0, 0), a, a, fill=False, linewidth=2))
        ax.set_xlim(-20, a + 20)
        ax.set_ylim(-20, a + 20)

        bars_per_side = num_bars // 4
        x1, x2 = cover, a - cover

        xs = np.linspace(x1, x2, bars_per_side + 2)[1:-1]

        positions = []
        positions += [(x, x1) for x in xs]
        positions += [(x2, x) for x in xs]
        positions += [(x, x2) for x in xs[::-1]]
        positions += [(x1, x) for x in xs[::-1]]

        positions = positions[:num_bars]

    else:  # Circular
        D = dims[0]
        ax.add_patch(patches.Circle((D / 2, D / 2), D / 2, fill=False, linewidth=2))
        ax.set_xlim(-20, D + 20)
        ax.set_ylim(-20, D + 20)

        cx, cy = D / 2, D / 2
        r = D / 2 - cover

        angles = np.linspace(0, 2 * np.pi, num_bars, endpoint=False)
        positions = [(cx + r * np.cos(a), cy + r * np.sin(a)) for a in angles]

    # ----------------------------
    # Draw bars
    # ----------------------------
    for x, y in positions:
        ax.add_patch(patches.Circle((x, y), bar_r, color="black"))

    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Cross-Section (Longitudinal Reinforcement)")

    return fig

def draw_side_view(num_bars, bar_dia, tie_spacing=150):
    fig, ax = plt.subplots(figsize=(3, 6))

    column_height = 3000  # mm (symbolic)
    width = 300
    cover = 40

    # Column outline
    ax.add_patch(
        patches.Rectangle((0, 0), width, column_height, fill=False, linewidth=2)
    )

    # ----------------------------
    # Longitudinal bars
    # ----------------------------
    bar_r = bar_dia / 2
    bar_x = np.linspace(cover, width - cover, num_bars)

    for x in bar_x:
        ax.plot(
            [x, x],
            [0, column_height],
            color="black",
            linewidth=2
        )

    # ----------------------------
    # Ties (stirrups)
    # ----------------------------
    for y in np.arange(0, column_height + tie_spacing, tie_spacing):
        ax.plot(
            [cover, width - cover],
            [y, y],
            color="black",
            linewidth=1
        )

    ax.set_xlim(-30, width + 30)
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
