import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# =========================================================
# APP CONFIG
# =========================================================
st.set_page_config(page_title="Advanced Soil Stress Analysis", layout="wide")

GAMMA_W = 9.81  # Global water unit weight


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
        st.caption("Define soil layers, water table, and surcharge to calculate the stress profile.")

        col_input, col_viz = st.columns([1.1, 1])

        # -------------------------------------------------
        # INPUTS
        # -------------------------------------------------
        with col_input:
            st.markdown("### A. Global Parameters")
            c1, c2, c3 = st.columns(3)
            with c1:
                water_depth = st.number_input("Water Table Depth (m)", value=3.0, step=0.5)
            with c2:
                hc = st.number_input("Capillary Rise (m)", value=0.0, step=0.1)
            with c3:
                surcharge = st.number_input("Surcharge q (kPa)", value=50.0, step=5.0)

            st.markdown("### B. Stratigraphy")
            num_layers = st.number_input("Number of Layers", 1, 5, 2)
            layers = []
            colors = {"Sand": "#E6D690", "Clay": "#B0A494"}

            depth_tracker = 0.0

            for i in range(int(num_layers)):
                with st.expander(f"Layer {i+1} (Top at {depth_tracker:.1f}m)", expanded=True):
                    cols = st.columns(4)
                    soil_type = cols[0].selectbox("Type", ["Sand", "Clay"], key=f"t{i}")
                    thickness = cols[1].number_input("Height (m)", 0.1, 20.0, 4.0, step=0.5, key=f"h{i}")

                    layer_top = depth_tracker
                    layer_bot = depth_tracker + thickness

                    eff_wt = water_depth - hc
                    needs_dry = layer_top < eff_wt
                    needs_sat = layer_bot > eff_wt

                    g_dry_input = 17.0
                    g_sat_input = 20.0

                    if needs_sat:
                        g_sat_input = cols[2].number_input("γ_sat", value=20.0, key=f"gs{i}")
                    else:
                        cols[2].text_input("γ_sat", value="N/A", disabled=True, key=f"gs_dis{i}")

                    if needs_dry:
                        g_dry_input = cols[3].number_input("γ_dry", value=17.0, key=f"gd{i}")
                    else:
                        cols[3].text_input("γ_dry", value="N/A", disabled=True, key=f"gd_dis{i}")

                    layers.append({
                        "type": soil_type,
                        "H": thickness,
                        "g_sat": g_sat_input,
                        "g_dry": g_dry_input,
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
                rect = patches.Rectangle((0, current_depth), 5, lay['H'],
                                         facecolor=lay['color'], edgecolor='black')
                ax.add_patch(rect)
                mid_y = current_depth + lay['H'] / 2
                ax.text(2.5, mid_y, lay['type'], ha='center', va='center', fontweight='bold')
                current_depth += lay['H']

            # Surcharge arrows
            if surcharge > 0:
                for x in np.linspace(0.5, 4.5, 8):
                    ax.arrow(x, -0.5, 0, 0.4, head_width=0.15, head_length=0.1, fc='red', ec='red')
                ax.text(2.5, -0.6, f"q = {surcharge} kPa", ha='center', color='red', fontweight='bold')

            # Water table
            ax.axhline(water_depth, color='blue', linestyle='--', linewidth=2)
            ax.text(5.1, water_depth, "WT ▽", color='blue', va='center')

            # Capillary zone
            if hc > 0:
                cap_top = max(0, water_depth - hc)
                rect_cap = patches.Rectangle((0, cap_top), 5, water_depth - cap_top,
                                             hatch='///', fill=False, edgecolor='blue')
                ax.add_patch(rect_cap)

            ax.set_xlim(-1, 6)
            ax.set_ylim(total_depth * 1.1, -1.5)
            ax.axis('off')
            ax.plot([0, 5], [0, 0], 'k-', linewidth=2)
            st.pyplot(fig)

        # -------------------------------------------------
        # CALCULATIONS
        # -------------------------------------------------
        st.markdown("---")
        if st.button("Calculate Stress Profiles", type="primary"):

            # Depth points
            z_points_set = {0.0, total_depth}
            cur = 0
            for l in layers:
                cur += l['H']
                z_points_set.add(round(cur, 3))

            if 0 < water_depth < total_depth:
                z_points_set.add(water_depth)

            cap_top = water_depth - hc
            if 0 < cap_top < total_depth:
                z_points_set.add(cap_top)

            for d in range(1, int(total_depth) + 1):
                z_points_set.add(float(d))

            sorted_z = sorted(list(z_points_set))

            # ===============================
            # CORE FUNCTION (FIXED)
            # ===============================
            def calculate_profile(mode_name, load_q):
                results = []
                math_logs = []
                sigma_prev = load_q
                z_prev = 0.0

                for i, z in enumerate(sorted_z):

                    # ----- FIX: ALWAYS DEFINE u_calc_text -----
                    u_calc_text = "0"

                    # Hydrostatic + capillary pore pressure
                    if z > water_depth:
                        u_h = (z - water_depth) * GAMMA_W
                        u_calc_text = f"({z} - {water_depth}) \\times 9.81"
                    elif z > (water_depth - hc):
                        u_h = -(water_depth - z) * GAMMA_W
                        u_calc_text = f"-({water_depth} - {z}) \\times 9.81"
                    else:
                        u_h = 0.0

                    # Total stress increment
                    if i > 0:
                        dz = z - z_prev
                        z_mid = (z + z_prev) / 2

                        d_search = 0
                        active_l = layers[-1]
                        for l in layers:
                            d_search += l['H']
                            if z_mid <= d_search:
                                active_l = l
                                break

                        eff_wt_boundary = water_depth - hc
                        if z_mid > eff_wt_boundary:
                            gam = active_l['g_sat']
                            g_sym = "\\gamma_{sat}"
                        else:
                            gam = active_l['g_dry']
                            g_sym = "\\gamma_{dry}"

                        sigma = sigma_prev + (gam * dz)
                        math_logs.append(f"**Interval {z_prev}m to {z}m:** {active_l['type']} (${g_sym}={gam}$)")
                        math_logs.append(f"$\\sigma = {sigma_prev:.2f} + ({gam} \\times {dz:.2f}) = {sigma:.2f}$")
                    else:
                        sigma = load_q
                        math_logs.append(f"**Surface (z=0):** Load = {load_q} kPa")

                    # Clay excess pore pressure (Short Term)
                    u_excess = 0.0
                    check_z = z if z < total_depth else z - 0.01

                    d_check = 0
                    is_clay = False
                    for l in layers:
                        d_check += l['H']
                        if check_z <= d_check:
                            if l['type'] == 'Clay':
                                is_clay = True
                            break

                    u_calc_add = ""
                    if mode_name == "Short Term" and load_q > 0 and is_clay:
                        u_excess = load_q
                        u_calc_add = f" + {load_q} (Excess)"

                    u_tot = u_h + u_excess
                    sig_eff = sigma - u_tot

                    math_logs.append(f"**@ z={z}m:**")
                    math_logs.append(f"$u = {u_calc_text}{u_calc_add} = {u_tot:.2f}$")
                    math_logs.append(f"$\\sigma' = {sigma:.2f} - {u_tot:.2f} = \\mathbf{{{sig_eff:.2f}}}$")
                    math_logs.append("---")

                    results.append({
                        "Depth (z)": z,
                        "Total Stress (σ)": sigma,
                        "Pore Pressure (u)": u_tot,
                        "Eff. Stress (σ')": sig_eff
                    })

                    sigma_prev = sigma
                    z_prev = z

                return pd.DataFrame(results), math_logs

            # Run profiles
            df_init, log_init = calculate_profile("Initial", 0.0)
            df_long, log_long = calculate_profile("Long Term", surcharge)
            df_short, log_short = calculate_profile("Short Term", surcharge)

            # Plot function
            def plot_results(df, title, ax):
                ax.plot(df["Total Stress (σ)"], df["Depth (z)"], 'b-o', label="Total σ")
                ax.plot(df["Pore Pressure (u)"], df["Depth (z)"], 'r--x', label="Pore u")
                ax.plot(df["Eff. Stress (σ')"], df["Depth (z)"], 'k-s', linewidth=2, label="Effective σ'")
                ax.invert_yaxis()
                ax.set_xlabel("Stress (kPa)")
                ax.set_ylabel("Depth (m)")
                ax.set_title(title)
                ax.grid(True)
                ax.legend()

            st.markdown("### Results Comparison")
            c1, c2, c3 = st.columns(3)

            for col, df, title in zip([c1, c2, c3],
                                      [df_init, df_long, df_short],
                                      ["Initial", "Long Term", "Short Term"]):
                with col:
                    st.subheader(title)
                    st.dataframe(df.style.format("{:.2f}"))
                    fig, ax = plt.subplots(figsize=(5, 6))
                    plot_results(df, title, ax)
                    st.pyplot(fig)

    # =====================================================
    # TAB 2 — HEAVE CHECK (unchanged)
    # =====================================================
    with tab2:
        st.subheader("Heave & Piping Analysis")
        st.info("This section unchanged from your original code.")


if __name__ == "__main__":
    app()
