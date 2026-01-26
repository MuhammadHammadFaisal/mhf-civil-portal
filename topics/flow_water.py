import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def app():
    st.markdown("---")
    st.subheader("Flow of Water & Seepage Analysis")

    # TABS FOR DIFFERENT PROBLEM TYPES
    tab1, tab2, tab3 = st.tabs(["1D Seepage (Effective Stress)", "Permeability Tests", "Flow Nets & Piping"])

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

            st.markdown("---")
            
            # --- BUTTON & CALCULATION LOGIC ---
            if st.button("Calculate Effective Stress", type="primary"):
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
                sigma_total = (val_y * gamma_w) + ((val_z - val_A) * gamma_sat)
                
                # Pore Pressure at A (u)
                # H(h) = H_bottom + (h/z) * (H_top - H_bottom) where h is height from datum
                H_A = H_bot + (val_A / val_z) * (H_top - H_bot)
                
                # Pressure Head = Total Head - Elevation Head
                h_p_A = H_A - val_A
                
                u_val = h_p_A * gamma_w
                
                sigma_prime = sigma_total - u_val
                
                # --- DISPLAY RESULTS ---
                st.success(f"**Flow Condition:** {flow_type}\n\n*{effect_msg}*")
                
                st.metric("Total Stress (σ)", f"{sigma_total:.2f} kPa")
                st.metric("Pore Pressure (u)", f"{u_val:.2f} kPa")
                st.metric("Effective Stress (σ')", f"{sigma_prime:.2f} kPa")
                    
                with st.expander("View Step-by-Step Derivation"):
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

        # --- DYNAMIC MATPLOTLIB DIAGRAM ---
        with col_plot:
            fig, ax = plt.subplots(figsize=(7, 8))
            
            # COORDINATES
            datum_y = 0.0
            soil_w = 2.5
            soil_x = 3.5  
            
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
            
            # 1. SOIL FILL
            ax.add_patch(patches.Rectangle((soil_x, datum_y), soil_w, val_z, 
                                           facecolor='#E3C195', hatch='...', edgecolor='none', zorder=1))
            ax.text(soil_x + soil_w/2, datum_y + val_z/2, "SOIL", ha='center', fontweight='bold', fontsize=12, zorder=3)
            
            # 2. WATER FILLS
            tank_w = 2.0
            tank_x = soil_x + (soil_w - tank_w)/2
            neck_w = 0.8
            neck_x = soil_x + (soil_w - neck_w)/2
            tank_base_y = wl_top - 0.5
            if tank_base_y < datum_y + val_z: tank_base_y = datum_y + val_z 
            
            # Top Tank Fill
            ax.add_patch(patches.Rectangle((tank_x, tank_base_y), tank_w, wl_top - tank_base_y, facecolor='#D6EAF8', edgecolor='none', zorder=1))
            ax.add_patch(patches.Rectangle((neck_x, datum_y + val_z), neck_w, tank_base_y - (datum_y + val_z) + 0.1, facecolor='#D6EAF8', edgecolor='none', zorder=1))
            
            # Left Tank & Tube Fill
            tube_w = 0.6
            left_tank_x = 0.5
            l_tank_base_y = wl_bot - 0.5
            if l_tank_base_y < datum_y - 1.0: l_tank_base_y = datum_y - 1.0 
            
            tube_start_x = soil_x + (soil_w - tube_w)/2
            
            # U-Tube Fill 
            ax.add_patch(patches.Rectangle((tube_start_x, datum_y - 1.0), tube_w, 1.0, facecolor='#D6EAF8', edgecolor='none', zorder=1))
            tube_left_end = left_tank_x + (tank_w - tube_w)/2
            ax.add_patch(patches.Rectangle((tube_left_end, datum_y - 1.0), tube_start_x - tube_left_end + tube_w, tube_w, facecolor='#D6EAF8', edgecolor='none', zorder=1))
            ax.add_patch(patches.Rectangle((tube_left_end, datum_y - 1.0), tube_w, l_tank_base_y - (datum_y - 1.0) + 0.1, facecolor='#D6EAF8', edgecolor='none', zorder=1))
            ax.add_patch(patches.Rectangle((left_tank_x, l_tank_base_y), tank_w, wl_bot - l_tank_base_y, facecolor='#D6EAF8', edgecolor='none', zorder=1))

            # --- 3. STRUCTURAL WALLS ---
            wall_thick = 2.5
            wall_color = 'black'
            
            # Top Tank Walls
            ax.plot([tank_x, tank_x, neck_x, neck_x], [wl_top + 0.5, tank_base_y, tank_base_y, datum_y + val_z], color=wall_color, lw=wall_thick, zorder=2)
            ax.plot([tank_x + tank_w, tank_x + tank_w, neck_x + neck_w, neck_x + neck_w], [wl_top + 0.5, tank_base_y, tank_base_y, datum_y + val_z], color=wall_color, lw=wall_thick, zorder=2)
            
            # Soil Box Walls
            ax.plot([soil_x, soil_x], [datum_y + val_z, datum_y], color=wall_color, lw=wall_thick, zorder=2) 
            ax.plot([soil_x + soil_w, soil_x + soil_w], [datum_y + val_z, datum_y], color=wall_color, lw=wall_thick, zorder=2) 
            
            # Bottom of Soil
            ax.plot([soil_x, tube_start_x], [datum_y, datum_y], color=wall_color, lw=wall_thick, zorder=2)
            ax.plot([tube_start_x + tube_w, soil_x + soil_w], [datum_y, datum_y], color=wall_color, lw=wall_thick, zorder=2)
           
            # Top of Soil
            ax.plot([soil_x, neck_x], [datum_y + val_z , datum_y + val_z], color=wall_color, lw=wall_thick, zorder=2)
            ax.plot([neck_x + neck_w, soil_x + soil_w], [datum_y + val_z , datum_y + val_z], color=wall_color, lw=wall_thick, zorder=2) 
            
            # Bottom Tube & Left Tank Walls
            path_outer_x = [tube_start_x , tube_start_x , tube_left_end + tube_w, tube_left_end + tube_w, left_tank_x + tank_w, left_tank_x + tank_w]
            path_outer_y = [datum_y, datum_y - 1.0 + tube_w, datum_y - 1.0 + tube_w, l_tank_base_y, l_tank_base_y, wl_bot + 0.5]
            ax.plot(path_outer_x, path_outer_y, color=wall_color, lw=wall_thick, zorder=2)
            
            path_inner_x = [tube_start_x + tube_w, tube_start_x + tube_w, tube_left_end, tube_left_end, left_tank_x, left_tank_x]
            path_inner_y = [datum_y, datum_y - 1.0, datum_y - 1.0, l_tank_base_y, l_tank_base_y, wl_bot + 0.5]
            ax.plot(path_inner_x, path_inner_y, color=wall_color, lw=wall_thick, zorder=2)

            # Water Surfaces
            ax.plot([tank_x, tank_x + tank_w], [wl_top, wl_top], color='blue', lw=2, zorder=2)
            ax.plot([left_tank_x, left_tank_x + tank_w], [wl_bot, wl_bot], color='blue', lw=2, zorder=2)
            
            # Triangles
            ax.plot(tank_x + tank_w/2, wl_top, marker='v', color='blue', markersize=8, zorder=2)
            ax.plot(left_tank_x + tank_w/2, wl_bot, marker='v', color='blue', markersize=8, zorder=2)

            # --- 4. DIMENSIONS ---
            
            # Datum Line
            ax.plot([-0.5, 8], [datum_y, datum_y], 'k-.', lw=1)
            ax.text(soil_x + 0.5 + soil_w, datum_y - 0.25, "Datum (z=0)", va='center', fontsize=10, style='italic')

            # Dimension z
            dim_z_x = soil_x - 0.4
            ax.annotate('', xy=(dim_z_x, datum_y), xytext=(dim_z_x, datum_y + val_z), 
                        arrowprops=dict(arrowstyle='<->', color='black'))
            ax.text(dim_z_x - 0.1, val_z/2, f"z = {val_z:.2f}m", fontsize=10, ha='right')

            # Dimension y
            dim_y_x = soil_x + soil_w + 0.8
            ax.annotate('', xy=(dim_y_x, val_z), xytext=(dim_y_x, wl_top), 
                        arrowprops=dict(arrowstyle='<->', color='black'))
            ax.text(dim_y_x + 0.1, (val_z + wl_top)/2, f"y = {val_y:.2f}m", fontsize=11, fontweight='bold', color='black', ha='left')
            ax.plot([soil_x + soil_w, dim_y_x + 0.2], [val_z, val_z], 'k--', lw=0.5)
            ax.plot([tank_x + tank_w, dim_y_x + 0.2], [wl_top, wl_top], 'k--', lw=0.5)

            # Dimension x
            dim_x_loc = left_tank_x - 0.4
            ax.annotate('', xy=(dim_x_loc, datum_y), xytext=(dim_x_loc, wl_bot), 
                        arrowprops=dict(arrowstyle='<->'))
            ax.text(dim_x_loc - 0.1, wl_bot/2, f"x = {val_x:.2f}m", fontsize=11, fontweight='bold', ha='right')

            # Point A
            ax.scatter(soil_x + soil_w/2 + 2.0, datum_y + val_A, color='Black', zorder=5, s=80, edgecolor='black')
            ax.text(soil_x + soil_w/2 + 2.2, datum_y + val_A + 0.1, f"Point A", color='Black', fontweight='bold', zorder=5)
            
            # Dimension A
            dim_A_x = soil_x + soil_w/2 + 2.0
            ax.annotate('', xy=(dim_A_x, datum_y), xytext=(dim_A_x, datum_y + val_A), 
                        arrowprops=dict(arrowstyle='<->', color='black'))
            ax.text(dim_A_x + 0.1, val_A/2, f"A = {val_A:.2f}m", color='black', fontweight='bold', zorder=5)
            ax.plot([soil_x + soil_w/2, dim_A_x], [datum_y + val_A, datum_y + val_A], 'k:', lw=1)

            ax.text(soil_x + soil_w/2, wl_top + 0.5, f"FLOW {flow_arrow}", ha='center', fontsize=12, fontweight='bold')

            ax.set_xlim(-1.5, 9)
            ax.set_ylim(datum_y - 1.5, max(wl_bot, wl_top) + 1)
            ax.axis('off')
            st.pyplot(fig)


    # =================================================================
    # TAB 2: PERMEABILITY (Lab Tests)
    # =================================================================
    with tab2:
        st.caption("Calculate Coefficient of Permeability (k) from Lab Tests.")
        col_input_2, col_plot_2 = st.columns([1, 1.2])

        with col_input_2:
            st.markdown("### 1. Test Configuration")
            test_type = st.radio("Select Method", ["Constant Head", "Falling Head"], horizontal=True)
            st.markdown("---")

            if "Constant" in test_type:
                # Constant Head Setup
                st.latex(r"k = \frac{Q \cdot L}{A \cdot h \cdot t}")
                
                Q = st.number_input("Collected Volume (Q) [cm³]", 0.0, step=10.0, value=500.0)
                L = st.number_input("Specimen Length (L) [cm]", 0.0, step=1.0, value=15.0)
                h = st.number_input("Constant Head Diff (h) [cm]", 0.0, step=1.0, value=20.0)
                A = st.number_input("Specimen Area (A) [cm²]", 0.0, step=1.0, value=40.0)
                t = st.number_input("Time Interval (t) [sec]", 0.0, step=1.0, value=60.0)
                
                st.markdown("---")
                if st.button("Calculate Permeability (k)", type="primary"):
                    if A*h*t > 0: 
                        k_val = (Q*L)/(A*h*t)
                        # UPGRADE: Use st.metric for consistent look
                        st.success("Calculation Successful")
                        st.metric("Permeability Coefficient (k)", f"{k_val:.4e} cm/sec")
                    else:
                        st.error("Inputs must be positive.")

            else:
                # Falling Head Setup
                st.latex(r"k = 2.303 \frac{a \cdot L}{A \cdot t} \log_{10}\left(\frac{h_1}{h_2}\right)")
                
                a = st.number_input("Standpipe Area (a) [cm²]", 0.0, format="%.4f", step=0.1, value=0.5)
                A_soil = st.number_input("Soil Specimen Area (A) [cm²]", 0.0, step=1.0, value=40.0)
                L_fall = st.number_input("Specimen Length (L) [cm]", 0.0, step=1.0, value=15.0)
                h1 = st.number_input("Initial Head (h1) [cm]", 0.0, step=1.0, value=30.0)
                h2 = st.number_input("Final Head (h2) [cm]", 0.0, step=1.0, value=15.0)
                t_fall = st.number_input("Time Interval (t) [sec]", 0.0, step=1.0, value=300.0)

                st.markdown("---")
                if st.button("Calculate Permeability (k)", type="primary"):
                    if A_soil*t_fall > 0 and h2 > 0: 
                        k_val = (2.303*a*L_fall/(A_soil*t_fall))*np.log10(h1/h2)
                        # UPGRADE: Use st.metric for consistent look
                        st.success("Calculation Successful")
                        st.metric("Permeability Coefficient (k)", f"{k_val:.4e} cm/sec")
                    else:
                        st.error("Inputs invalid. h2 must be > 0.")

        with col_plot_2:
            fig2, ax2 = plt.subplots(figsize=(6, 6))
            ax2.set_xlim(0, 10)
            ax2.set_ylim(0, 10)
            ax2.axis('off')

            if "Constant" in test_type:
                # --- CONSTANT HEAD SCHEMATIC ---
                # Soil Sample
                ax2.add_patch(patches.Rectangle((3, 3), 4, 4, facecolor='#E3C195', hatch='..', edgecolor='black'))
                ax2.text(5, 5, "Soil Sample\n(Area A)", ha='center', va='center', fontweight='bold')
                
                # Inlet Pipe (Top)
                ax2.add_patch(patches.Rectangle((4.5, 7), 1, 2, facecolor='#D6EAF8', edgecolor='black'))
                ax2.text(5, 8, "Inlet", ha='center', fontsize=8)
                
                # Piezometers
                ax2.plot([3.5, 2], [6.5, 6.5], 'k-') # Top Tap
                ax2.plot([2, 2], [6.5, 9], 'k-', lw=1.5) # Top Tube
                ax2.plot([3.5, 2], [3.5, 3.5], 'k-') # Bot Tap
                ax2.plot([2, 2], [3.5, 7.5], 'k-', lw=1.5) # Bot Tube (lower)

                # Water Levels
                ax2.plot([1.8, 2.2], [8.5, 8.5], 'b-', lw=2) # High head
                ax2.plot([1.8, 2.2], [4.5, 4.5], 'b-', lw=2) # Low head

                # Dimension h
                ax2.annotate('', xy=(1.5, 4.5), xytext=(1.5, 8.5), arrowprops=dict(arrowstyle='<->'))
                ax2.text(1.2, 6.5, "h", ha='right', fontweight='bold')
                
                # Dimension L
                ax2.annotate('', xy=(7.5, 3), xytext=(7.5, 7), arrowprops=dict(arrowstyle='<->'))
                ax2.text(7.8, 5, "L", ha='left', fontweight='bold')
                
                # Collection
                ax2.text(5, 2, "Q (Collected Volume)\nmeasured over time t", ha='center', style='italic', fontsize=9, bbox=dict(facecolor='white', edgecolor='blue'))

            else:
                # --- FALLING HEAD SCHEMATIC ---
                # Soil Sample
                ax2.add_patch(patches.Rectangle((3, 1), 4, 3, facecolor='#E3C195', hatch='..', edgecolor='black'))
                ax2.text(5, 2.5, "Soil Sample\n(Area A)", ha='center', va='center', fontweight='bold')

                # Standpipe (Narrow)
                ax2.add_patch(patches.Rectangle((4.5, 4), 1, 5, facecolor='#D6EAF8', edgecolor='black', alpha=0.3))
                ax2.text(6.0, 7.5, "Standpipe\n(Area a)", ha='left', fontsize=9)
                
                # Water Levels
                ax2.plot([4.5, 5.5], [8.5, 8.5], 'b-', lw=2) # h1
                ax2.text(4.2, 8.5, "h1 (start)", ha='right')
                
                ax2.plot([4.5, 5.5], [6.0, 6.0], 'b--', lw=2) # h2
                ax2.text(4.2, 6.0, "h2 (end)", ha='right')

                # Arrow for drop
                ax2.annotate('', xy=(5, 6), xytext=(5, 8.5), arrowprops=dict(arrowstyle='->', color='blue'))
                ax2.text(5.2, 7.2, "dt", color='blue')

                # L Dimension
                ax2.annotate('', xy=(7.5, 1), xytext=(7.5, 4), arrowprops=dict(arrowstyle='<->'))
                ax2.text(7.8, 2.5, "L", ha='left', fontweight='bold')

            st.pyplot(fig2)

    # =================================================================
    # TAB 3: FLOW NETS (Quick Sand)
    # =================================================================
    with tab3:
        st.caption("Calculate Critical Hydraulic Gradient and visualize Seepage Force.")
        col_input_3, col_plot_3 = st.columns([1, 1.2])

        with col_input_3:
            st.markdown("### 1. Soil Parameters")
            st.latex(r"i_{cr} = \frac{G_s - 1}{1+e}")
            
            Gs = st.number_input("Specific Gravity (Gs)", 2.0, 3.0, 2.65, step=0.01)
            e = st.number_input("Void Ratio (e)", 0.1, 2.0, 0.60, step=0.01)
            
            st.markdown("---")
            if st.button("Calculate Critical Gradient", type="primary"):
                icr = (Gs - 1) / (1 + e)
                # UPGRADE: Use st.metric for consistent look
                st.success("Calculation Successful")
                st.metric("Critical Gradient (i_cr)", f"{icr:.3f}")
                
                st.info("""
                **What does this mean?**
                If the upward hydraulic gradient (i) exceeds this value, 
                the Effective Stress becomes zero.
                
                **Condition:** Boiling / Quick Sand
                """)

        with col_plot_3:
            # --- CONCEPTUAL DIAGRAM FOR QUICK SAND ---
            fig3, ax3 = plt.subplots(figsize=(6, 6))
            ax3.set_xlim(0, 10)
            ax3.set_ylim(0, 10)
            ax3.axis('off')

            # Soil Element Block
            ax3.add_patch(patches.Rectangle((3, 3), 4, 4, facecolor='#E3C195', hatch='X', edgecolor='black', lw=2))
            ax3.text(5, 5, "Soil\nElement", ha='center', fontweight='bold', fontsize=12, bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

            # Downward Force (Weight)
            ax3.annotate('', xy=(5, 4), xytext=(5, 8.5), arrowprops=dict(arrowstyle='->', color='black', lw=3))
            ax3.text(5.2, 8, "Submerged Weight\n(γ' = γ_sat - γ_w)", ha='left', fontsize=10)

            # Upward Force (Seepage)
            ax3.annotate('', xy=(5, 6), xytext=(5, 1.5), arrowprops=dict(arrowstyle='->', color='red', lw=3))
            ax3.text(5.2, 2, "Seepage Force\n(j = i · γ_w)", ha='left', color='red', fontsize=10, fontweight='bold')

            # Equilibrium Text
            ax3.text(5, 0.5, "Critical Condition: Seepage Force = Weight", ha='center', fontweight='bold', fontsize=10, bbox=dict(facecolor='#ffeeba', edgecolor='orange'))

            st.pyplot(fig3)

if __name__ == "__main__":
    app()
