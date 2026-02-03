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
    # RECTANGULAR
    # ----------------------------
    if shape == "Rectangular":
        b, h = dims
        ax.add_patch(patches.Rectangle((0, 0), b, h, fill=False, linewidth=2))
        ax.set_xlim(-20, b + 20)
        ax.set_ylim(-20, h + 20)

        xL, xR = cover, b - cover
        yB, yT = cover, h - cover

        positions = []

        # Corner bars (always)
        positions += [
            (xL, yB),
            (xR, yB),
            (xR, yT),
            (xL, yT),
        ]

        remaining = num_bars - 4

        # Extra bars on LONGER faces only
        if remaining > 0:
            if h >= b:
                ys = np.linspace(yB, yT, remaining + 2)[1:-1]
                positions += [(xL, y) for y in ys[: remaining // 2]]
                positions += [(xR, y) for y in ys[remaining // 2 :]]
            else:
                xs = np.linspace(xL, xR, remaining + 2)[1:-1]
                positions += [(x, yB) for x in xs[: remaining // 2]]
                positions += [(x, yT) for x in xs[remaining // 2 :]]

        positions = positions[:num_bars]

    # ----------------------------
    # SQUARE
    # ----------------------------
    elif shape == "Square":
        a = dims[0]
        ax.add_patch(patches.Rectangle((0, 0), a, a, fill=False, linewidth=2))
        ax.set_xlim(-20, a + 20)
        ax.set_ylim(-20, a + 20)

        xL, xR = cover, a - cover
        yB, yT = cover, a - cover

        positions = [
            (xL, yB),
            (xR, yB),
            (xR, yT),
            (xL, yT),
        ]

        remaining = num_bars - 4
        if remaining > 0:
            xs = np.linspace(xL, xR, remaining + 2)[1:-1]
            positions += [(x, yB) for x in xs[: remaining // 2]]
            positions += [(x, yT) for x in xs[remaining // 2 :]]

        positions = positions[:num_bars]

    # ----------------------------
    # CIRCULAR
    # ----------------------------
    else:
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
        ax.add_patch(patches.Circle((x, y), bar_r, color="red"))

    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Cross-Section (Longitudinal Reinforcement)")

    return fig


def draw_side_view(num_bars, bar_dia, tie_spacing=150):
    fig, ax = plt.subplots(figsize=(3, 6))

    column_height = 3000  # mm
    width = 300
    cover = 40

    ax.add_patch(patches.Rectangle((0, 0), width, column_height, fill=False, linewidth=2))

    bar_x = np.linspace(cover, width - cover, num_bars)

    for x in bar_x:
        ax.plot([x, x], [0, column_height], color="black", linewidth=2)

    for y in np.arange(0, column_height + tie_spacing, tie_spacing):
        ax.plot([cover, width - cover], [y, y], color="black", linewidth=1)

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

    solver_mode = st.radio(
        "Select Solver Mode:",
        ["Numeric Calculation", "Symbolic / Formula Finder"],
        horizontal=True,
    )

    input_col, diagram_col = st.columns([1.1, 1])

    with input_col:
        st.markdown("## Inputs")

        design_code = st.selectbox("Design Code", ["ACI 318-19", "Eurocode 2"])
        shape = st.selectbox("Column Shape", ["Rectangular", "Square", "Circular"])

        fc = st.number_input("Concrete Strength f'c [MPa]", value=30.0)
        fy = st.number_input("Steel Yield Strength fy [MPa]", value=420.0)

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

        bar_dia = st.number_input("Bar Diameter [mm]", value=20.0)
        num_bars = st.number_input("Number of Bars", value=6, step=2)
        tie_spacing = st.number_input("Tie Spacing [mm]", value=150)

        Ast = num_bars * np.pi * (bar_dia / 2) ** 2
        rho = Ast / Ag * 100

        st.info(f"Ag = {Ag:,.0f} mm² | Ast = {Ast:,.0f} mm² | ρ = {rho:.2f}%")

    with diagram_col:
        c1, c2 = st.columns(2)
        with c1:
            st.pyplot(draw_cross_section(shape, dims, num_bars, bar_dia))
        with c2:
            st.pyplot(draw_side_view(num_bars, bar_dia, tie_spacing))

    st.markdown("---")
    st.subheader("Axial Capacity")

    if st.button("Calculate Capacity", type="primary"):
        if "ACI" in design_code:
            phi = 0.75
            Pn = 0.85 * fc * (Ag - Ast) + fy * Ast
            st.success(f"Design Axial Capacity = {phi * Pn / 1000:,.2f} kN")
        else:
            fcd = 0.85 * fc / 1.5
            fyd = fy / 1.15
            Nrd = (fcd * (Ag - Ast) + fyd * Ast) / 1000
            st.success(f"Design Axial Capacity = {Nrd:,.2f} kN")


if __name__ == "__main__":
    app()
