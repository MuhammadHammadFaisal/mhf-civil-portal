import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- HELPER FUNCTIONS ---

def format_scientific(val):
    """
    Converts a number to a professional LaTeX scientific string.
    Example: 0.004 -> 4.00 \times 10^{-3}
    """
    if val == 0:
        return "0"
    
    exponent = int(np.floor(np.log10(abs(val))))
    mantissa = val / (10**exponent)
    
    # Check if we really need scientific notation (for very small/large numbers)
    if -3 < exponent < 4:
        return f"{val:.4f}"
    else:
        return f"{mantissa:.2f} \\times 10^{{{exponent}}}"

def solve_flow_net_at_point(px, py, has_dam, dam_width, has_pile, pile_depth, pile_x, h_upstream, h_downstream):
    """
    Calculates head and pressure using Bligh's Creep Theory (Linear Loss).
    Returns detailed steps for display.
    """
    # 1. Elevation Head (z)
    z = py 
    
    # 2. Total Head (h)
    delta_H = h_upstream - h_downstream
    
    # --- GEOMETRY SETUP ---
    # Define the "Creep Path" (The path water follows along the contact)
    
    L_horizontal = 0.0
    L_vertical = 0.0
    
    if has_dam:
        dam_left = -dam_width / 2.0
        dam_right = dam_width / 2.0
        L_horizontal = dam_width
    else:
        # Minimal width if no dam
        dam_left = -0.1
        dam_right = 0.1
        L_horizontal = 0.2

    if has_pile:
        # Pile adds 2 * Depth to the path (down and up)
        L_vertical = 2 * pile_depth
        
    total_creep_length = L_horizontal + L_vertical
    if total_creep_length <= 0: total_creep_length = 1.0 

    # --- CALCULATE LOSS RATIO AT POINT X ---
    current_creep = 0.0
    
    # 1. Before Structure
    if px <= dam_left:
        fraction_lost = 0.0
    # 2. After Structure
    elif px >= dam_right:
        fraction_lost = 1.0
    # 3. Under/Inside Structure Zone
    else:
        x_dist = px - dam_left
        current_creep += x_dist 
        
        if has_pile:
            if px > pile_x:
                current_creep += 2 * pile_depth 
            elif abs(px - pile_x) < 0.01: # On the pile line
                depth_ratio = abs(py) / pile_depth if pile_depth > 0 else 0
                if depth_ratio > 1: depth_ratio = 1
                current_creep += (abs(py)) # Just going down
        
        fraction_lost = current_creep / total_creep_length

    # Clamp fraction
    fraction_lost = max(0.0, min(1.0, fraction_lost))
    
    # Calculate Head
    head_loss = delta_H * fraction_lost
    h = h_upstream - head_loss

    # 3. Pressure Head (hp) = Total Head - Elevation Head
    hp = h - z

    # 4. Pore Pressure (u) = hp * gamma_w
    gamma_w = 9.81
    u = hp * gamma_w
    
    # Return everything needed for the "Show Calculation" step
    return {
        "h": h, "z": z, "hp": hp, "u": u,
        "L_total": total_creep_length,
        "L_current": current_creep if px > dam_left and px < dam_right else (0 if px <= dam_left else total_creep_length),
        "fraction": fraction_lost,
        "dH": delta_H,
        "head_loss": head_loss
    }

# --- MAIN APP ---

