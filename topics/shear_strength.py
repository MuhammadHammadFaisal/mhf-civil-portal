import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import math

# ============================================================
# MAIN APP
# ============================================================
def app():

    st.header("Shear Strength Analysis – Mohr–Coulomb (Theory)")
    st.caption("Applicable for drained or undrained theoretical problems")
    st.markdown("---")

    # --------------------------------------------------------
    # MODE SELECTION
    # --------------------------------------------------------
    mode = st.radio(
        "Calculation Mode",
        ["Forward Calculation (Check Failure)", "Back Analysis (Find c and φ)"],
        horizontal=True
    )

    st.markdown("---")

    # --------------------------------------------------------
    # GLOBAL PARAMETERS (FORWARD MODE)
    # --------------------------------------------------------
    global_params = {}

    if mode == "Forward Calculation (Check Failure)":
        col1, col2 = st.columns(2)
        with col1:
            c = st.number_input("Cohesion, c (kPa)", value=15.0, step=1.0)
        with col2:
            phi = st.number_input("Friction Angle, φ (deg)", value=30.0, step=1.0)

        global_params = {"c": c, "phi": phi}

    else:
        st.info("Enter **two failure stress states** to back-calculate soil parameters.")

    # --------------------------------------------------------
    # INPUT STRESS STATES
    # --------------------------------------------------------
    col_in, col_fig = st.columns([1.4, 1])

    test_data = []
    n_tests = 1 if mode == "Forward Calculation (Check Failure)" else 2

    with col_in:
        st.subheader("Stress State Input")

        for i in range(n_tests):
            with st.expander(f"Stress State #{i+1}", expanded=True):
                c1, c2 = st.columns(2)

                sig3 = c1.number_input(
                    r"$\sigma_3$ (Confining Stress) [kPa]",
                    value=50.0 + 50*i,
                    key=f"s3_{i}"
                )

                sig1 = c2.number_input(
                    r"$\sigma_1$ (Major Principal Stress) [kPa]",
                    value=150.0 + 100*i,
                    key=f"s1_{i}"
                )

                center = (sig1 + sig3) / 2
                radius = (sig1 - sig3) / 2

                test_data.append({
                    "sig1": sig1,
                    "sig3": sig3,
                    "center": center,
                    "radius": radius
                })

    # ============================================================
    # CALCULATION FUNCTIONS
    # ============================================================
    def forward_strength(test, params):
        c = params["c"]
        phi = params["phi"]
        s3 = test["sig3"]
        s1_applied = test["sig1"]

        tan_term = math.tan(math.radians(45 + phi / 2))

        sig1_failure = (s3 * tan_term**2) + (2 * c * tan_term)

        safe = s1_applied < sig1_failure

        steps = [
            "**Mohr–Coulomb Failure Criterion**",
            r"$\sigma_1 = \sigma_3 \tan^2(45+\phi/2) + 2c\tan(45+\phi/2)$",
            f"$\sigma_1 = {s3:.1f}({tan_term:.2f})^2 + 2({c:.1f})({tan_term:.2f})$",
            f"$\sigma_{{1,max}} = {sig1_failure:.2f}$ kPa"
        ]

        return sig1_failure, safe, steps

    def back_calculate(t1, t2):
        dy = t2["sig1"] - t1["sig1"]
        dx = t2["sig3"] - t1["sig3"]

        if dx == 0:
            return None, None, ["Confining stresses must be different."]

        m = dy / dx
        phi = math.degrees(2 * (math.atan(math.sqrt(m)) - math.pi / 4))
        c = (t1["sig1"] - m * t1["sig3"]) / (2 * math.sqrt(m))

        steps = [
            f"Slope, m = {m:.3f}",
            r"$\phi = 2(\tan^{-1}(\sqrt{m}) - 45^\circ)$",
            f"$\phi = {phi:.2f}^\circ$",
            f"$c = {c:.2f}$ kPa"
        ]

        return c, phi, steps

    # ============================================================
    # MOHR CIRCLE PLOT
    # ============================================================
    with col_fig:
        st.subheader("Mohr Circle Representation")

        fig, ax = plt.subplots(figsize=(6, 6))
        max_sig = max(t["sig1"] for t in test_data) * 1.3

        ax.set_xlim(0, max_sig)
        ax.set_ylim(0, max_sig * 0.6)
        ax.set_aspect("equal")
        ax.grid(True, linestyle="--", alpha=0.5)

        ax.set_xlabel(r"Normal Stress, $\sigma$ (kPa)")
        ax.set_ylabel(r"Shear Stress, $\tau$ (kPa)")

        for t in test_data:
            arc = patches.Arc(
                (t["center"], 0),
                2 * t["radius"],
                2 * t["radius"],
                theta1=0,
                theta2=180,
                linewidth=2
            )
            ax.add_patch(arc)
            ax.plot([t["sig3"], t["sig1"]], [0, 0], "ko")

        # Failure Envelope
        if mode == "Forward Calculation (Check Failure)":
            c_plot = global_params["c"]
            phi_plot = global_params["phi"]
        else:
            c_plot, phi_plot, _ = back_calculate(test_data[0], test_data[1])

        if phi_plot is not None:
            x = np.array([0, max_sig])
            y = c_plot + x * np.tan(math.radians(phi_plot))
            ax.plot(x, y, "r", linewidth=2)

        st.pyplot(fig)

    # ============================================================
    # RESULTS
    # ============================================================
    st.markdown("---")
    st.subheader("Results")

    if mode == "Forward Calculation (Check Failure)":
        if st.button("Evaluate Stress State", type="primary"):
            sig1_fail, safe, steps = forward_strength(test_data[0], global_params)

            st.metric("Maximum Sustainable σ₁", f"{sig1_fail:.2f} kPa")

            if safe:
                st.success("Soil is **SAFE** under applied stress.")
            else:
                st.error("Soil has **FAILED**.")

            with st.expander("Step-by-Step Solution"):
                for s in steps:
                    st.write(s)

    else:
        if st.button("Compute Soil Parameters", type="primary"):
            c, phi, steps = back_calculate(test_data[0], test_data[1])

            st.metric("Cohesion, c", f"{c:.2f} kPa")
            st.metric("Friction Angle, φ", f"{phi:.2f}°")

            with st.expander("Derivation"):
                for s in steps:
                    st.write(s)


if __name__ == "__main__":
    app()
