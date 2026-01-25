import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# =========================================================
# APP CONFIG
# =========================================================
st.set_page_config(
    page_title="Advanced Soil Stress Analysis",
    layout="wide",
)

# =========================================================
# MAIN APP
# =========================================================
def app():
    st.title("Advanced Effective Stress Analysis")
    st.markdown("---")

    tab1, tab2 = st.tabs(["Stress Profile Calculator", "Heave Check"])

    # =====================================================
    # TAB 1 — STRESS PROFILE
    # =====================================================
    with tab1:

        # -------------------------------------------------
        # 1. INPUTS + INPUT MONITOR (SAME ROW)
        # -------------------------------------------------
        st.markdown("## 1. Inputs")

        col_inputs, col_monitor = st.columns([2.2, 1.3])

        # ================= LEFT: INPUTS =================
        with col_inputs:

            solver_mode = st.radio(
                "Select Solver Mode:",
                ["Numeric Calculation", "Symbolic / Formula Finder"],
                horizontal=True
            )

            st.caption(
                "The INPUT diagram updates live. "
                "Stress results appear after solving."
            )

            st.markdown("### Soil State")
            soil_state = st.radio(
                "",
                ["Partially Saturated", "Fully Saturated (Sr = 1)", "Dry (Sr = 0)"]
            )

            c1, c2 = st.columns(2)
            with c1:
                w = st.number_input("Water Content (w)", value=0.0)
                Gs = st.number_input("Specific Gravity (Gs)", value=2.65)
                e = st.number_input("Void Ratio (e)", value=0.6)
            with c2:
                n = st.number_input("Porosity (n)", value=0.0)
                Sr = st.number_input("Degree of Saturation (Sr)", value=0.0)
                gamma_bulk = st.number_input("Bulk Unit Weight (kN/m³)", value=18.0)

            st.divider()

            c3, c4, c5 = st.columns(3)
            with c3:
                water_depth = st.number_input("Water Table Depth (m)", value=2.0)
            with c4:
                hc = st.number_input("Capillary Rise (m)", value=0.0)
            with c5:
                surcharge = st.number_input("Surcharge q (kPa)", value=80.0)

        # ================= RIGHT: INPUT MONITOR =================
        with col_monitor:
            st.markdown("### Input Monitor")

            fig, ax = plt.subplots(figsize=(3.6, 5))
            ax.axis("off")

            # Soil column (normalized sketch)
            ax.add_patch(patches.Rectangle((0.4, 0), 0.6, 3, facecolor="#D2B48C", edgecolor="black"))
            ax.add_patch(patches.Rectangle((0.4, 3), 0.6, 1, facecolor="#8fd3f4", edgecolor="black"))
            ax.add_patch(patches.Rectangle((0.4, 4), 0.6, 1, facecolor="white", edgecolor="black"))

            ax.text(0.7, 1.5, "S", ha="center", va="center", fontsize=12, weight="bold")
            ax.text(0.7, 3.5, "W", ha="center", va="center", fontsize=12, weight="bold")
            ax.text(0.7, 4.5, "A", ha="center", va="center", fontsize=12, weight="bold")

            ax.text(1.05, 3.5, "Mw (w = ?)", color="red", fontsize=9)
            ax.text(1.05, 1.5, "Ms (Gs = ?)", color="red", fontsize=9)
            ax.text(0.55, 5.1, "Sr = ?", color="red", fontsize=10)

            st.pyplot(fig, use_container_width=True)

        # -------------------------------------------------
        # 2. SOIL STRATIGRAPHY
        # -------------------------------------------------
        st.markdown("## Soil Stratigraphy")

        num_layers = st.number_input("Number of Layers", 1, 5, 2)
        layers = []
        colors = {"Sand": "#E6D690", "Clay": "#B0A494"}

        depth_tracker = 0.0

        for i in range(int(num_layers)):
            with st.expander(f"Layer {i+1} (Top at {depth_tracker:.2f} m)", expanded=True):
                a, b, c, d = st.columns(4)

                soil_type = a.selectbox("Type", ["Sand", "Clay"], key=f"t{i}")
                thickness = b.number_input("Thickness (m)", 0.1, step=0.5, value=4.0, key=f"h{i}")
                gamma_sat = c.number_input("γ_sat (kN/m³)", value=20.0, key=f"gs{i}")
                gamma_dry = d.number_input("γ_dry (kN/m³)", value=17.0, key=f"gd{i}")

                layers.append({
                    "type": soil_type,
                    "H": thickness,
                    "g_sat": gamma_sat,
                    "g_dry": gamma_dry,
                    "color": colors[soil_type]
                })

                depth_tracker += thickness

        total_depth = depth_tracker

        # -------------------------------------------------
        # 3. CALCULATE STRESSES
        # -------------------------------------------------
        if st.button("Calculate Stress Profile", type="primary"):

            gamma_w = 9.81

            # -------- DEPTH DISCRETIZATION (FIXED BUG) --------
            z_points = [0.0]
            current_depth = 0.0

            for layer in layers:
                current_depth += layer["H"]
                z_points.append(round(current_depth, 3))

            if 0 < water_depth < current_depth:
                z_points.append(water_depth)

            if hc > 0:
                cap_top = water_depth - hc
                if 0 < cap_top < current_depth:
                    z_points.append(cap_top)

            z_points = sorted(set(z_points))

            results = []
            sigma_prev = surcharge
            z_prev = 0.0

            for z in z_points:

                # ---- pore pressure ----
                if z > water_depth:
                    u_h = (z - water_depth) * gamma_w
                elif z > water_depth - hc:
                    u_h = -(water_depth - z) * gamma_w
                else:
                    u_h = 0.0

                # ---- total stress ----
                if z == 0:
                    sigma = surcharge
                    soil_here = layers[0]["type"]
                else:
                    dz = z - z_prev
                    z_mid = (z + z_prev) / 2

                    depth_sum = 0
                    for l in layers:
                        depth_sum += l["H"]
                        if z_mid <= depth_sum:
                            soil_here = l["type"]
                            gamma = l["g_sat"] if z_mid >= water_depth - hc else l["g_dry"]
                            break

                    sigma = sigma_prev + gamma * dz

                # ---- excess pore pressure ----
                u_excess = 0.0
                if soil_here == "Clay" and z > water_depth and "Short Term" in solver_mode:
                    u_excess = surcharge

                u_total = u_h + u_excess
                sigma_eff = sigma - u_total

                results.append([z, sigma, u_total, sigma_eff])

                sigma_prev = sigma
                z_prev = z

            df = pd.DataFrame(
                results,
                columns=[
                    "Depth (m)",
                    "Total Stress σ (kPa)",
                    "Pore Pressure u (kPa)",
                    "Effective Stress σ' (kPa)"
                ]
            )

            # -------------------------------------------------
            # 4. RESULTS
            # -------------------------------------------------
            st.markdown("## 2. Results")

            fig, ax = plt.subplots(figsize=(8, 6))

            cur = 0
            for l in layers:
                ax.axhspan(cur, cur + l["H"], color=l["color"], alpha=0.3)
                cur += l["H"]

            ax.plot(df["Total Stress σ (kPa)"], df["Depth (m)"], label="σ", marker="o")
            ax.plot(df["Pore Pressure u (kPa)"], df["Depth (m)"], label="u", linestyle="--")
            ax.plot(df["Effective Stress σ' (kPa)"], df["Depth (m)"], label="σ'", linewidth=2)

            ax.axhline(water_depth, color="blue", linestyle="--", label="WT")
            ax.set_ylim(max(z_points), 0)
            ax.set_xlabel("Stress (kPa)")
            ax.set_ylabel("Depth (m)")
            ax.grid(True)
            ax.legend()

            c1, c2 = st.columns([1, 2])
            with c1:
                st.dataframe(df.style.format("{:.2f}"))
            with c2:
                st.pyplot(fig)

    # =====================================================
    # TAB 2 — HEAVE CHECK
    # =====================================================
    with tab2:
        st.subheader("Bottom Heave & Piping Check")

        c1, c2 = st.columns(2)
        with c1:
            h_clay = st.number_input("Clay Thickness (m)", value=5.0)
            gamma_clay = st.number_input("Clay Unit Weight (kN/m³)", value=20.0)
        with c2:
            artesian_head = st.number_input("Artesian Head (m)", value=2.0)
            excavation_depth = st.number_input("Excavation Depth (m)", value=3.0)

        if st.button("Check Heave Safety"):
            remaining = h_clay - excavation_depth

            if remaining <= 0:
                st.error("Excavation exceeds clay thickness!")
            else:
                sigma_down = remaining * gamma_clay
                u_up = (h_clay + artesian_head) * 9.81
                FS = sigma_down / u_up

                st.latex(
                    rf"FS = \frac{{{remaining:.2f} \times {gamma_clay}}}{{{u_up:.2f}}} = \mathbf{{{FS:.2f}}}"
                )

                if FS < 1.0:
                    st.error("UNSAFE — Bottom Heave Expected")
                elif FS < 1.2:
                    st.warning("Marginal Safety")
                else:
                    st.success("Safe Against Heave")

# =========================================================
# RUN APP
# =========================================================
if __name__ == "__main__":
    app()
