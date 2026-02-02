import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# =========================================================
# APP CONFIG
# =========================================================
st.set_page_config(page_title="Soil Stress Analysis", layout="wide")

GAMMA_W = 9.81  

# =========================================================
# MAIN APP
# =========================================================
def app():
    st.title("Effective Stress Analysis")
    st.markdown("---")

    # Use a container to keep the layout clean (Left = Inputs, Right = Profile)
    col_input, col_viz = st.columns([1, 1.2])

    # =====================================================
    # LEFT COLUMN: MANDATORY INPUTS
    # =====================================================
    with col_input:
        st.subheader("1. Soil Profile Inputs")
        
        # --- A. Global Parameters ---
        with st.container(border=True):
            st.markdown("**Global Conditions**")
            c1, c2 = st.columns(2)
            with c1:
                water_depth = st.number_input("Water Table Depth (m)", value=3.0, step=0.5)
                surcharge = st.number_input("Surcharge q (kPa)", value=0.0, step=5.0)
            with c2:
                hc = st.number_input("Capillary Rise (m)", value=0.0, step=0.1)

        # --- B. Stratigraphy ---
        st.write("")
        st.markdown("**Soil Stratigraphy (Mandatory)**")
        num_layers = st.number_input("Number of Layers", 1, 5, 2)
        layers = []
        colors = {"Sand": "#E6D690", "Clay": "#B0A494"}
        
        # Validation Flag
        all_inputs_valid = True

        depth_tracker = 0.0

        for i in range(int(num_layers)):
            with st.expander(f"Layer {i+1} (Top: {depth_tracker:.1f}m)", expanded=True):
                # Row 1: Type and Thickness
                r1_c1, r1_c2 = st.columns(2)
                soil_type = r1_c1.selectbox("Soil Type", ["Sand", "Clay"], key=f"t{i}")
                thickness = r1_c2.number_input("Thickness (m)", 0.1, 50.0, 4.0, step=0.5, key=f"h{i}")

                layer_top = depth_tracker
                layer_bot = depth_tracker + thickness
                eff_wt = water_depth - hc
                
                # Determine which unit weights are required based on Water Table
                needs_dry = layer_top < eff_wt  # Part of layer is above water/capillary
                needs_sat = layer_bot > eff_wt  # Part of layer is below water/capillary

                # Row 2: Unit Weights (Defaults set to 0.0 to force input)
                r2_c1, r2_c2 = st.columns(2)
                
                g_sat_val = 0.0
                g_dry_val = 0.0

                # Input for Saturated Unit Weight
                if needs_sat:
                    g_sat_val = r2_c1.number_input(f"γ_sat (kN/m³) [Required]", min_value=0.0, value=0.0, step=0.1, key=f"gs{i}")
                    if g_sat_val == 0.0:
                        r2_c1.error("⚠ Required")
                        all_inputs_valid = False
                else:
                    r2_c1.text_input("γ_sat", value="N/A", disabled=True, key=f"gs_d{i}")

                # Input for Dry Unit Weight
                if needs_dry:
                    g_dry_val = r2_c2.number_input(f"γ_dry (kN/m³) [Required]", min_value=0.0, value=0.0, step=0.1, key=f"gd{i}")
                    if g_dry_val == 0.0:
                        r2_c2.error("⚠ Required")
                        all_inputs_valid = False
                else:
                    r2_c2.text_input("γ_dry", value="N/A", disabled=True, key=f"gd_d{i}")

                layers.append({
                    "id": i+1,
                    "type": soil_type,
                    "top": layer_top,
                    "bot": layer_bot,
                    "H": thickness,
                    "g_sat": g_sat_val,
                    "g_dry": g_dry_val,
                    "color": colors[soil_type]
                })

                depth_tracker += thickness

        total_depth = depth_tracker

    # =====================================================
    # RIGHT COLUMN: VISUAL PROFILE
    # =====================================================
    with col_viz:
        st.subheader("2. Soil Profile Visualization")
        
        fig, ax = plt.subplots(figsize=(6, 6))
        
        # Draw Layers
        for lay in layers:
            # Main Box
            rect = patches.Rectangle((0, lay['top']), 6, lay['H'], 
                                     facecolor=lay['color'], edgecolor='black', linewidth=1.5)
            ax.add_patch(rect)
            
            # Label: Center of Layer
            mid_y = lay['top'] + lay['H']/2
            ax.text(3, mid_y, f"{lay['type']}", ha='center', va='center', fontweight='bold', fontsize=10)
            
            # Label: Depth Marker (Bottom line)
            ax.text(-0.6, lay['bot'], f"{lay['bot']:.1f}m", va='center', ha='right', fontsize=9)

        # Draw Surcharge
        if surcharge > 0:
            for x in np.linspace(0.5, 5.5, 10):
                ax.arrow(x, -0.7, 0, 0.6, head_width=0.15, fc='red', ec='red')
            ax.text(3, -0.9, f"q = {surcharge} kPa", color='red', ha='center', fontweight='bold')

        # Draw Water Table
        ax.axhline(water_depth, color='blue', linestyle='--', linewidth=2)
        ax.text(6.1, water_depth, "▽ WT", color='blue', va='center', fontweight='bold')
        ax.text(-0.6, water_depth, f"{water_depth}m", color='blue', va='center', ha='right')

        # Draw Capillary Zone
        if hc > 0:
            cap_top = water_depth - hc
            rect_cap = patches.Rectangle((0, cap_top), 6, hc, hatch='///', fill=False, edgecolor='blue', alpha=0.5)
            ax.add_patch(rect_cap)
            ax.text(6.1, cap_top, f"Capillary ({hc}m)", color='blue', fontsize=8, va='center')

        # Formatting
        ax.set_ylim(total_depth * 1.1, -2)
        ax.set_xlim(0, 6)
        ax.axis('off') # Turn off standard axis, we drew our own depth markers
        
        # Ground Line
        ax.plot([0, 6], [0, 0], 'k-', linewidth=2)
        ax.text(-0.6, 0, "0.0m", va='center', ha='right', fontsize=9)

        st.pyplot(fig)

    # =====================================================
    # CALCULATION SECTION (BELOW COLUMNS)
    # =====================================================
    st.markdown("---")
    
    calc_col1, calc_col2 = st.columns([1, 3])
    
    with calc_col1:
        # BUTTON IS DISABLED IF INPUTS ARE INVALID
        if all_inputs_valid:
            trigger = st.button("Calculate Stress Profile", type="primary", use_container_width=True)
        else:
            st.warning("Please fill in all required unit weights above.")
            trigger = False

    if trigger and all_inputs_valid:
        
        # --- CORE CALCULATION LOGIC (LAYER-BY-LAYER) ---
        def calculate_profile(mode_name, load_q):
            results = []
            sigma_prev = load_q
            
            # Iterate strictly layer by layer
            for layer in layers:
                
                # Define key points: Top, Mid-points (integers), Bottom
                # We force calculations at specific Zs to capture the profile
                z_in_layer = {layer['top'], layer['bot']}
                
                # Add integer depths inside the layer
                for d in range(int(layer['top']), int(layer['bot']) + 1):
                    if layer['top'] < d < layer['bot']:
                        z_in_layer.add(float(d))
                
                # Add Water Table / Capillary if inside
                if layer['top'] < water_depth < layer['bot']: z_in_layer.add(water_depth)
                cap_top = water_depth - hc
                if layer['top'] < cap_top < layer['bot']: z_in_layer.add(cap_top)
                
                sorted_z = sorted(list(z_in_layer))
                z_internal_prev = layer['top']
                
                for z in sorted_z:
                    # Skip z if it matches the previous (e.g. at Top)
                    if z == z_internal_prev and z != layer['top']:
                        continue
                        
                    dz = z - z_internal_prev
                    z_mid = (z + z_internal_prev) / 2
                    
                    # 1. Determine Unit Weight (Above vs Below Effective WT)
                    eff_wt_boundary = water_depth - hc
                    if z_mid > eff_wt_boundary:
                        gam = layer['g_sat']
                    else:
                        gam = layer['g_dry']
                        
                    # 2. Calculate Total Stress Increment
                    sigma = sigma_prev + (gam * dz)
                    
                    # 3. Calculate Pore Pressure
                    u_h = 0.0
                    if z > water_depth:
                        u_h = (z - water_depth) * GAMMA_W
                    elif z > (water_depth - hc):
                        u_h = -(water_depth - z) * GAMMA_W
                    
                    # Excess Pore Pressure (Short Term Logic)
                    u_excess = 0.0
                    if mode_name == "Short Term" and load_q > 0 and layer['type'] == "Clay":
                        u_excess = load_q
                        
                    u_tot = u_h + u_excess
                    sig_eff = sigma - u_tot
                    
                    # Labeling for Table
                    pos_label = ""
                    if abs(z - layer['top']) < 0.001: pos_label = " (Top)"
                    elif abs(z - layer['bot']) < 0.001: pos_label = " (Bottom)"
                    
                    results.append({
                        "Depth (m)": z,
                        "Soil Type": f"{layer['type']}{pos_label}",
                        "Total Stress (σ)": sigma,
                        "Pore Water (u)": u_tot,
                        "Effective (σ')": sig_eff
                    })
                    
                    # Update trackers
                    sigma_prev = sigma
                    z_internal_prev = z
                    
            return pd.DataFrame(results)

        # Run Calculations
        df_init = calculate_profile("Initial", 0.0)
        df_short = calculate_profile("Short Term", surcharge)
        df_long = calculate_profile("Long Term", surcharge)

        # Display Results
        with st.container():
            st.subheader("Calculation Results")
            t1, t2, t3 = st.tabs(["Initial State", "Short Term (Immediate)", "Long Term (Consolidated)"])
            
            def show_tab(df, title):
                # Custom Styling for the table to highlight changes
                st.dataframe(
                    df.style.format("{:.2f}")
                    .background_gradient(subset=["Effective (σ')"], cmap="Blues"),
                    use_container_width=True
                )
                
                # Plotting Results
                fig, ax = plt.subplots(figsize=(8, 5))
                ax.plot(df["Total Stress (σ)"], df["Depth (m)"], 'b-o', label="Total σ")
                ax.plot(df["Pore Water (u)"], df["Depth (m)"], 'r--x', label="Pore u")
                ax.plot(df["Effective (σ')"], df["Depth (m)"], 'k-s', linewidth=2, label="Effective σ'")
                ax.invert_yaxis()
                ax.set_xlabel("Stress (kPa)")
                ax.set_ylabel("Depth (m)")
                ax.grid(True, linestyle=':', alpha=0.6)
                ax.legend()
                ax.set_title(f"Stress Profile: {title}")
                st.pyplot(fig)

            with t1: show_tab(df_init, "Initial")
            with t2: show_tab(df_short, "Short Term (Clay Undrained)")
            with t3: show_tab(df_long, "Long Term (Fully Drained)")

if __name__ == "__main__":
    app()
