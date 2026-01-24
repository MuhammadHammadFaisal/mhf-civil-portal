import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def app():
    st.markdown("---")
    st.subheader("💧 Flow of Water & Seepage Analysis")

    # TABS FOR DIFFERENT PROBLEM TYPES
    tab1, tab2, tab3 = st.tabs(["1️⃣ 1D Seepage (Effective Stress)", "2️⃣ Permeability Tests", "3️⃣ Flow Nets & Piping"])

    # =================================================================
    # TAB 1: 1D SEEPAGE (The "Diagram" Problem)
    # =================================================================
    with tab1:
        st.caption("Determine Effective Stress at Point A. (Datum is at the Bottom of Soil)")
        
        col_setup, col_plot = st.columns([1, 1.2])
        
        with col_setup:
            st.markdown("### 1. Problem Setup")
            
            # 1. Soil Height (z)
            val_z = st.number_input("Soil Specimen Height (z) [m]", 0.1, step=0.5, value=4.0)
            
            # 2. Top Water (y)
            val_y = st.number_input("Water Height above Soil (y) [m]", 0.0, step=0.5, value=2.0)
            
            # 3. Bottom Head (x)
            val_x = st.number_input("Piezometer Head at Bottom (x) [m]", 0.0, step=0.5, value=7.5,
                                   help="This is the total head at the bottom boundary, measured from the Datum.")

            # 4. Soil Properties
            gamma_sat = st.number_input("Saturated Unit Weight (γ_sat) [kN/m³]", 18.0, step=0.1)
            gamma_w = 9.81

            # 5. Point A
            val_A = st.slider("Height of Point 'A' from Datum [m]", 0.0, val_z, val_z/2)

        # --- DYNAMIC MATPLOTLIB DIAGRAM (PROFESSIONAL CAD STYLE) ---
        with col_plot:
            fig, ax = plt.subplots(figsize=(7, 8))
            
            # COORDINATES
            datum_y = 0.0
            soil_w = 2.5
            soil_x = 3.5  # Moved right to make space for left arrows
            
            # Water Levels relative to Datum
            wl_top = val_z + val_y  
            wl_bot = val_x          
            
            # Flow Detection
            if wl_top > wl_bot:
                flow_arrow = "⬇️"
            elif wl_bot > wl_top:
                flow_arrow = "⬆️"
            else:
                flow_arrow = "No Flow"

            # --- DRAWING LAYERS ---
            # Strategy: Draw Fills first (Zorder 1), then Thick Walls (Zorder 2)
            
            # 1. SOIL FILL
            ax.add_patch(patches.Rectangle((soil_x, datum_y), soil_w, val_z, 
                                           facecolor='#E3C195', hatch='...', edgecolor='none', zorder=1))
            ax.text(soil_x + soil_w/2, datum_y + val_z/2, "SOIL", ha='center', fontweight='bold', fontsize=12, zorder=3)
            
            # 2. WATER FILLS (Blue areas without borders)
            # Top Tank Water
            tank_w = 2.0
            tank_x = soil_x + (soil_w - tank_w)/2
            neck_w = 0.8
            neck_x = soil_x + (soil_w - neck_w)/2
            tank_base_y = wl_top - 0.5
            if tank_base_y < datum_y + val_z: tank_base_y = datum_y + val_z # Prevent tank from sinking into soil
            
            # Top Tank Fill
            ax.add_patch(patches.Rectangle((tank_x, tank_base_y), tank_w, wl_top - tank_base_y, facecolor='#D6EAF8', edgecolor='none', zorder=1))
            # Neck Fill
            ax.add_patch(patches.Rectangle((neck_x, datum_y + val_z), neck_w, tank_base_y - (datum_y + val_z) + 0.1, facecolor='#D6EAF8', edgecolor='none', zorder=1))
            
            # Left Tank & Tube Fill
            tube_w = 0.6
            left_tank_x = 0.5
            l_tank_base_y = wl_bot - 0.5
            if l_tank_base_y > datum_y - 1.0: pass 
            else: l_tank_base_y = datum_y - 1.0 # Logic to keep tank valid
            
            # U-Tube Fill (One continuous polygon to avoid internal lines)
            # Vertical Down from Soil Center
            tube_start_x = soil_x + (soil_w - tube_w)/2
            
            ax.add_patch(patches.Rectangle((tube_start_x, datum_y - 1.0), tube_w, 1.0, facecolor='#D6EAF8', edgecolor='none', zorder=1))
            # Horizontal Left
            tube_left_end = left_tank_x + (tank_w - tube_w)/2
            ax.add_patch(patches.Rectangle((tube_left_end, datum_y - 1.0), tube_start_x - tube_left_end + tube_w, tube_w, facecolor='#D6EAF8', edgecolor='none', zorder=1))
            # Vertical Up to Left Tank
            ax.add_patch(patches.Rectangle((tube_left_end, datum_y - 1.0), tube_w, l_tank_base_y - (datum_y - 1.0) + 0.1, facecolor='#D6EAF8', edgecolor='none', zorder=1))
            # Left Tank Fill
            ax.add_patch(patches.Rectangle((left_tank_x, l_tank_base_y), tank_w, wl_bot - l_tank_base_y, facecolor='#D6EAF8', edgecolor='none', zorder=1))

            # --- 3. STRUCTURAL WALLS (Thick Continuous Lines) ---
            wall_thick = 2.5
            wall_color = 'black'
            
            # Top Tank Walls
            # Left side (Tank + Neck)
            ax.plot([tank_x, tank_x, neck_x, neck_x], [wl_top + 0.5, tank_base_y, tank_base_y, datum_y + val_z], color=wall_color, lw=wall_thick, zorder=2)
            # Right side (Tank + Neck)
            ax.plot([tank_x + tank_w, tank_x + tank_w, neck_x + neck_w, neck_x + neck_w], [wl_top + 0.5, tank_base_y, tank_base_y, datum_y + val_z], color=wall_color, lw=wall_thick, zorder=2)
            
            # Soil Box Walls
            ax.plot([soil_x, soil_x], [datum_y + val_z, datum_y], color=wall_color, lw=wall_thick, zorder=2) # Left
            ax.plot([soil_x + soil_w, soil_x + soil_w], [datum_y + val_z, datum_y], color=wall_color, lw=wall_thick, zorder=2) # Right
            
            # Bottom of Soil (Split for tube)
            ax.plot([soil_x, tube_start_x], [datum_y, datum_y], color=wall_color, lw=wall_thick, zorder=2)
            ax.plot([tube_start_x + tube_w, soil_x + soil_w], [datum_y, datum_y], color=wall_color, lw=wall_thick, zorder=2)
            
            # Bottom Tube & Left Tank Walls (Continuous Path)
            # Outer Path (Right side of tube -> Bottom -> Left Tank Right -> Top)
            path_outer_x = [tube_start_x + tube_w, tube_start_x + tube_w, tube_left_end + tube_w, tube_left_end + tube_w, left_tank_x + tank_w, left_tank_x + tank_w]
            path_outer_y = [datum_y, datum_y - 1.0 + tube_w, datum_y - 1.0 + tube_w, l_tank_base_y, l_tank_base_y, wl_bot + 0.5]
            ax.plot(path_outer_x, path_outer_y, color=wall_color, lw=wall_thick, zorder=2)
            
            # Inner Path (Left side of tube -> Bottom -> Left Tank Left -> Top)
            path_inner_x = [tube_start_x, tube_start_x, tube_left_end, tube_left_end, left_tank_x, left_tank_x]
            path_inner_y = [datum_y, datum_y - 1.0, datum_y - 1.0, l_tank_base_y, l_tank_base_y, wl_bot + 0.5]
            ax.plot(path_inner_x, path_inner_y, color=wall_color, lw=wall_thick, zorder=2)

            # Water Surfaces (Blue Lines)
            ax.plot([tank_x, tank_x + tank_w], [wl_top, wl_top], color='blue', lw=2, zorder=2)
            ax.plot([left_tank_x, left_tank_x + tank_w], [wl_bot, wl_bot], color='blue', lw=2, zorder=2)
            
            # Triangles
            ax.plot(tank_x + tank_w/2, wl_top, marker='v', color='blue', markersize=8, zorder=2)
            ax.plot(left_tank_x + tank_w/2, wl_bot, marker='v', color='blue', markersize=8, zorder=2)

            # --- 4. DIMENSIONS ---
            
            # Datum Line
            ax.plot([-0.5, 8], [datum_y, datum_y], 'k-.', lw=1)
            ax.text(soil_x + soil_w + 0.5, datum_y, "Datum (z=0)", va='center', fontsize=10, style='italic')

            # Dimension z (Soil Height) - LEFT SIDE
            dim_z_x = soil_x - 0.4
            ax.annotate('', xy=(dim_z_x, datum_y), xytext=(dim_z_x, datum_y + val_z), 
                        arrowprops=dict(arrowstyle='<->', color='black'))
            ax.text(dim_z_x - 0.1, val_z/2, f"z = {val_z:.2f}m", fontsize=10, ha='right')

            # Dimension y (Water Depth ABOVE Soil)
            dim_y_x = soil_x + soil_w + 0.8
            ax.annotate('', xy=(dim_y_x, val_z), xytext=(dim_y_x, wl_top), 
                        arrowprops=dict(arrowstyle='<->', color='blue'))
            ax.text(dim_y_x + 0.1, (val_z + wl_top)/2, f"y = {val_y:.2f}m", fontsize=11, fontweight='bold', color='blue', ha='left')
            # Extension lines
            ax.plot([soil_x + soil_w, dim_y_x + 0.2], [val_z, val_z], 'k--', lw=0.5)
            ax.plot([tank_x + tank_w, dim_y_x + 0.2], [wl_top, wl_top], 'k--', lw=0.5)

            # Dimension x (Total Head Bottom)
            dim_x_loc = left_tank_x - 0.4
            ax.annotate('', xy=(dim_x_loc, datum_y), xytext=(dim_x_loc, wl_bot), 
                        arrowprops=dict(arrowstyle='<->'))
            ax.text(dim_x_loc - 0.1, wl_bot/2, f"x = {val_x:.2f}m", fontsize=11, fontweight='bold', ha='right')

            # Point A (Dot)
            ax.scatter(soil_x + soil_w/2, datum_y + val_A, color='red', zorder=5, s=80, edgecolor='black')
            ax.text(soil_x + soil_w/2 + 0.2, datum_y + val_A + 0.1, f"Point A", color='red', fontweight='bold', zorder=5)
            
            # Dimension A (Shifted Right & Black Arrow)
            dim_A_x = soil_x + soil_w/2 + 0.5  # Shifted to the right of the center
            ax.annotate('', xy=(dim_A_x, datum_y), xytext=(dim_A_x, datum_y + val_A), 
                        arrowprops=dict(arrowstyle='<->', color='black')) # BLACK ARROW
            ax.text(dim_A_x + 0.1, val_A/2, f"A = {val_A:.2f}m", color='black', fontweight='bold', zorder=5)
            
            # Connect Dimension A to Point A with small dotted line for clarity
            ax.plot([soil_x + soil_w/2, dim_A_x], [datum_y + val_A, datum_y + val_A], 'k:', lw=1)

            ax.text(soil_x + soil_w/2, wl_top + 0.5, f"FLOW {flow_arrow}", ha='center', fontsize=12, fontweight='bold')

            ax.set_xlim(-1.5, 9)
            ax.set_ylim(datum_y - 1.5, max(wl_bot, wl_top) + 1)
            ax.axis('off')
            st.pyplot(fig)

        # --- CALCULATION LOGIC ---
        if st.button("🚀 Calculate Effective Stress"):
            # 1. Identify Heads
            H_top = val_z + val_y  # Total Head at Top (Datum + Soil + Water)
            H_bot = val_x          # Total Head at Bottom (Given directly as x)
            
            # 2. Flow Analysis
            h_loss = H_top - H_bot
            
            if h_loss > 0:
                flow_type = "Downward"
                effect_msg = "Downward Flow increases Effective Stress (+i·z·γw)"
            elif h_loss < 0:
                flow_type = "Upward"
                effect_msg = "Upward Flow decreases Effective Stress (-i·z·γw)"
            else:
                flow_type = "No Flow"
                effect_msg = "Hydrostatic Condition"

            # 3. Calculations
            i = abs(h_loss) / val_z  # Hydraulic Gradient
            
            # --- Method 1: Total Stress - Pore Pressure ---
            
            # Total Stress at A (Sigma)
            # Weight of water above soil + Weight of saturated soil above A
            # Depth of soil above A = z - A
            sigma_total = (val_y * gamma_w) + ((val_z - val_A) * gamma_sat)
            
            # Pore Pressure at A (u)
            # We calculate Total Head at A using linear interpolation
            # H(h) = H_bottom + (h/z) * (H_top - H_bottom) where h is height from datum
            H_A = H_bot + (val_A / val_z) * (H_top - H_bot)
            
            # Pressure Head = Total Head - Elevation Head
            h_p_A = H_A - val_A
            
            u_val = h_p_A * gamma_w
            
            sigma_prime = sigma_total - u_val
            
            # --- DISPLAY ---
            st.success(f"**Flow Condition:** {flow_type} ({effect_msg})")
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Total Stress (σ)", f"{sigma_total:.2f} kPa")
            with c2:
                st.metric("Pore Pressure (u)", f"{u_val:.2f} kPa")
            with c3:
                st.metric("Effective Stress (σ')", f"{sigma_prime:.2f} kPa")
                
            with st.expander("📝 View Step-by-Step Derivation"):
                st.markdown("**1. Heads & Gradient**")
                st.latex(rf"H_{{top}} = z + y = {val_z} + {val_y} = {H_top:.2f} m")
                st.latex(rf"H_{{bot}} = x = {H_bot:.2f} m")
                st.latex(rf"\Delta h = {H_top:.2f} - {H_bot:.2f} = {h_loss:.2f} m")
                st.latex(rf"i = \frac{{|\Delta h|}}{{z}} = \frac{{{abs(h_loss):.2f}}}{{{val_z}}} = {i:.3f}")
                
                st.markdown("**2. Stresses at Point A**")
                st.latex(rf"\sigma = (y \cdot \gamma_w) + ((z - A) \cdot \gamma_{{sat}})")
                st.latex(rf"\sigma = ({val_y} \cdot 9.81) + (({val_z} - {val_A}) \cdot {gamma_sat}) = {sigma_total:.2f} kPa")
                
                st.markdown("**3. Pore Pressure (via Bernoulli/Head)**")
                st.latex(rf"H_A = H_{{bot}} + \frac{{A}}{{z}}(H_{{top}} - H_{{bot}})")
                st.latex(rf"H_A = {H_bot} + \frac{{{val_A}}}{{{val_z}}}({H_top} - {H_bot}) = {H_A:.2f} m")
                st.latex(rf"u = (H_A - Z_A) \cdot \gamma_w = ({H_A:.2f} - {val_A}) \cdot 9.81 = {u_val:.2f} kPa")

    # =================================================================
    # TAB 2: PERMEABILITY (Lab Tests)
    # =================================================================
    with tab2:
        st.subheader("🧪 Permeability Tests")
        test_type = st.radio("Test Type", ["Constant Head", "Falling Head"], horizontal=True)
        
        if "Constant" in test_type:
            st.latex(r"k = \frac{Q \cdot L}{A \cdot h \cdot t}")
            c1, c2, c3 = st.columns(3)
            Q = c1.number_input("Volume (Q) [cm³]", 0.0)
            L = c2.number_input("Length (L) [cm]", 0.0)
            h = c3.number_input("Head (h) [cm]", 0.0)
            c4, c5 = st.columns(2)
            A = c4.number_input("Area (A) [cm²]", 0.0)
            t = c5.number_input("Time (t) [sec]", 0.0)
            if st.button("Calculate k"):
                if A*h*t > 0: st.success(f"k = {(Q*L)/(A*h*t):.4e} cm/sec")
        else:
            st.latex(r"k = 2.303 \frac{a \cdot L}{A \cdot t} \log_{10}\left(\frac{h_1}{h_2}\right)")
            c1, c2 = st.columns(2)
            a = c1.number_input("Standpipe Area (a)", 0.0, format="%.4f")
            A_soil = c2.number_input("Soil Area (A)", 0.0)
            L = c1.number_input("Length (L)", 0.0)
            t = c2.number_input("Time (t)", 0.0)
            h1 = c1.number_input("Start Head (h1)", 0.0)
            h2 = c2.number_input("End Head (h2)", 0.0)
            if st.button("Calculate k"):
                if A_soil*t > 0: st.success(f"k = {(2.303*a*L/(A_soil*t))*np.log10(h1/h2):.4e} cm/sec")

    # =================================================================
    # TAB 3: FLOW NETS
    # =================================================================
    with tab3:
        st.subheader("⚠️ Quick Sand & Seepage")
        st.latex(r"i_{cr} = \frac{G_s - 1}{1+e}")
        Gs = st.number_input("Gs", 2.65)
        e = st.number_input("Void Ratio e", 0.6)
        if st.button("Calculate Critical Gradient"):
            st.metric("i_critical", f"{(Gs-1)/(1+e):.3f}")

# For testing
if __name__ == "__main__":
    app()
