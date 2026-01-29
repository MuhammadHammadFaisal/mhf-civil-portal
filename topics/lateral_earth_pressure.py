import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import math

# =========================================================
# MAIN APP
# =========================================================
def app():

    st.header("Lateral Earth Pressure – Theory (Rankine & Coulomb)")
    st.caption("Interactive textbook-style visualization for 3rd year Soil Mechanics")
    st.markdown("---")

    tab_rankine, tab_coulomb = st.tabs(["Rankine Theory", "Coulomb Theory"])

    # =========================================================
    # TAB 1 — RANKINE
    # =========================================================
    with tab_rankine:

        st.subheader("Rankine Active Earth Pressure")

        col_in, col_fig = st.columns([1.2, 1])

        with col_in:
            H = st.number_input("Wall Height, H (m)", value=6.0)
            gamma = st.number_input("Unit Weight, γ (kN/m³)", value=18.0)
            phi = st.slider("Soil Friction Angle, φ (deg)", 0, 45, 30)

        # --- Calculations ---
        Ka = math.tan(math.radians(45 - phi/2))**2
        Pa = 0.5 * Ka * gamma * H**2
        theta = 45 + phi/2  # Failure plane angle

        with col_fig:
            fig, ax = plt.subplots(figsize=(6, 6))

            # Wall
            ax.plot([0, 0], [0, H], linewidth=3)

            # Ground
            ax.plot([-4, 4], [H, H], linewidth=2)

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
                [[0, 0], [0.6, 0], [0, H]],
                closed=True,
                fill=False,
                edgecolor="red"
            )
            ax.add_patch(tri)

            ax.text(-L/2, H/2, "Failure Wedge", fontsize=10)
            ax.text(0.1, H/3, "Pa", color="red")

            ax.set_aspect("equal")
            ax.set_xlim(-5, 3)
            ax.set_ylim(0, H + 1)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title("Rankine Active State")

            st.pyplot(fig)

        st.markdown("### Results")
        st.metric("Active Earth Pressure Coefficient (Ka)", f"{Ka:.3f}")
        st.metric("Resultant Force (Pa)", f"{Pa:.2f} kN/m")

        with st.expander("Theory & Formula"):
            st.latex(r"K_a = \tan^2\left(45 - \frac{\phi}{2}\right)")
            st.latex(r"P_a = \frac{1}{2} K_a \gamma H^2")
            st.latex(r"\theta = 45 + \frac{\phi}{2}")

    # =========================================================
    # TAB 2 — COULOMB
    # =========================================================
    with tab_coulomb:

        st.subheader("Coulomb Active Earth Pressure")

        col_in, col_fig = st.columns([1.3, 1])

        with col_in:
            H = st.number_input("Wall Height, H (m)", value=6.0, key="Hc")
            gamma = st.number_input("Unit Weight, γ (kN/m³)", value=18.0, key="gc")
            phi = st.slider("Soil Friction Angle, φ (deg)", 0, 45, 30, key="phic")
            delta = st.slider("Wall Friction Angle, δ (deg)", 0, 30, 15)
            beta = st.slider("Backfill Slope Angle, β (deg)", 0, 30, 10)
            alpha = st.slider("Wall Inclination from Vertical, α (deg)", 0, 15, 5)

        # --- Coulomb Ka (simplified standard form) ---
        phi_r = math.radians(phi)
        delta_r = math.radians(delta)
        beta_r = math.radians(beta)
        alpha_r = math.radians(alpha)

        Ka = (
            math.sin(phi_r + alpha_r)**2 /
            (
                math.sin(alpha_r)**2 *
                math.sin(alpha_r - delta_r) *
                (1 + math.sqrt(
                    math.sin(phi_r + delta_r) * math.sin(phi_r - beta_r) /
                    (math.sin(alpha_r - delta_r) * math.sin(alpha_r + beta_r))
                ))**2
            )
        )

        Pa = 0.5 * Ka * gamma * H**2

        with col_fig:
            fig, ax = plt.subplots(figsize=(6, 6))

            # Wall
            ax.plot(
                [0, H*math.tan(alpha_r)],
                [0, H],
                linewidth=3
            )

            # Backfill
            ax.plot(
                [-4, 4],
                [H, H + 4*math.tan(beta_r)],
                linewidth=2
            )

            # Failure plane (representative)
            theta = 45 + phi/2
            L = H / math.tan(math.radians(theta))
            ax.plot([0, -L], [0, H], linestyle="--", linewidth=2)

            # Soil wedge
            wedge = patches.Polygon(
                [[0, 0], [0, H], [-L, H + L*math.tan(beta_r)]],
                closed=True,
                fill=False,
                hatch="..",
                edgecolor="brown"
            )
            ax.add_patch(wedge)

            # Force arrow
            ax.arrow(
                0.1, H/2,
                0.8*math.cos(delta_r),
                0.8*math.sin(delta_r),
                head_width=0.15,
                color="red"
            )

            ax.text(0.2, H/2, "Pa", color="red")

            ax.set_aspect("equal")
            ax.set_xlim(-5, 4)
            ax.set_ylim(0, H + 4)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title("Coulomb Active State")

            st.pyplot(fig)

        st.markdown("### Results")
        st.metric("Coulomb Active Earth Pressure Coefficient (Ka)", f"{Ka:.3f}")
        st.metric("Resultant Force (Pa)", f"{Pa:.2f} kN/m")

        with st.expander("Theory Note"):
            st.write(
                "Coulomb theory accounts for wall friction, wall inclination, "
                "and sloping backfill. It generally predicts **lower active pressure** "
                "than Rankine for δ > 0."
            )

# =========================================================
if __name__ == "__main__":
    app()
