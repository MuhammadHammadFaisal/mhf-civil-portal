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

def solve_flow_net_at_point(h_upstream, h_downstream, total_Nd, drops_passed, z_point):
    """
    Calculates head and pressure using Flow Net Counting Method (Standard Textbook Approach).
    """
    # 1. Total Head Loss (H_diff)
    H_diff = h_upstream - h_downstream
    
    # 2. Head Loss per Drop (delta_h)
    if total_Nd > 0:
        delta_h = H_diff / total_Nd
    else:
        delta_h = 0
        
    # 3. Total Head at Point (H_point)
    # H_point = H_start - (drops_passed * loss_per_drop)
    # Note: H_start is usually equal to h_upstream (assuming datum is at 0 or consistent)
    h_point = h_upstream - (drops_passed * delta_h)
    
    # 4. Pressure Head (hp)
    # Bernoulli: Total Head = Elevation Head + Pressure Head
    # h = z + hp  ->  hp = h - z
    hp = h_point - z_point
    
    # 5. Pore Pressure (u)
    gamma_w = 9.81
    u = hp * gamma_w
    
    return {
        "H_diff": H_diff,
        "delta_h": delta_h,
        "h_point": h_point,
        "hp": hp,
        "u": u,
        "z": z_point,
        "nd_passed": drops_passed,
        "Nd_total": total_Nd
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
    # TAB 3: FLOW NETS & PIPING (TEXTBOOK SOLVER)
    # =================================================================
    with tab3:
        st.markdown("### Flow Net Analysis")
        st.caption("Solve Flow Net problems by counting Drops ($N_d$) and Channels ($N_f$).")
        
        col_input, col_plot = st.columns([1, 1])

        with col_input:
            st.markdown("#### 1. Hydraulic Conditions")
            c_h1, c_h2 = st.columns(2)
            h_up = c_h1.number_input("Upstream Head ($H_{up}$) [m]", value=4.5, step=0.1)
            h_down = c_h2.number_input("Downstream Head ($H_{down}$) [m]", value=0.5, step=0.1)
            
            st.markdown("---")
            st.markdown("#### 2. Flow Net Properties")
            c_net1, c_net2 = st.columns(2)
            Nd = c_net1.number_input("Total Potential Drops ($N_d$)", value=7, step=1, min_value=1)
            Nf = c_net2.number_input("Total Flow Channels ($N_f$)", value=3, step=1, min_value=1)
            
            st.markdown("---")
            st.markdown("#### 3. Point Calculator")
            st.caption("Look at your diagram. Where is the point located?")
            
            # Point Inputs
            z_point = st.number_input("Elevation of Point ($z$) [m]", value=-4.0, step=0.5, help="Vertical distance from datum")
            nd_point = st.number_input("Drops Passed to reach Point ($n_d$)", value=2.0, step=0.1, help="How many equipotential lines has the water crossed to get here?")
            
            # Calculate Logic
            results = solve_flow_net_at_point(h_up, h_down, Nd, nd_point, z_point)
            
            # --- RESULTS DISPLAY ---
            st.markdown(f"""
            <div style="background-color: #e3f2fd; color: #333333; border: 1px solid #90caf9; border-radius: 8px; padding: 15px; margin-top: 10px;">
                <h4 style="color: #1565c0; margin-top: 0;">Results at Point</h4>
                <table style="width: 100%; border-collapse: collapse; color: #333333;">
                    <tr>
                        <td style="padding: 5px;"><strong>Total Head ($h$)</strong></td>
                        <td style="text-align: right; font-family: monospace; font-size: 1.1em; color: #333333;">{results['h_point']:.2f} m</td>
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
            
            # --- SEEPAGE RATE CALCULATION (Part a of image) ---
            k_val = st.number_input("Permeability ($k$) [m/sec] (for q calc)", value=1e-6, format="%.1e")
            q = k_val * results['H_diff'] * (Nf / Nd)
            
            st.info(f"**Seepage Rate (q):** {format_scientific(q)} m³/sec/m")

            # --- DETAILED STEPS (Matches Handwritten Note) ---
            with st.expander("See Calculation Steps (Textbook Style)"):
                st.markdown("**Step 1: Calculate Head Loss per Drop**")
                st.latex(rf"\Delta H = H_{{up}} - H_{{down}} = {h_up} - {h_down} = {results['H_diff']:.2f} \text{{ m}}")
                st.latex(rf"\Delta h = \frac{{\Delta H}}{{N_d}} = \frac{{{results['H_diff']:.2f}}}{{{Nd}}} = {results['delta_h']:.3f} \text{{ m}}")
                
                st.markdown("**Step 2: Calculate Total Head at Point**")
                st.write("Using the formula: $H_{point} = H_{start} - (n \times \Delta h)$")
                st.latex(rf"H_{{point}} = {h_up} - ({nd_point} \times {results['delta_h']:.3f}) = \mathbf{{{results['h_point']:.2f} \text{{ m}}}}")
                
                st.markdown("**Step 3: Calculate Pore Pressure**")
                st.write("Using Bernoulli: $H = z + \frac{u}{\gamma_w}$")
                st.latex(rf"\frac{{u}}{{\gamma_w}} = H_{{point}} - z = {results['h_point']:.2f} - ({results['z']}) = {results['hp']:.2f} \text{{ m}}")
                st.latex(rf"u = {results['hp']:.2f} \times 9.81 = \mathbf{{{results['u']:.2f} \text{{ kPa}}}}")

        with col_plot:
            # Dynamic Plot Visualization
            fig, ax = plt.subplots(figsize=(6, 5))
            
            # Setup Limits
            ax.set_xlim(-10, 10)
            ax.set_ylim(-12, 6)
            ax.set_aspect('equal')
            ax.axis('off')
            
            # 1. Draw Structure (Generic Sheet Pile)
            pile_depth = 6.0
            ax.add_patch(patches.Rectangle((-0.2, -pile_depth), 0.4, pile_depth + h_up, facecolor='#444', edgecolor='black', zorder=5))
            
            # 2. Draw Water Levels
            ax.plot([-10, 0], [h_up, h_up], 'b-', lw=2)
            ax.add_patch(patches.Rectangle((-10, 0), 10, h_up, facecolor='#D6EAF8', alpha=0.5))
            ax.text(-8, h_up + 0.5, f"Upstream: {h_up}m", fontsize=8, color='blue')

            ax.plot([0, 10], [h_down, h_down], 'b-', lw=2)
            ax.add_patch(patches.Rectangle((0, 0), 10, h_down, facecolor='#D6EAF8', alpha=0.5))
            ax.text(2, h_down + 0.5, f"Downstream: {h_down}m", fontsize=8, color='blue')
            
            # 3. Draw Ground Line
            ax.plot([-10, 10], [0, 0], 'k-', lw=2)

            # 4. Generate Flow Net Lines (Approximation for visuals)
            # We use complex potentials for a theoretical sheet pile to draw curves
            # But we limit the number of lines to exactly what the user typed (Nf, Nd)
            
            gx = np.linspace(-10, 10, 100)
            gy = np.linspace(-12, 0, 100)
            X, Y = np.meshgrid(gx, gy)
            Z = X + 1j * Y
            Z_shift = Z + 1j*pile_depth
            
            with np.errstate(invalid='ignore'):
                W = -1j * np.sqrt(Z_shift)
            Phi = np.real(W) # Potentials
            Psi = np.imag(W) # Flow lines
            
            # Draw Equipotential Lines (Nd)
            # We want Nd drops, so we need Nd+1 lines roughly
            ax.contour(X, Y, Phi, levels=Nd+1, colors='red', linewidths=1, linestyles='dashed', alpha=0.6)
            
            # Draw Flow Lines (Nf)
            ax.contour(X, Y, Psi, levels=Nf+1, colors='blue', linewidths=1, linestyles='solid', alpha=0.6)

            # 5. Highlight the "Elevation" line
            ax.plot([-10, 10], [z_point, z_point], 'k:', lw=1, alpha=0.5)
            ax.text(-9, z_point + 0.2, f"Elevation z={z_point}", fontsize=8)

            # Legend
            ax.plot([], [], 'b-', label=f'{Nf} Flow Channels')
            ax.plot([], [], 'r--', label=f'{Nd} Potential Drops')
            ax.legend(loc='lower center', ncol=2, fontsize=8)
            
            st.pyplot(fig)
if __name__ == "__main__":
    app()
