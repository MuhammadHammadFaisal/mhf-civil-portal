import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ============================================================
# FINITE DIFFERENCE SOLVER FOR HEAD (φ)
# ============================================================

def solve_laplace_phi(nx, ny, lx, ly, pile_d, pile_x, dam_w, h_up, h_down, mode):
    x = np.linspace(-lx / 2, lx / 2, nx)
    y = np.linspace(-ly, 0, ny)
    dx = x[1] - x[0]
    dy = y[1] - y[0]

    X, Y = np.meshgrid(x, y)

    phi = np.full((ny, nx), (h_up + h_down) / 2)

    def ix(val): return np.abs(x - val).argmin()
    def iy(val): return np.abs(y - val).argmin()

    pile_ix = ix(pile_x)
    pile_iy = iy(-pile_d)

    dam_l = ix(-dam_w / 2)
    dam_r = ix(dam_w / 2)

    iters = 5000
    for _ in range(iters):
        phi[1:-1, 1:-1] = 0.25 * (
            phi[2:, 1:-1] + phi[:-2, 1:-1] +
            phi[1:-1, 2:] + phi[1:-1, :-2]
        )

        # Upstream / Downstream heads
        phi[-1, :dam_l] = h_up
        phi[-1, dam_r + 1:] = h_down

        # Dam base (impervious)
        if "Dam" in mode:
            phi[-1, dam_l:dam_r + 1] = phi[-2, dam_l:dam_r + 1]

        # Sheet pile (impervious)
        if "Pile" in mode:
            phi[pile_iy:, pile_ix] = phi[pile_iy:, pile_ix - 1]

        # Impervious bottom
        phi[0, :] = phi[1, :]

        # Far field (Neumann)
        phi[:, 0] = phi[:, 1]
        phi[:, -1] = phi[:, -2]

    return x, y, phi


# ============================================================
# STREAMLIT APP
# ============================================================

def app():
    st.set_page_config(layout="wide")
    st.title("2D Seepage Flow Net (Correct Physics)")

    mode = st.radio(
        "Structure Type",
        ["Sheet Pile Only", "Concrete Dam Only", "Combined (Dam + Pile)"]
    )

    col1, col2 = st.columns([1, 1.6])

    with col1:
        h_up = st.number_input("Upstream Head [m]", value=10.0)
        h_down = st.number_input("Downstream Head [m]", value=2.0)
        soil_d = st.number_input("Impervious Layer Depth [m]", value=12.0)

        dam_w = 0.0
        pile_d = 0.0
        pile_x = 0.0

        if "Dam" in mode:
            dam_w = st.number_input("Dam Width [m]", value=6.0)
        if "Pile" in mode:
            pile_d = st.number_input("Pile Depth [m]", value=6.0)
            pile_x = st.number_input("Pile X Location [m]", value=0.0)

        Nf = st.slider("Flow Line Density", 2, 10, 5)
        Nd = st.slider("Equipotential Drops", 6, 24, 12)

    with col2:
        nx, ny = 160, 80
        lx = 120

        x, y, phi = solve_laplace_phi(
            nx, ny, lx, soil_d,
            pile_d, pile_x, dam_w,
            h_up, h_down, mode
        )

        X, Y = np.meshgrid(x, y)

        # Darcy velocity field
        dphidy, dphidx = np.gradient(phi, y, x)
        vx = -dphidx
        vy = -dphidy

        # Masks
        mask = Y < -soil_d
        vx = np.ma.array(vx, mask=mask)
        vy = np.ma.array(vy, mask=mask)
        phi_m = np.ma.array(phi, mask=mask)

        fig, ax = plt.subplots(figsize=(11, 7))
        ax.set_aspect('equal')
        ax.set_facecolor("#fdf6e3")

        # FLOW LINES (streamlines)
        ax.streamplot(
            X, Y, vx, vy,
            density=Nf,
            color="blue",
            linewidth=2,
            arrowsize=1.2
        )

        # EQUIPOTENTIAL LINES
        levels = np.linspace(h_down, h_up, Nd + 1)
        ax.contour(
            X, Y, phi_m,
            levels=levels,
            colors="red",
            linestyles="--",
            linewidths=1.4
        )

        # STRUCTURES
        if "Dam" in mode:
            ax.add_patch(
                patches.Rectangle(
                    (-dam_w / 2, 0),
                    dam_w,
                    h_up / 2,
                    facecolor="gray",
                    edgecolor="black",
                    hatch="//"
                )
            )

        if "Pile" in mode:
            ax.plot([pile_x, pile_x], [0, -pile_d], "k-", lw=6)
            ax.plot([pile_x, pile_x], [0, -pile_d], "blue", lw=3)

        # BOUNDARIES
        ax.axhline(0, color="saddlebrown", lw=3)
        ax.axhline(-soil_d, color="black", lw=4)

        # WATER
        ax.fill_between(
            [-lx / 2, (pile_x if "Pile" in mode else -dam_w / 2)],
            0, h_up,
            color="lightblue", alpha=0.4
        )
        ax.fill_between(
            [(pile_x if "Pile" in mode else dam_w / 2), lx / 2],
            0, h_down,
            color="lightblue", alpha=0.4
        )

        ax.set_xlim(-15, 15)
        ax.set_ylim(-soil_d - 1, h_up + 1)
        ax.set_title("Flow Lines (Blue) & Equipotential Lines (Red)")
        st.pyplot(fig)


if __name__ == "__main__":
    app()
