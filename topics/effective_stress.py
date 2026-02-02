import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# =========================================================
# APP CONFIG
# =========================================================
st.set_page_config(page_title="Advanced Soil Stress Analysis", layout="wide")

GAMMA_W = 9.81  # kN/m³

# =========================================================
# MAIN APP
# =========================================================
def app():
    st.markdown("---")

    tab1, tab2 = st.tabs(["Stress Profile Calculator", "Heave Check"])

    # =====================================================
    # TAB 1 — STRESS PROFILE
    # =====================================================
    with tab1:
        st.caption("Define soil layers, water table, and surcharge to calculate stress profiles.")

        col_input, col_viz = st.columns([1.1, 1])

        # -------------------------------------------------
        # INPUTS
        # -------------------------------------------------
        with col_input:
            st.markdown("### A. Global Parameters")

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(r"**Water Table Depth $z_w$ (m)**")
                water_depth = st.number_input("", value=3.0, step=0.1)
            with c2:
                st.markdown(r"**Capillary Rise $h_c$ (m)**")
                hc = st.number_input("", value=0.0, step=0.1)
            with c3:
                st.markdown(r"**Surcharge $q$ (kPa)**")
                surcharge = st.number_input("", value=50.0, step=1.0)

            st.markdown("### B. Soil Properties")
            num_layers = st.number_input("Number of Layers", 1, 5, 2)

            layers = []
            colors = {"Sand": "#E6D690", "Clay": "#B0A494"}
            depth_tracker = 0.0

            for i in range(int(num_layers)):
                with st.expander(f"Layer {i+1} (Top at {depth_tracker:.1f} m)", expanded=True):
                    cols = st.columns(4)

                    soil_type = cols[0].selectbox("Type", ["Sand", "Clay"], key=f"t{i}")
                    thickness = cols[1].number_input("Thickness (m)", 0.1, 20.0, 4.0, step=0.5, key=f"h{i}")

                    layer_top = depth_tracker
                    layer_bot = depth_tracker + thickness

                    eff_wt = water_depth - hc
                    needs_dry = layer_top < eff_wt
                    needs_sat = layer_bot > eff_wt

                    g_dry = 17.0
                    g_sat = 20.0

                    if needs_sat:
                        cols[2].markdown(r"**$\gamma_{sat}$ (kN/m³)**")
                        g_sat = cols[2].number_input("", value=20.0, key=f"gs{i}")
                    else:
                        cols[2].text_input("γ_sat", "N/A", disabled=True, key=f"gsd{i}")

                    if needs_dry:
                        cols[3].markdown(r"**$\gamma_{dry}$ (kN/m³)**")
                        g_dry = cols[3].number_input("", value=17.0, key=f"gd{i}")
                    else:
                        cols[3].text_input("γ_dry", "N/A", disabled=True, key=f"gdd{i}")

                    layers.append({
                        "id": i + 1,
                        "type": soil_type,
                        "top": layer_top,
                        "bot": layer_bot,
                        "H": thickness,
                        "g_sat": g_sat,
                        "g_dry": g_dry,
                        "color": colors[soil_type]
                    })

                    depth_tracker += thickness

            total_depth = depth_tracker

        # -------------------------------------------------
        # SOIL PROFILE VISUALIZER
        # -------------------------------------------------
        with col_viz:
            st.markdown("### Soil Profile Preview")
            fig, ax = plt.subplots(figsize=(6, 5))

            current_depth = 0
            for lay in layers:
                ax.add_patch(
                    patches.Rectangle((0, current_depth), 5, lay["H"],
                                      facecolor=lay["color"], edgecolor="black")
                )
                ax.text(2.5, current_depth + lay["H"] / 2,
                        lay["type"], ha="center", va="center", fontweight="bold")
                current_depth += lay["H"]

            if surcharge > 0:
                for x in np.linspace(0.5, 4.5, 8):
                    ax.arrow(x, -0.5, 0, 0.4, head_width=0.15,
                             head_length=0.1, fc="red", ec="red")
                ax.text(2.5, -0.7, rf"$q = {surcharge}\,\mathrm{{kPa}}$",
                        ha="center", color="red", fontweight="bold")

            ax.axhline(water_depth, color="blue", linestyle="--", linewidth=2)
            ax.text(5.1, water_depth, r"$WT$", color="blue", va="center")

            if hc > 0:
                cap_top = max(0, water_depth - hc)
                ax.add_patch(
                    patches.Rectangle((0, cap_top), 5, water_depth - cap_top,
                                      hatch="///", fill=False, edgecolor="blue")
                )

            ax.set_xlim(-1, 6)
            ax.set_ylim(total_depth * 1.1, -1.5)
            ax.axis("off")
            ax.plot([0, 5], [0, 0], "k-", linewidth=2)
            st.pyplot(fig)
            plt.close(fig)

        # -------------------------------------------------
        # CALCULATIONS
        # -------------------------------------------------
        st.markdown("---")
        if st.button("Calculate Stress Profiles", type="primary"):

            def calculate_profile(mode, q):
                results, logs = [], []
                sigma_prev = q

                for layer in layers:
                    z_pts = {layer["top"], layer["bot"]}

                    for d in range(int(layer["top"]), int(layer["bot"]) + 1):
                        if layer["top"] < d < layer["bot"]:
                            z_pts.add(float(d))

                    if layer["top"] < water_depth < layer["bot"]:
                        z_pts.add(water_depth)

                    cap_top = water_depth - hc
                    if layer["top"] < cap_top < layer["bot"]:
                        z_pts.add(cap_top)

                    z_sorted = sorted(z_pts)
                    z_prev = layer["top"]

                    for z in z_sorted:
                        dz = z - z_prev
                        z_mid = (z + z_prev) / 2

                        if z_mid > (water_depth - hc):
                            gamma = layer["g_sat"]
                            gsym = r"\gamma_{sat}"
                        else:
                            gamma = layer["g_dry"]
                            gsym = r"\gamma_{dry}"

                        sigma = sigma_prev + gamma * dz

                        if dz > 0:
                            logs.append(
                                rf"Layer {layer['id']} ({layer['type']}): "
                                rf"${gsym}={gamma}$, "
                                rf"$\Delta z={dz:.2f}$"
                            )
                            logs.append(
                                rf"$\sigma = {sigma_prev:.2f} + {gamma}\times{dz:.2f} = {sigma:.2f}$"
                            )

                        if z > water_depth:
                            u = (z - water_depth) * GAMMA_W
                            u_txt = rf"({z:.2f}-{water_depth})\times9.81"
                        elif z > (water_depth - hc):
                            u = -(water_depth - z) * GAMMA_W
                            u_txt = rf"-({water_depth}-{z:.2f})\times9.81"
                        else:
                            u = 0
                            u_txt = "0"

                        if mode == "Short Term" and q > 0 and layer["type"] == "Clay":
                            u += q
                            u_txt += rf"+{q}"

                        sig_eff = sigma - u

                        logs.append(rf"$u = {u_txt} = {u:.2f}$")
                        logs.append(
                            rf"$\sigma' = {sigma:.2f} - {u:.2f} = \mathbf{{{sig_eff:.2f}}}$"
                        )
                        logs.append("---")

                        results.append({
                            "Depth (m)": z,
                            "Soil": layer["type"],
                            "σ (kPa)": sigma,
                            "u (kPa)": u,
                            "σ′ (kPa)": sig_eff
                        })

                        sigma_prev = sigma
                        z_prev = z

                return pd.DataFrame(results), logs

            df_i, log_i = calculate_profile("Initial", 0)
            df_l, log_l = calculate_profile("Long Term", surcharge)
            df_s, log_s = calculate_profile("Short Term", surcharge)

            def plot(df, title, ax):
                ax.plot(df["σ (kPa)"], df["Depth (m)"], "b-o", label=r"$\sigma$")
                ax.plot(df["u (kPa)"], df["Depth (m)"], "r--x", label=r"$u$")
                ax.plot(df["σ′ (kPa)"], df["Depth (m)"], "k-s", label=r"$\sigma'$")
                ax.invert_yaxis()
                ax.set_xlabel("Stress (kPa)")
                ax.set_ylabel("Depth (m)")
                ax.set_title(title)
                ax.grid(True)
                ax.legend()

            st.markdown("### Results Comparison")
            for df, title in zip([df_i, df_l, df_s],
                                 ["Initial", "Long Term", "Short Term"]):
                fig, ax = plt.subplots(figsize=(5, 6))
                plot(df, title, ax)
                st.pyplot(fig)
                plt.close(fig)

    # =====================================================
    # TAB 2 — HEAVE CHECK
    # =====================================================
    with tab2:
        st.subheader("Heave & Piping Analysis")
        st.caption("Bottom heave check for clay over artesian sand.")

        st.markdown(r"Factor of Safety: $FS = \dfrac{\sigma_v}{u}$")

if __name__ == "__main__":
    app()
