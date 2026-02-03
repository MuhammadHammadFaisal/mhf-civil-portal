import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ======================================
# BAR DISTRIBUTION (PROFESSIONAL LOGIC)
# ======================================

def distribute_bars_rectangular(b, h, cover, num_bars):
    xL, xR = cover, b - cover
    yB, yT = cover, h - cover

    # Always start with 4 corner bars
    positions = [
        (xL, yB), (xR, yB),
        (xR, yT), (xL, yT)
    ]

    remaining = num_bars - 4
    if remaining <= 0:
        return positions

    # Determine face priority (longer faces first)
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

    face_index = 0
    while remaining > 0:
        face = faces[face_index % 4]

        if face[0] in ["left", "right"]:
            y = np.linspace(face[2], face[3], remaining + 2)[1]
            positions.append((face[1], y))
        else:
            x = np.linspace(face[2], face[3], remaining + 2)[1]
            positions.append((x, face[1]))

        remaining -= 1
        face_index += 1

    return positions[:num_bars]


# ======================================
# DRAWING FUNCTIONS
# ======================================

def draw_cross_section(shape, dims, num_bars, bar_dia):
    fig, ax = plt.subplots(figsize=(4, 4))
    cover = 40
    bar_r = bar_dia / 2

    if shape == "Rectangular":
        b, h = dims
        ax.add_patch(patches.Rectangle((0, 0), b, h, fill=False, linewidth=2))
        ax.set_xlim(-20, b + 20)
        ax.set_ylim(-20, h + 20)
        positions = distribute_bars_rectangular(b, h, cover, num_bars)

    elif shape == "Square":
        a = dims[0]
        ax.add_patch(patches.Rectangle((0, 0), a, a, fill=False, linewidth=2))
        ax.set_xlim(-20, a + 20)
        ax.set_ylim(-20, a + 20)
        positions = distribute_bars_rectangular(a, a, cover, num_bars)

    else:  # Circular
        D = dims[0]
        cx, cy = D / 2, D / 2
        r = D / 2 - cover
        ax.add_patch(patches.Circle((cx, cy), D / 2, fill=False, linewidth=2))
        ax.set_xlim(-20, D + 20)
        ax.set_ylim(-20, D + 20)

        angles = np.linspace(0, 2 * np.pi, num_bars, endpoint=False)
        positions = [(cx + r * np.cos(a), cy + r * np.sin(a)) for a in angles]

    for x, y in positions:
        ax.add_patch(patches.Circle((x, y), bar_r, color="red"))

    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Cross-Section (Longitudinal Reinforcement)")
    return fig


def draw_side_view(num_bars, bar_dia, tie_spacing):
    fig, ax = plt.subplots(figsize=(3, 6))
    height = 3000
    width = 300
    cover = 40

    ax.add_patch(patches.Rectangle((0, 0), width, height, fill=False, linewidth=2))

    bar_x = np.linspace(cover, width - cover, num_bars)
    for x in bar_x:
        ax.plot([x, x], [0, height], color="black", linewidth=2)

    for y in np.arange(0, height + tie_spacing, tie_spacing):
        ax.plot([cover, width - cover], [y, y], color="black", linewidth=1)

    ax.set_xlim(-30, width + 30)
    ax.set_ylim(0, height)
    ax.axis("off")
    ax.set_title("Side View (Longitudinal + Ties)")
    return fig


# ======================================
# STREAMLIT APP
# ======================================

def app():


    input_col, diagram_col = st.columns([1.1, 1])

    with input_col:
        st.subheader("Inputs")

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