def app():
    st.markdown("---")
    st.subheader("Flow of Water & Seepage Analysis")

    # TABS FOR DIFFERENT PROBLEM TYPES
    tab1, tab2, tab3 = st.tabs(["1D Seepage (Effective Stress)", "Permeability Tests", "Flow Nets & Piping"])

    # =================================================================
    # TAB 1: 1D SEEPAGE (Effective Stress)
    # =================================================================
    with tab1:
        st.caption("Determine Effective Stress at Point A. (Datum is at the Bottom of Soil)")
        
        col_setup, col_plot = st.columns([1, 1.2])
        
        with col_setup:
            st.markdown("### 1. Problem Setup")
            val_z = st.number_input("Soil Specimen Height (z) [m]", 0.1, step=0.5, value=4.0)
            val_y = st.number_input("Water Height above Soil (y) [m]", 0.0, step=0.5, value=2.0)
            val_x = st.number_input("Piezometer Head at Bottom (x) [m]", 0.0, step=0.5, value=7.5)
            gamma_sat = st.number_input("Saturated Unit Weight (γ_sat) [kN/m³]", 18.0, step=0.1)
            gamma_w = 9.81
            val_A = st.slider("Height of Point 'A' from Datum [m]", 0.0, val_z, val_z/2)

            st.markdown("---")
            if st.button("Calculate Effective Stress", type="primary"):
                H_top = val_z + val_y
                H_bot = val_x
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

                i = abs(h_loss) / val_z
                sigma_total = (val_y * gamma_w) + ((val_z - val_A) * gamma_sat)
                H_A = H_bot + (val_A / val_z) * (H_top - H_bot)
                h_p_A = H_A - val_A
                u_val = h_p_A * gamma_w
                sigma_prime = sigma_total - u_val
                
                # Result Display
                st.success(f"**Flow Condition:** {flow_type}\n\n*{effect_msg}*")
                st.metric("Total Stress (σ)", f"{sigma_total:.2f} kPa")
                st.metric("Pore Pressure (u)", f"{u_val:.2f} kPa")
                st.metric("Effective Stress (σ')", f"{sigma_prime:.2f} kPa")
                    
                with st.expander("View Step-by-Step Derivation"):
                    st.latex(rf"H_{{top}} = {H_top:.2f} m, \quad H_{{bot}} = {H_bot:.2f} m")
                    st.latex(rf"\sigma = {sigma_total:.2f} kPa")
                    st.latex(rf"u = {u_val:.2f} kPa")

        with col_plot:
            fig, ax = plt.subplots(figsize=(7, 8))
            
            # COORDINATES
            datum_y = 0.0
            soil_w = 2.5
            soil_x = 3.5  
            wl_top = val_z + val_y  
            wl_bot = val_x          
            
            if wl_top > wl_bot: flow_arrow = "⬇️"
            elif wl_bot > wl_top: flow_arrow = "⬆️"
            else: flow_arrow = "No Flow"

            # 1. SOIL FILL
            ax.add_patch(patches.Rectangle((soil_x, datum_y), soil_w, val_z, 
                                            facecolor='#E3C195', hatch='...', edgecolor='none', zorder=1))
            ax.text(soil_x + soil_w/2, datum_y + val_z/2, "SOIL", ha='center', fontweight='bold', fontsize=12, zorder=3)
            
            # 2. WATER FILLS & TANKS
            tank_w = 2.0
            tank_x = soil_x + (soil_w - tank_w)/2
            neck_w = 0.8
            neck_x = soil_x + (soil_w - neck_w)/2
            tank_base_y = wl_top - 0.5
            if tank_base_y < datum_y + val_z: tank_base_y = datum_y + val_z 
            
            ax.add_patch(patches.Rectangle((tank_x, tank_base_y), tank_w, wl_top - tank_base_y, facecolor='#D6EAF8', edgecolor='none', zorder=1))
            ax.add_patch(patches.Rectangle((neck_x, datum_y + val_z), neck_w, tank_base_y - (datum_y + val_z) + 0.1, facecolor='#D6EAF8', edgecolor='none', zorder=1))
            
            tube_w = 0.6
            left_tank_x = 0.5
            l_tank_base_y = wl_bot - 0.5
            if l_tank_base_y < datum_y - 1.0: l_tank_base_y = datum_y - 1.0 
            
            tube_start_x = soil_x + (soil_w - tube_w)/2
            ax.add_patch(patches.Rectangle((tube_start_x, datum_y - 1.0), tube_w, 1.0, facecolor='#D6EAF8', edgecolor='none', zorder=1))
            tube_left_end = left_tank_x + (tank_w - tube_w)/2
            ax.add_patch(patches.Rectangle((tube_left_end, datum_y - 1.0), tube_start_x - tube_left_end + tube_w, tube_w, facecolor='#D6EAF8', edgecolor='none', zorder=1))
            ax.add_patch(patches.Rectangle((tube_left_end, datum_y - 1.0), tube_w, l_tank_base_y - (datum_y - 1.0) + 0.1, facecolor='#D6EAF8', edgecolor='none', zorder=1))
            ax.add_patch(patches.Rectangle((left_tank_x, l_tank_base_y), tank_w, wl_bot - l_tank_base_y, facecolor='#D6EAF8', edgecolor='none', zorder=1))

            # 3. WALLS
            wall_thick = 2.5
            wall_color = 'black'
            ax.plot([tank_x, tank_x, neck_x, neck_x], [wl_top + 0.5, tank_base_y, tank_base_y, datum_y + val_z], color=wall_color, lw=wall_thick, zorder=2)
            ax.plot([tank_x + tank_w, tank_x + tank_w, neck_x + neck_w, neck_x + neck_w], [wl_top + 0.5, tank_base_y, tank_base_y, datum_y + val_z], color=wall_color, lw=wall_thick, zorder=2)
            ax.plot([soil_x, soil_x], [datum_y + val_z, datum_y], color=wall_color, lw=wall_thick, zorder=2) 
            ax.plot([soil_x + soil_w, soil_x + soil_w], [datum_y + val_z, datum_y], color=wall_color, lw=wall_thick, zorder=2) 
            ax.plot([soil_x, tube_start_x], [datum_y, datum_y], color=wall_color, lw=wall_thick, zorder=2)
            ax.plot([tube_start_x + tube_w, soil_x + soil_w], [datum_y, datum_y], color=wall_color, lw=wall_thick, zorder=2)
            ax.plot([soil_x, neck_x], [datum_y + val_z , datum_y + val_z], color=wall_color, lw=wall_thick, zorder=2)
            ax.plot([neck_x + neck_w, soil_x + soil_w], [datum_y + val_z , datum_y + val_z], color=wall_color, lw=wall_thick, zorder=2) 
            path_outer_x = [tube_start_x , tube_start_x , tube_left_end + tube_w, tube_left_end + tube_w, left_tank_x + tank_w, left_tank_x + tank_w]
            path_outer_y = [datum_y, datum_y - 1.0 + tube_w, datum_y - 1.0 + tube_w, l_tank_base_y, l_tank_base_y, wl_bot + 0.5]
            ax.plot(path_outer_x, path_outer_y, color=wall_color, lw=wall_thick, zorder=2)
            path_inner_x = [tube_start_x + tube_w, tube_start_x + tube_w, tube_left_end, tube_left_end, left_tank_x, left_tank_x]
            path_inner_y = [datum_y, datum_y - 1.0, datum_y - 1.0, l_tank_base_y, l_tank_base_y, wl_bot + 0.5]
            ax.plot(path_inner_x, path_inner_y, color=wall_color, lw=wall_thick, zorder=2)

            # Water & Details
            ax.plot([tank_x, tank_x + tank_w], [wl_top, wl_top], color='blue', lw=2, zorder=2)
            ax.plot([left_tank_x, left_tank_x + tank_w], [wl_bot, wl_bot], color='blue', lw=2, zorder=2)
            ax.plot(tank_x + tank_w/2, wl_top, marker='v', color='blue', markersize=8, zorder=2)
            ax.plot(left_tank_x + tank_w/2, wl_bot, marker='v', color='blue', markersize=8, zorder=2)

            # Dimensions
            ax.plot([-0.5, 8], [datum_y, datum_y], 'k-.', lw=1)
            ax.text(soil_x + 0.5 + soil_w, datum_y - 0.25, "Datum (z=0)", va='center', fontsize=10, style='italic')
            
            dim_z_x = soil_x - 0.4
            ax.annotate('', xy=(dim_z_x, datum_y), xytext=(dim_z_x, datum_y + val_z), arrowprops=dict(arrowstyle='<->', color='black'))
            ax.text(dim_z_x - 0.1, val_z/2, f"z = {val_z:.2f}m", fontsize=10, ha='right')
            
            dim_y_x = soil_x + soil_w + 0.8
            ax.annotate('', xy=(dim_y_x, val_z), xytext=(dim_y_x, wl_top), arrowprops=dict(arrowstyle='<->', color='black'))
            ax.text(dim_y_x + 0.1, (val_z + wl_top)/2, f"y = {val_y:.2f}m", fontsize=11, fontweight='bold', color='black', ha='left')
            ax.plot([soil_x + soil_w, dim_y_x + 0.2], [val_z, val_z], 'k--', lw=0.5)
            ax.plot([tank_x + tank_w, dim_y_x + 0.2], [wl_top, wl_top], 'k--', lw=0.5)

            dim_x_loc = left_tank_x - 0.4
            ax.annotate('', xy=(dim_x_loc, datum_y), xytext=(dim_x_loc, wl_bot), arrowprops=dict(arrowstyle='<->'))
            ax.text(dim_x_loc - 0.1, wl_bot/2, f"x = {val_x:.2f}m", fontsize=11, fontweight='bold', ha='right')

            dim_A_x = soil_x + soil_w/2 + 2.0
            ax.annotate('', xy=(dim_A_x, datum_y), xytext=(dim_A_x, datum_y + val_A), arrowprops=dict(arrowstyle='<->', color='black'))
            ax.text(dim_A_x + 0.1, val_A/2, f"A = {val_A:.2f}m", color='black', fontweight='bold', zorder=5)
            ax.plot([soil_x + soil_w/2, dim_A_x], [datum_y + val_A, datum_y + val_A], 'k:', lw=1)
            ax.scatter(soil_x + soil_w/2 + 2.0, datum_y + val_A, color='Black', zorder=5, s=80, edgecolor='black')
            ax.text(soil_x + soil_w/2 + 2.2, datum_y + val_A + 0.1, f"Point A", color='Black', fontweight='bold', zorder=5)

            ax.text(soil_x + soil_w/2, wl_top + 0.5, f"FLOW {flow_arrow}", ha='center', fontsize=12, fontweight='bold')
            ax.set_xlim(-1.5, 9)
            ax.set_ylim(datum_y - 1.5, max(wl_bot, wl_top) + 1)
            ax.axis('off')
            st.pyplot(fig)


    # =================================================================
    # TAB 2: PERMEABILITY (Lab Tests)
    # =================================================================
    with tab2:
        st.caption("Calculate Coefficient of Permeability (k). Input variables are marked on the diagram.")
        col_input_2, col_plot_2 = st.columns([1, 1.2])

        with col_input_2:
            st.markdown("### 1. Test Configuration")
            test_type = st.radio("Select Method", ["Constant Head", "Falling Head"], horizontal=True)
            st.markdown("---")

            if "Constant" in test_type:
                st.latex(r"k = \frac{Q \cdot L}{A \cdot h \cdot t}")
                Q = st.number_input("Collected Volume (Q) [cm³]", value=500.0)
                L = st.number_input("Specimen Length (L) [cm]", value=15.0)
                h = st.number_input("Head Difference (h) [cm]", value=40.0, help="Vertical distance from top water level to bottom outlet level")
                A = st.number_input("Specimen Area (A) [cm²]", value=40.0)
                t = st.number_input("Time Interval (t) [sec]", value=60.0)
                
                st.markdown("---")
                if st.button("Calculate Permeability (k)", type="primary"):
                    if A*h*t > 0: 
                        k_val = (Q*L)/(A*h*t)
                        
                        # --- PROFESSIONAL FORMATTING (LaTeX Scientific) ---
                        k_formatted = format_scientific(k_val)
                        st.success(f"""
                        **Permeability Coefficient (k)**
                        
                        $$
                        {k_formatted} \\text{{ cm/sec}}
                        $$
                        """)
                        st.markdown(f"""
                        <div style="background-color: #d1e7dd; padding: 20px; border-radius: 10px; border: 1px solid #0f5132; text-align: center; margin-top: 20px;">
                            <p style="color: #0f5132; margin-bottom: 8px; font-size: 16px; font-weight: 600;">Permeability Coefficient (k)</p>
                            <h2 style="color: #0f5132; margin: 0; font-size: 28px; font-weight: 800;">
                                $${k_formatted} \\text{{ cm/sec}}$$
                            </h2>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Inputs must be positive.")

            else:
                st.latex(r"k = 2.303 \frac{a \cdot L}{A \cdot t} \log_{10}\left(\frac{h_1}{h_2}\right)")
                a = st.number_input("Standpipe Area (a) [cm²]", format="%.4f", value=0.5)
                A_soil = st.number_input("Soil Specimen Area (A) [cm²]", value=40.0)
                L_fall = st.number_input("Specimen Length (L) [cm]", value=15.0)
                h1 = st.number_input("Initial Head (h1) [cm]", value=50.0, help="Height from bottom water level to Start level")
                h2 = st.number_input("Final Head (h2) [cm]", value=30.0, help="Height from bottom water level to End level")
                t_fall = st.number_input("Time Interval (t) [sec]", value=300.0)

                st.markdown("---")
                if st.button("Calculate Permeability (k)", type="primary"):
                    if A_soil*t_fall > 0 and h2 > 0: 
                        k_val = (2.303*a*L_fall/(A_soil*t_fall))*np.log10(h1/h2)
                        
                        # --- PROFESSIONAL FORMATTING (LaTeX Scientific) ---
                        k_formatted = format_scientific(k_val)
                        st.success(f"""
                        **Permeability Coefficient (k)**
                        
                        $$
                        {k_formatted} \\text{{ cm/sec}}
                        $$
                        """)
                    else:
                        st.error("Inputs invalid. h2 must be > 0.")

        with col_plot_2:
            fig2, ax2 = plt.subplots(figsize=(6, 8))
            ax2.set_xlim(0, 10); ax2.set_ylim(0, 10); ax2.axis('off')
            soil_color, water_color, wall_color = '#E3C195', '#D6EAF8', 'black'

            if "Constant" in test_type:
                ax2.add_patch(patches.Rectangle((2, 8), 4, 1.5, facecolor=water_color, edgecolor=wall_color))
                ax2.text(2.2, 8.2, "Supply\nTank", fontsize=8)
                ax2.plot([2, 6], [9, 9], 'b-', lw=2); ax2.plot(4, 9, marker='v', color='blue')
                
                ax2.add_patch(patches.Rectangle((3.8, 6), 0.4, 2, facecolor=water_color, edgecolor='none'))
                ax2.plot([3.8, 3.8], [6, 8], 'k-'); ax2.plot([4.2, 4.2], [6, 8], 'k-')

                ax2.add_patch(patches.Rectangle((3, 4), 2, 2, facecolor=soil_color, hatch='X', edgecolor=wall_color, lw=2))
                ax2.text(4, 5, "SOIL\nArea A", ha='center', va='center', fontweight='bold')
                
                ax2.add_patch(patches.Rectangle((3.8, 2.5), 0.4, 1.5, facecolor=water_color, edgecolor='none'))
                ax2.plot([3.8, 3.8], [2.5, 4], 'k-'); ax2.plot([4.2, 4.2], [2.5, 4], 'k-')
                ax2.add_patch(patches.Rectangle((3.5, 1), 3, 1.5, facecolor=water_color, edgecolor=wall_color))
                ax2.text(6, 0.5, "Collection\nTank", ha='center')
                ax2.plot([3.5, 6.5], [2.2, 2.2], 'b-', lw=2); ax2.plot(6, 2.2, marker='v', color='blue')

                ax2.annotate('', xy=(8, 2.2), xytext=(8, 9), arrowprops=dict(arrowstyle='<->', lw=1.5))
                ax2.text(8.2, 5.5, "h (Head Diff)", ha='left', fontweight='bold', fontsize=12, color='blue')
                ax2.plot([6, 8.2], [9, 9], 'k--', lw=0.5); ax2.plot([6.5, 8.2], [2.2, 2.2], 'k--', lw=0.5)

                ax2.annotate('', xy=(1.5, 4), xytext=(1.5, 6), arrowprops=dict(arrowstyle='<->', lw=1.5))
                ax2.text(1.2, 5, "L", ha='right', fontweight='bold', fontsize=12)
                ax2.plot([1.5, 3], [4, 4], 'k--', lw=0.5); ax2.plot([1.5, 3], [6, 6], 'k--', lw=0.5)
                ax2.text(6.8, 1.5, "-> Q (Vol)", ha='left', fontstyle='italic')

            else:
                ax2.add_patch(patches.Rectangle((3.8, 6), 0.4, 3.5, facecolor=water_color, edgecolor=wall_color))
                ax2.text(3.5, 8, "Standpipe\n(Area a)", ha='right', fontsize=9)
                ax2.add_patch(patches.Rectangle((3, 4), 2, 2, facecolor=soil_color, hatch='X', edgecolor=wall_color, lw=2))
                ax2.text(4, 5, "SOIL\nArea A", ha='center', va='center', fontweight='bold')
                ax2.add_patch(patches.Rectangle((3.8, 2), 0.4, 2, facecolor=water_color, edgecolor='none'))
                ax2.plot([3.8, 3.8], [2, 4], 'k-'); ax2.plot([4.2, 4.2], [2, 4], 'k-')
                ax2.add_patch(patches.Rectangle((3.5, 1), 3, 1.5, facecolor=water_color, edgecolor=wall_color))
                ax2.plot([3.5, 6.5], [2, 2], 'b-', lw=2); ax2.plot(6, 2, marker='v', color='blue')

                ax2.plot([3.8, 4.2], [9, 9], 'r-', lw=2); ax2.text(4.4, 9, "Start", fontsize=8, color='red')
                ax2.plot([3.8, 4.2], [7, 7], 'r-', lw=2); ax2.text(4.4, 7, "End", fontsize=8, color='red')

                ax2.annotate('', xy=(8, 2), xytext=(8, 9), arrowprops=dict(arrowstyle='<->', color='red'))
                ax2.text(8.2, 9, "h1", ha='left', fontweight='bold', color='red')
                ax2.plot([4.2, 8.2], [9, 9], 'r--', lw=0.5)
                ax2.annotate('', xy=(7, 2), xytext=(7, 7), arrowprops=dict(arrowstyle='<->', color='red'))
                ax2.text(7.2, 7, "h2", ha='left', fontweight='bold', color='red')
                ax2.plot([4.2, 7.2], [7, 7], 'r--', lw=0.5)
                ax2.plot([6.5, 8.2], [2, 2], 'b--', lw=0.5)

                ax2.annotate('', xy=(1.5, 4), xytext=(1.5, 6), arrowprops=dict(arrowstyle='<->', lw=1.5))
                ax2.text(1.2, 5, "L", ha='right', fontweight='bold', fontsize=12)
                ax2.plot([1.5, 3], [4, 4], 'k--', lw=0.5); ax2.plot([1.5, 3], [6, 6], 'k--', lw=0.5)

            st.pyplot(fig2)

    # =================================================================
    # TAB 3: 2D FLOW NET (DAM + PILE COMBINATION)
    # =================================================================
    with tab3:
        st.markdown("### Combined Flow Net Analysis")
        st.caption("Design a hydraulic structure using a Concrete Dam, a Sheet Pile, or both.")
        
        # CHANGED: Adjusted column ratio to make the plot smaller/more balanced
        col_input, col_plot = st.columns([1, 1])

        with col_input:
            st.markdown("#### 1. Structure Configuration")
            
            has_dam = st.checkbox("Include Concrete Dam", value=True)
            has_pile = st.checkbox("Include Sheet Pile (Cutoff)", value=False)
            
            dam_width = 0.0
            pile_depth = 0.0
            pile_x = 0.0

            if has_dam:
                dam_width = st.number_input("Dam Base Width (B) [m]", value=10.0, step=1.0)
            
            if has_pile:
                c_p1, c_p2 = st.columns(2)
                pile_depth = c_p1.number_input("Pile Depth (D) [m]", value=5.0, step=0.5)
                
                min_x = -dam_width/2.0 if has_dam else -10.0
                max_x = dam_width/2.0 if has_dam else 10.0
                pile_x = c_p2.number_input("Pile Location (X) [m]", value=min_x, step=0.5, min_value=min_x, max_value=max_x)

            st.markdown("---")
            st.markdown("#### 2. Hydraulic Conditions")
            c_h1, c_h2 = st.columns(2)
            h_up = c_h1.number_input("Upstream Level [m]", value=10.0)
            h_down = c_h2.number_input("Downstream Level [m]", value=2.0)
            
            st.markdown("---")
            st.markdown("#### 3. Point Pressure Calculator")
            
            cp1, cp2 = st.columns(2)
            p_x = cp1.number_input("Point X [m]", value=0.0, step=0.5)
            p_y = cp2.number_input("Point Y [m]", value=-4.0, step=0.5, max_value=0.0)
            
            results = None
            if p_y > 0:
                st.error("Point Y must be negative (in the soil).")
            else:
                conflict = False
                if has_pile:
                    if abs(p_x - pile_x) < 0.1 and abs(p_y) < pile_depth:
                        conflict = True
                
                if conflict:
                    st.warning("Point is inside the structure material.")
                else:
                    results = solve_flow_net_at_point(
                        p_x, p_y, has_dam, dam_width, has_pile, pile_depth, pile_x, h_up, h_down
                    )

            if results:
                # --- PROFESSIONAL RESULT CARD (FIXED COLORS) ---
                st.markdown(f"""
                <div style="background-color: #e3f2fd; color: #333333; border: 1px solid #90caf9; border-radius: 8px; padding: 15px; margin-top: 10px;">
                    <h4 style="color: #1565c0; margin-top: 0;">Results at Point ({p_x}, {p_y})</h4>
                    <table style="width: 100%; border-collapse: collapse; color: #333333;">
                        <tr>
                            <td style="padding: 5px;"><strong>Total Head ($h$)</strong></td>
                            <td style="text-align: right; font-family: monospace; font-size: 1.1em; color: #333333;">{results['h']:.2f} m</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px;"><strong>Elevation Head ($z$)</strong></td>
                            <td style="text-align: right; font-family: monospace; font-size: 1.1em; color: #333333;">{results['z']:.2f} m</td>
                        </tr>
                        <tr>
                            <td style="padding: 5px; border-top: 1px solid #bdc3c7;"><strong>Pore Pressure ($u$)</strong></td>
                            <td style="text-align: right; font-family: monospace; font-size: 1.2em; color: #d63384; font-weight: bold; border-top: 1px solid #bdc3c7;">{results['u']:.2f} kPa</td>
                        </tr>
                    </table>
                </div>
                """, unsafe_allow_html=True)
                
                # --- DETAILED CALCULATION EXPANDER ---
                with st.expander("See Detailed Calculation Steps"):
                    st.markdown("**Step 1: Geometry & Creep Length**")
                    st.latex(rf"L_{{total}} = \text{{Horizontal}} + \text{{Vertical}} = {results['L_total']:.2f} \text{{ m}}")
                    st.latex(rf"L_{{point}} = \text{{Creep path to Point A}} = {results['L_current']:.2f} \text{{ m}}")
                    
                    st.markdown("**Step 2: Head Loss Calculation**")
                    st.latex(rf"\Delta H = H_{{up}} - H_{{down}} = {h_up} - {h_down} = {results['dH']:.2f} \text{{ m}}")
                    st.latex(rf"\text{{Loss Ratio}} = \frac{{L_{{point}}}}{{L_{{total}}}} = \frac{{{results['L_current']:.2f}}}{{{results['L_total']:.2f}}} = {results['fraction']:.3f}")
                    st.latex(rf"h_{{loss}} = \Delta H \times \text{{Ratio}} = {results['head_loss']:.2f} \text{{ m}}")
                    
                    st.markdown("**Step 3: Total Head ($h$)**")
                    st.latex(rf"h = H_{{up}} - h_{{loss}} = {h_up} - {results['head_loss']:.2f} = \mathbf{{{results['h']:.2f} \text{{ m}}}}")
                    
                    st.markdown("**Step 4: Pore Pressure ($u$)**")
                    st.write("Bernoulli Equation: $h = z + h_p$")
                    st.latex(rf"h_p = h - z = {results['h']:.2f} - ({results['z']}) = {results['hp']:.2f} \text{{ m}}")
                    st.latex(rf"u = h_p \times \gamma_w = {results['hp']:.2f} \times 9.81 = \mathbf{{{results['u']:.2f} \text{{ kPa}}}}")

        with col_plot:
            # CHANGED: Reduced figure size from (8,6) to (6, 5) for a compact look
            fig, ax = plt.subplots(figsize=(6, 5))
            
            gx = np.linspace(-15, 15, 200)
            gy = np.linspace(-15, 0, 150)
            X, Y = np.meshgrid(gx, gy)
            Z = X + 1j * Y
            
            if has_dam:
                C = dam_width / 2.0
                ax.add_patch(patches.Rectangle((-C, 0), 2*C, h_up+1, facecolor='gray', edgecolor='black', zorder=5))
                ax.text(0, 1, "DAM", ha='center', color='white', fontweight='bold', zorder=6)
                with np.errstate(invalid='ignore', divide='ignore'):
                    W = np.arccosh(Z / C)
                Phi, Psi = np.real(W), np.imag(W)
            elif has_pile:
                D = pile_depth
                Z_shift = Z + 1j*D 
                with np.errstate(invalid='ignore'):
                    W = -1j * np.sqrt(Z_shift)
                Phi, Psi = np.real(W), np.imag(W)
            else:
                Phi, Psi = np.zeros_like(X), np.zeros_like(Y)

            if has_pile:
                ax.add_patch(patches.Rectangle((pile_x - 0.15, -pile_depth), 0.3, pile_depth + h_up, facecolor='#444', edgecolor='black', zorder=6))
                ax.text(pile_x, -pile_depth/2, "PILE", rotation=90, color='white', ha='center', va='center', fontsize=8, zorder=7)

            if has_dam or has_pile:
                ax.contour(X, Y, Psi, levels=12, colors='blue', linewidths=1, linestyles='solid', alpha=0.4)
                ax.contour(X, Y, Phi, levels=18, colors='red', linewidths=1, linestyles='dashed', alpha=0.4)

            ax.add_patch(patches.Rectangle((-15, 0), 15, h_up, facecolor='#D6EAF8', alpha=0.5))
            ax.plot([-15, 0], [h_up, h_up], 'b-', lw=2)
            ax.add_patch(patches.Rectangle((0, 0), 15, h_down, facecolor='#D6EAF8', alpha=0.5))
            ax.plot([0, 15], [h_down, h_down], 'b-', lw=2)
            ax.plot([-15, 15], [0, 0], 'k-', lw=2) 

            if results:
                ax.scatter(p_x, p_y, c='red', s=80, marker='x', zorder=10, linewidths=2)
                # Shorter label on plot to reduce clutter
                ax.text(p_x + 0.5, p_y, f"u={results['u']:.1f}", color='red', fontweight='bold', fontsize=9, zorder=10)

            ax.set_ylim(-12, max(h_up, h_down)+2)
            ax.set_xlim(-12, 12)
            ax.set_aspect('equal'); ax.axis('off')
            
            # Simplified Legend
            ax.plot([], [], 'b-', label='Flow', alpha=0.5)
            ax.plot([], [], 'r--', label='Equipotential', alpha=0.5)
            ax.legend(loc='lower center', ncol=2, fontsize=8, frameon=True)

            st.pyplot(fig)

if __name__ == "__main__":
    app()
