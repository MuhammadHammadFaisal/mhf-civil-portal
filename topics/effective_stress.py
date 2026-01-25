import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# =========================================================
# APP CONFIG (Must be the first Streamlit command)
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
        # 1. INPUTS + INPUT MONITOR
        # -------------------------------------------------
        st.markdown("## 1. Inputs")

        col_inputs, col_monitor = st.columns([2.0, 1.5])

        # ================= LEFT: INPUTS =================
        with col_inputs:
            
            # Analysis Settings
            analysis_mode = st.radio(
                "Analysis State:", 
                ["Long Term (Drained)", "Short Term (Undrained)"],
                help="Short Term: Surcharge creates excess pore pressure in CLAY layers only."
            )

            st.caption("Define global parameters below. Soil layers are defined in the next section.")

            c1, c2 = st.columns(2)
            with c1:
                water_depth = st.number_input("Water Table Depth (m)", value=2.0, step=0.1)
                hc = st.number_input("Capillary Rise (m)", value=0.0, step=0.1)
            with c2:
                surcharge = st.number_input("Surcharge q (kPa)", value=80.0, step=5.0)
                gamma_w = 9.81 # Constant

        # ================= RIGHT: INPUT MONITOR =================
        with col_monitor:
            st.markdown("### Input Monitor")
            # Drawing a generic Phase Diagram representation
            fig, ax = plt.subplots(figsize=(4, 3))
            ax.axis("off")
            
            # Draw containers
            # Solids (Bottom)
            ax.add_patch(patches.Rectangle((0.3, 0), 0.4, 0.5, facecolor="#D2B48C", edgecolor="black"))
            ax.text(0.5, 0.25, "Solids (S)", ha="center", va="center", fontsize=10, weight="bold")
            
            # Water (Middle)
            ax.add_patch(patches.Rectangle((0.3, 0.5), 0.4, 0.3, facecolor="#8fd3f4", edgecolor="black"))
            ax.text(0.5, 0.65, "Water (W)", ha="center", va="center", fontsize=10, weight="bold")
            
            # Air (Top)
            ax.add_patch(patches.Rectangle((0.3, 0.8), 0.4, 0.2, facecolor="white", edgecolor="black"))
            ax.text(0.5, 0.9, "Air (A)", ha="center", va="center", fontsize=10, weight="bold")

            # Annotations based on inputs
            ax.text(0.8, 0.9, r"$V_a$", fontsize=9)
            ax.text(0.8, 0.65, r"$V_w$", fontsize=9)
            ax.text(0.8, 0.25, r"$V_s=1$", fontsize=9)
            
            ax.text(0.5, 1.1, "Phase Diagram Concept", ha="center", color="gray")
            st.pyplot(fig, use_container_width=True)

        # -------------------------------------------------
        # 2. SOIL STRATIGRAPHY
        # -------------------------------------------------
        st.markdown("## 2. Soil Stratigraphy")

        num_layers = st.number_input("Number of Layers", 1, 5, 2)
        layers = []
        colors = {"Sand": "#E6D690", "Clay": "#B0A494"}

        depth_tracker = 0.0

        for i in range(int(num_layers)):
            with st.expander(f"Layer {i+1} (Top at {depth_tracker:.2f} m)", expanded=True):
                a, b, c, d = st.columns(4)

                soil_type = a.selectbox("Type", ["Sand", "Clay"], key=f"t{i}")
                thickness = b.number_input("Thickness (m)", 0.1, step=0.5, value=4.0, key=f"h{i}")
                gamma_sat = c.number_input("γ_sat (kN/m³)", value=20.0, step=0.1, key=f"gs{i}")
                gamma_dry = d.number_input("γ_dry (kN/m³)", value=17.0, step=0.1, key=f"gd{i}")

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
        st.markdown("---")
        if st.button("Calculate Stress Profile", type="primary"):

            # 1. Discretize Depth (Create calculation points)
            z_points = {0.0, total_depth} # Start with top and bottom
            current_depth = 0.0

            # Add Layer Boundaries
            for layer in layers:
                current_depth += layer["H"]
                z_points.add(round(current_depth, 3))

            # Add Water Table
            if 0 < water_depth < total_depth:
                z_points.add(water_depth)

            # Add Capillary Rise Top
            if hc > 0:
                cap_top = water_depth - hc
                if 0 < cap_top < total_depth:
                    z_points.add(cap_top)

            # Sort points
            z_points = sorted(list(z_points))

            # 2. Calculation Loop
            results = []
            sigma_prev = surcharge
            z_prev = 0.0

            for i, z in enumerate(z_points):
                
                # --- A. Pore Pressure (u) ---
                if z > water_depth:
                    # Hydrostatic
                    u_h = (z - water_depth) * gamma_w
                elif z > (water_depth - hc) and z <= water_depth:
                    # Capillary Suction (Negative)
                    u_h = -(water_depth - z) * gamma_w
                else:
                    # Dry
                    u_h = 0.0

                # --- B. Total Stress (sigma) ---
                if i == 0:
                    sigma = surcharge
                    # Determine soil type at surface for completeness
                    soil_here = layers[0]["type"]
                else:
                    dz = z - z_prev
                    z_mid = (z + z_prev) / 2 # Midpoint for checking layer props

                    # Find which layer we are in
                    depth_sum = 0
                    active_layer = None
                    for l in layers:
                        depth_sum += l["H"]
                        if z_mid <= depth_sum:
                            active_layer = l
                            break
                    
                    if active_layer is None: active_layer = layers[-1] # Fallback
                    
                    soil_here = active_layer["type"]
                    
                    # Decide Unit Weight (Sat vs Dry)
                    # If below Water Table OR in Capillary Zone -> Use Saturated
                    if z_mid > (water_depth - hc):
                        gamma_used = active_layer["g_sat"]
                    else:
                        gamma_used = active_layer["g_dry"]

                    # Accumulate Stress
                    sigma = sigma_prev + (gamma_used * dz)

                # --- C. Excess Pore Pressure (Undrained Condition) ---
                u_excess = 0.0
                
                # Check layer at this specific point z
                active_layer_at_point = None
                depth_check = 0
                for l in layers:
                    depth_check += l["H"]
                    if z <= depth_check and z > (depth_check - l["H"]):
                        active_layer_at_point = l
                        break
                
                # Fallback for boundaries
                if active_layer_at_point is None and z > 0:
                     # If at exact boundary, usually look at layer above or below depending on context.
                     # Here simplified: check layer we just calculated for.
                     active_layer_at_point = active_layer

                is_clay = (active_layer_at_point["type"] == "Clay") if active_layer_at_point else False
                
                # If Short Term AND Clay AND Saturated -> Excess u = Surcharge
                if "Short Term" in analysis_mode and is_clay and z > water_depth:
                    u_excess = surcharge

                # --- D. Final Calculations ---
                u_total = u_h + u_excess
                sigma_eff = sigma - u_total

                results.append({
                    "Depth (m)": z,
                    "Total Stress σ": sigma,
                    "Pore Pressure u": u_total,
                    "Eff. Stress σ'": sigma_eff
                })

                sigma_prev = sigma
                z_prev = z

            df = pd.DataFrame(results)

            # -------------------------------------------------
            # 4. RESULTS VISUALIZATION
            # -------------------------------------------------
            st.markdown("## 2. Results")

            col_res1, col_res2 = st.columns([1, 2])

            with col_res1:
                st.dataframe(df.style.format("{:.2f}"))

            with col_res2:
                fig, ax = plt.subplots(figsize=(8, 6))

                # Background Layers
                cur = 0
                for l in layers:
                    ax.axhspan(cur, cur + l["H"], color=l["color"], alpha=0.3)
                    # Label the layer on the plot
                    ax.text(df["Total Stress σ"].max()*0.8, cur + l["H"]/2, l["type"], 
                            ha="center", va="center", alpha=0.5, fontsize=9)
                    cur += l["H"]

                # Plot Lines
                ax.plot(df["Total Stress σ"], df["Depth (m)"], label=r"Total $\sigma$", marker="o", color="blue")
                ax.plot(df["Pore Pressure u"], df["Depth (m)"], label=r"Pore $u$", linestyle="--", color="red")
                ax.plot(df["Eff. Stress σ'"], df["Depth (m)"], label=r"Effective $\sigma'$", linewidth=3, color="black")

                # Water Table Line
                ax.axhline(water_depth, color="blue", linestyle="-.", label="Water Table")

                ax.set_ylim(max(z_points) * 1.05, 0) # Invert Y Axis
                ax.set_xlabel("Stress (kPa)")
                ax.set_ylabel("Depth (m)")
                ax.set_title("Stress Distribution with Depth")
                ax.grid(True, linestyle=":", alpha=0.6)
                ax.legend()

                st.pyplot(fig)

    # =====================================================
    # TAB 2 — HEAVE CHECK
    # =====================================================
    with tab2:
        st.subheader("Bottom Heave & Piping Check")
        st.info("Checks safety against heave for an excavation in Clay overlying an Artesian Sand layer.")

        c1, c2 = st.columns(2)
        with c1:
            h_clay = st.number_input("Total Clay Thickness (m)", value=5.0)
            gamma_clay = st.number_input("Clay Unit Weight (kN/m³)", value=20.0)
        with c2:
            artesian_head = st.number_input("Artesian Head above Surface (m)", value=2.0)
            excavation_depth = st.number_input("Excavation Depth (m)", value=3.0)

        if st.button("Check Heave Safety"):
            remaining = h_clay - excavation_depth

            if remaining <= 0:
                st.error("Excavation exceeds clay thickness! (No clay left to resist uplift)")
            else:
                # Downward Force (Weight of remaining clay)
                sigma_down = remaining * gamma_clay
                
                # Upward Force (Artesian Pressure at bottom of clay)
                # Pressure head at bottom = (H_clay + Head_above_surface)
                # Note: Pressure acts at the interface.
                total_head_at_bottom = h_clay + artesian_head
                u_up = total_head_at_bottom * 9.81
                
                FS = sigma_down / u_up

                st.markdown(f"**Remaining Clay Thickness:** {remaining:.2f} m")
                st.latex(
                    rf"FS = \frac{{\sigma_{{down}}}}{{u_{{up}}}} = \frac{{{remaining:.2f} \times {gamma_clay}}}{{{total_head_at_bottom:.2f} \times 9.81}} = \mathbf{{{FS:.3f}}}"
                )

                if FS < 1.0:
                    st.error("❌ UNSAFE — Bottom Heave Expected")
                elif FS < 1.2:
                    st.warning("⚠️ Marginal Safety (FS < 1.2)")
                else:
                    st.success("✅ Safe Against Heave")

# =========================================================
# RUN APP
# =========================================================
if __name__ == "__main__":
    app()
