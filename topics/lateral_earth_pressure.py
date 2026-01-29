import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import math

# =========================================================
# SAFE COULOMB FUNCTION (NO CRASH)
# =========================================================
def coulomb_Ka(phi, delta, beta, alpha):
    phi_r = math.radians(phi)
    delta_r = math.radians(delta)
    beta_r = math.radians(beta)
    alpha_r = math.radians(alpha)

    # ---- THEORY VALIDITY CHECKS ----
    if delta >= phi:
        return None, "δ must be less than φ"

    if beta >= phi:
        return None, "β must be less than φ"

    if abs(math.sin(alpha_r - delta_r)) < 1e-6:
        return None, "Invalid geometry (α − δ)"

    inner = (
        math.sin(phi_r + delta_r) *
        math.sin(phi_r - beta_r) /
        (math.sin(alpha_r - delta_r) *
         math.sin(alpha_r + beta_r))
    )

    if inner <= 0:
        return None, "Invalid parameter combination"

    Ka = (
        math.sin(phi_r + alpha_r)**2 /
        (
            math.sin(alpha_r)**2 *
            math.sin(alpha_r - delta_r) *
            (1 + math.sqrt(inner))**2
        )
    )

    return Ka, None


# =========================================================
# MAIN APP
# =========================================================
def app():

    st.header("Lateral Earth Pressure – Theory")
    st.caption("Rankine & Coulomb | 3rd Year Soil Mechanics")
    st.markdown("---")

    tab_rankine, tab_coulomb = st.tabs(["Rankine Theory", "Coulomb Theory"])

    # =====================================================
    # TAB 1 — RANKINE ACTIVE
    # =====================================================
    with tab_rankine:

        st.subheader("Q1: Rankine Active Earth Pressure")

        col_in, col_fig = st.columns([1.2, 1])

        with col_in:
            H = st.number_input("Wall Height H (m)", value=6.0)
            gamma = st.number_input("Unit Weight γ (kN/m³)", value=18.0)
            phi = st.slider("Soil Friction Angle φ (deg)", 0, 45, 30)

        # ---- Rankine Calculations ----
        Ka = math.tan(math.radians(45 - phi / 2)) ** 2
        Pa = 0.5 * Ka * gamma * H ** 2
        theta = 45 + phi / 2

        # ---- Diagram ----
        with col_fig:
            fig, ax = plt.subplots(figsize=(6, 6))

            # Wall
            ax.plot([0, 0], [0, H], linewidth=3)

            # Ground surface
            ax.plot([-5, 5], [H, H], linewidth=2)

            # Failure plane
            L = H / math.tan(math.radians(theta))
            ax.plot([0, -L], [0, H], linestyle="--", linewidth=2)

            # Soil wedge
            wedge = patches.Polygon(
                [[0, 0], [0, H], [-L, H]],
                closed=True,
                fill=False,
                hatch="..",
                edgecolor="brown"
            )
            ax.add_patch(wedge)

            # Pressure triangle
            tri = patches.Polygon(
                [[0, 0], [0.7, 0], [0, H]],
                closed=True,
                fill=False,
                edgecolor="red"
            )
            ax.add_patch(tri)

            ax.text(-L/2, H/2, "Failure Wedge")
            ax.text(0.1, H/3, "Pa", color="red")

            ax.set_aspect("equal")
            ax.set_xlim(-6, 3)
            ax.set_ylim(0, H + 1)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title("Rankine Active State")

            st.pyplot(fig)

        # ---- Results ----
        st.markdown("### Results")
        st.metric("Active Earth Pressure Coefficient (Ka)", f"{Ka:.3f}")
        st.metric("Resultant Force Pa", f"{Pa:.2f} kN/m")

        with st.expander("Theory"):
            st.latex(r"K_a = \tan^2\left(45 - \frac{\phi}{2}\right)")
            st.latex(r"P_a = \frac{1}{2} K_a \gamma H^2")
            st.latex(r"\theta = 45 + \frac{\phi}{2}")

    # =====================================================
    # TAB 2 — COULOMB ACTIVE
    # =====================================================
    with tab_coulomb:

        st.subheader("Q1: Coulomb Active Earth Pressure")

        col_in, col_fig = st.columns([1.3, 1])

        with col_in:
            H = st.number_input("Wall Height H (m)", value=6.0, key="Hc")
            gamma = st.number_input("Unit Weight γ (kN/m³)", value=18.0, key="gc")
            phi = st.slider("Soil Friction Angle φ (deg)", 20, 45, 30, key="phic")
            delta = st.slider("Wall Friction δ (deg)", 0, phi-1, min(15, phi-1))
            beta = st.slider("Backfill Slope β (deg)", 0, phi-1, 10)
            alpha = st.slider("Wall Inclination α from vertical (deg)", 0, 15, 5)

        Ka, err = coulomb_Ka(phi, delta, beta, alpha)

        with col_fig:
            fig, ax = plt.subplots(figsize=(6, 6))

            # Wall
            ax.plot(
                [0, H * math.tan(math.radians(alpha))],
                [0, H],
                linewidth=3
            )

            # Backfill
            ax.plot(
                [-5, 5],
                [H, H + 5 * math.tan(math.radians(beta))],
                linewidth=2
            )

            # Failure plane (representative)
            theta = 45 + phi / 2
            L = H / math.tan(math.radians(theta))
            ax.plot([0, -L], [0, H], linestyle="--", linewidth=2)

            # Soil wedge
            wedge = patches.Polygon(
                [[0, 0], [0, H], [-L, H + L * math.tan(math.radians(beta))]],
                closed=True,
                fill=False,
                hatch="..",
                edgecolor="brown"
            )
            ax.add_patch(wedge)

            # Force arrow
            ax.arrow(
                0.15, H/2,
                0.9 * math.cos(math.radians(delta)),
                0.9 * math.sin(math.radians(delta)),
                head_width=0.15,
                color="red"
            )

            ax.text(0.2, H/2, "Pa", color="red")

            ax.set_aspect("equal")
            ax.set_xlim(-6, 4)
            ax.set_ylim(0, H + 4)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title("Coulomb Active State")

            st.pyplot(fig)

        st.markdown("### Results")

        if err:
            st.warning(err)
        else:
            Pa = 0.5 * Ka * gamma * H**2
            st.metric("Coulomb Ka", f"{Ka:.3f}")
            st.metric("Resultant Force Pa", f"{Pa:.2f} kN/m")

        with st.expander("Theory"):
            st.write(
                "Coulomb theory accounts for wall friction, wall inclination "
                "and sloping backfill. For δ > 0, Coulomb Ka is usually less "
                "than Rankine Ka."
            )


# =========================================================
if __name__ == "__main__":
    app()
