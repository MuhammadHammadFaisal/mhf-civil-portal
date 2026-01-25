import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ==================================================
# MAIN APP
# ==================================================
def app():
    st.title("Advanced Effective Stress Analysis")
    st.markdown("---")

    tab1, tab2 = st.tabs(["Stress Profile Calculator", "Heave Check"])

    # ==================================================
    # TAB 1: STRESS PROFILE
    # ==================================================
    with tab1:
        st.caption("Define soil layers and water conditions to generate stress profiles.")

        # ------------------------------
        # ANALYSIS MODE
        # ------------------------------
        c1, c2 = st.columns(2)
        with c1:
            analysis_mode = st.radio(
                "Analysis State",
                ["Long Term (Drained)", "Short Term (Undrained - Immediate)"]
            )
        with c2:
            st.info(
                "Short Term: Excess pore pressure = surcharge in **Clay** layers only.\n\n"
                "Long Term: Excess pore pressure dissipates."
            )

        st.divider()

        # ------------------------------
        # GLOBAL INPUTS
        # ------------------------------
        colA, colB, colC = st.columns(3)
        with colA:
            water_depth = st.number_input("Water Table Depth (m)", 0.0, step=0.1, value=2.0)
        with colB:
            hc = st.number_input("Capillary Rise (m)", 0.0, step=0.1, value=0.0)
        with colC:
            surcharge = st.number_input("Surcharge q (kPa)", 0.0, step=5.0, value=80.0)

        # ------------------------------
        # LAYER DEFINITION
        # ------------------------------
        num_layers = st.number_input("Number of Layers", 1, 5, 2)
        layers = []
        colors = {"Sand": "#E6D690", "Clay": "#B0A494"}

        st.markdown("### Soil Stratigraphy")

        depth_tracker = 0.0
        for i in range(int(num_layers)):
            with st.expander(f"Layer {i+1} (Top at {depth_tracker:.2f} m)", expanded=True):
                a, b, c, d = st.columns(4)

                soil_type = a.selectbox("Type", ["Sand", "Clay"], key=f"t{i}")
                thickness = b.number_input("Thickness (m)", 0.1, step=0.5, value=4.0, key=f"h{i}")
                gamma_sat = c.number_input("γ_sat (kN/m³)", 10.0, step=0.5, value=20.0, key=f"gs{i}")
                gamma_dry = d.number_input("γ_dry (kN/m³)", 10.0, step=0.5, value=17.0, key=f"gd{i}")

                layers.append({
                    "type": soil_type,
                    "H": thickness,
                    "g_sat": gamma_sat,
                    "g_dry": gamma_dry,
                    "color": colors[soil_type]
                })

                depth_tracker += thickness

        total_depth = depth_tracker

        # ==================================================
        # INPUT VISUALIZATION (COMPACT)
        # ==================================================
        st.markdown("### 1. Input Visualization")

        col_left, col_right = st.columns([2, 1])

        with col_right:
            if total_depth > 0:
                fig_sch, ax_sch = plt.subplots(figsize=(3.2, 4))
                cur_d = 0.0

                for lay in layers:
                    rect = patches.Rectangle(
                        (0, cur_d), 1.5, lay["H"],
                        facecolor=lay["color"], edgecolor="black", alpha=0.7
                    )
                    ax_sch.add_patch(rect)

                    ax_sch.text(
                        0.75, cur_d + lay["H"]/2,
                        lay["type"], ha="center", va="center", fontsize=8
                    )
                    cur_d += lay["H"]

                # Water table
                ax_sch.axhline(water_depth, color="blue", linestyle="--", linewidth=1)
                ax_sch.text(1.55, water_depth, "WT", fontsize=7, color="blue", va="center")

                # Capillary zone
                if hc > 0:
                    c_top = max(0, water_depth - hc)
                    rect_cap = patches.Rectangle(
                        (0, c_top), 1.5, water_depth - c_top,
                        hatch="///", fill=False, edgecolor="blue"
                    )
                    ax_sch.add_patch(rect_cap)

                # Surcharge arrows
                if surcharge > 0:
                    for x in np.linspace(0.2, 1.3, 4):
                        ax_sch.arrow(x, -0.4, 0, 0.3,
                                     head_width=0.05, head_length=0.08,
                                     fc="red", ec="red")
                    ax_sch.text(0.75, -0.6, f"q = {surcharge} kPa",
                                fontsize=7, color="red", ha="center")

                ax_sch.set_ylim(total_depth + 0.5, -1)
                ax_sch.set_xlim(-0.3, 1.8)
                ax_sch.axis("off")

                st.pyplot(fig_sch, use_container_width=True)

        # ==================================================
        # CALCULATIONS
        # ==================================================
        if st.button("Calculate Stress Profile", type="primary"):

            gamma_w = 9.81
            z_points = [0.0]
            d = 0.0
            for l in layers:
                d += l["H"]
                z_points.append(round(d, 3))

            if 0 < water_depth < total_depth:
                z_points.append(water_depth)

            z_points = sorted(set(z_points))

            results = []
            sigma_prev = surcharge
            z_prev = 0.0

            for z in z_points:
                # Pore pressure
                if z > water_depth:
                    u_h = (z - water_depth) * gamma_w
                elif z > water_depth - hc:
                    u_h = -(water_depth - z) * gamma_w
                else:
                    u_h = 0.0

                # Total stress
                if z == 0:
                    sigma = surcharge
                else:
                    dz = z - z_prev
                    z_mid = (z + z_prev) / 2

                    depth_sum = 0
                    for l in layers:
                        depth_sum += l["H"]
                        if z_mid <= depth_sum:
                            gamma = l["g_sat"] if z_mid >= water_depth - hc else l["g_dry"]
                            soil = l["type"]
                            break

                    sigma = sigma_prev + gamma * dz

                # Excess pore pressure
                u_excess = 0.0
                if "Short Term" in analysis_mode and soil == "Clay" and z > water_depth:
                    u_excess = surcharge

                u_total = u_h + u_excess
                sigma_eff = sigma - u_total

                results.append([z, sigma, u_total, sigma_eff])

                sigma_prev = sigma
                z_prev = z

            df = pd.DataFrame(
                results,
                columns=["Depth (m)", "Total Stress σ (kPa)", "Pore Pressure u (kPa)", "Effective Stress σ' (kPa)"]
            )

            # ------------------------------
            # OUTPUT GRAPH
            # ------------------------------
            st.markdown("### 2. Stress Profile")

            fig, ax = plt.subplots(figsize=(8, 6))

            cur = 0
            for l in layers:
                ax.axhspan(cur, cur + l["H"], color=l["color"], alpha=0.3)
                cur += l["H"]

            ax.plot(df["Total Stress σ (kPa)"], df["Depth (m)"], label="σ", marker="o")
            ax.plot(df["Pore Pressure u (kPa)"], df["Depth (m)"], label="u", linestyle="--")
            ax.plot(df["Effective Stress σ' (kPa)"], df["Depth (m)"], label="σ'", linewidth=2)

            ax.axhline(water_depth, color="blue", linestyle="--", label="WT")
            ax.invert_yaxis()
            ax.set_xlabel("Stress (kPa)")
            ax.set_ylabel("Depth (m)")
            ax.grid(True)
            ax.legend()

            c1, c2 = st.columns([1, 2])
            with c1:
                st.dataframe(df.style.format("{:.2f}"))
            with c2:
                st.pyplot(fig)

    # ==================================================
    # TAB 2: HEAVE CHECK
    # ==================================================
    with tab2:
        st.subheader("Heave & Piping Check")

        c1, c2 = st.columns(2)
        with c1:
            h_clay_total = st.number_input("Clay Thickness (m)", 5.0)
            gamma_clay = st.number_input("Clay Unit Weight (kN/m³)", 20.0)
        with c2:
            artesian_head = st.number_input("Artesian Head (m)", 2.0)
            exc_depth = st.number_input("Excavation Depth (m)", 3.0)

        if st.button("Check Heave Safety"):
            remaining = h_clay_total - exc_depth
            if remaining <= 0:
                st.error("Excavation exceeds clay thickness!")
            else:
                sigma_down = remaining * gamma_clay
                u_up = (h_clay_total + artesian_head) * 9.81
                fs = sigma_down / u_up

                st.latex(
                    rf"FS = \frac{{{remaining:.2f} \times {gamma_clay}}}{{{u_up:.2f}}} = \mathbf{{{fs:.2f}}}"
                )

                if fs < 1.0:
                    st.error("UNSAFE – Bottom Heave Expected")
                elif fs < 1.2:
                    st.warning("Marginal Safety")
                else:
                    st.success("Safe Against Heave")

# ==================================================
# RUN
# ==================================================
if __name__ == "__main__":
    app()
