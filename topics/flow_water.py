import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ============================================================
# MAINTENANCE BANNER
# ============================================================
def show_maintenance_banner():
    st.markdown("""
    <div style="background: linear-gradient(90deg, #ff6b6b 0%, #ffa500 100%); 
                padding: 15px; 
                border-radius: 10px; 
                border: 3px solid #cc0000;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h2 style="color: white; margin: 0; text-align: center;">
             UNDER MAINTENANCE 
        </h2>
        <p style="color: white; margin: 10px 0 0 0; text-align: center; font-size: 16px;">
            Flow net calculations are currently being calibrated and improved.<br>
            Results may not be accurate. Please use with caution.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_scientific(val):
    if val == 0:
        return "0"
    exponent = int(np.floor(np.log10(abs(val))))
    mantissa = val / (10**exponent)
    if -3 < exponent < 4:
        return f"{val:.4f}"
    return f"{mantissa:.2f} \\times 10^{{{exponent}}}"

# ============================================================
# FLOW NET CALCULATION LOGIC
# ============================================================

def get_complex_potential_sheet_pile(x, y, pile_depth, pile_x, h_up, h_down, soil_depth):
    """
    CORRECTED: Uses Conformal Mapping (Inverse Sine) for flow around a vertical barrier.
    """
    # Safety check
    d = max(pile_depth, 0.1)

    # 1. Center coordinates on the pile
    z = (x - pile_x) + 1j * y
    
    # 2. Conformal Map: w = i * arcsin(z/d)
    # This maps the sheet pile geometry to a semi-infinite strip.
    z_norm = z / d
    
    with np.errstate(all='ignore'):
        # The '1j' rotation aligns the potential so the surface is an equipotential
        # and the pile is a streamline.
        w_raw = 1j * np.arcsin(z_norm)
    
    # 3. Scale to match Head Boundary Conditions
    amplitude = (h_up - h_down) / np.pi
    average_head = (h_up + h_down) / 2.0
    
    # Refined Potential Function
    W = -amplitude * w_raw + average_head
    
    return W

def get_complex_potential_dam(x, y, dam_width, h_up, h_down):
    """
    CORRECTED: Uses Conformal Mapping (Inverse Sine) for flow under a flat plate.
    """
    z = x + 1j * y
    b = max(dam_width / 2.0, 0.1)
        
    # Conformal Map: w = arcsin(z/b)
    # For a flat dam, the base (-b to b) is a streamline.
    with np.errstate(all='ignore'):
        w_raw = np.arcsin(z / b)
    
    # Scale to match heads
    amplitude = (h_up - h_down) / np.pi
    average_head = (h_up + h_down) / 2.0
    
    # Note the sign change to ensure flow goes High -> Low
    W = -amplitude * w_raw + average_head
    
    return W

def get_complex_potential(x, y, mode, pile_depth, pile_x, dam_width, h_up, h_down, soil_depth):
    """
    Main router function to get complex potential.
    """
    # Adjust for very shallow depth or numerical stability
    y = np.minimum(y, -0.01) 
    
    if mode == "Sheet Pile Only":
        return get_complex_potential_sheet_pile(x, y, pile_depth, pile_x, h_up, h_down, soil_depth)
    
    elif mode == "Concrete Dam Only":
        return get_complex_potential_dam(x, y, dam_width, h_up, h_down)
    
    elif mode == "Combined (Dam + Pile)":
        # Approximate combined effect by increasing effective pile depth
        effective_depth = pile_depth + (dam_width * 0.25)
        return get_complex_potential_sheet_pile(x, y, effective_depth, pile_x, h_up, h_down, soil_depth)
    
    return 0 + 0j

def calculate_pore_pressure(px, py, mode, pile_d, pile_x, dam_w, h_up, h_down, soil_d):
    """
    Calculates pore pressure (u) at a specific point (px, py).
    """
    if py > 0:
        return None  # Above ground surface

    gamma_w = 9.81  # kN/m³

    # 1. Get complex potential at the specific point
    w_pt = get_complex_potential(px, py, mode, pile_d, pile_x, dam_w, h_up, h_down, soil_d)
    
    # 2. Extract the Total Head (Phi)
    # In our conformal map, the Real part (Phi) is directly the Total Head (h)
    h_total = np.real(w_pt)

    # Handle numerical edges (NaN or Inf)
    if not np.isfinite(h_total):
        return None

    # 3. Calculate Pore Pressure
    # Bernoulli/Terzaghi principle: Total Head = Elevation Head + Pressure Head
    # h_total = y + (u / gamma_w)
    # Therefore: u = (h_total - y) * gamma_w
    
    pressure_head = h_total - py
    u = pressure_head * gamma_w

    return {"u": u, "h_total": h_total, "pressure_head": pressure_head}

# ============================================================
# MAIN APP
# ============================================================

def app():

    try:
        st.set_page_config(page_title="Soil Mechanics Analysis", layout="wide")
    except:
        pass

    st.subheader("Flow of Water & Seepage Analysis")
    
    tab1, tab2, tab3 = st.tabs(["1D Seepage", "Permeability", "Flow Nets"])
    
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
            
            datum_y = 0.0
            soil_w = 2.5
            soil_x = 3.5  
            wl_top = val_z + val_y  
            wl_bot = val_x          
            
            if wl_top > wl_bot: flow_arrow = "⬇️"
            elif wl_bot > wl_top: flow_arrow = "⬆️"
            else: flow_arrow = "No Flow"

            ax.add_patch(patches.Rectangle((soil_x, datum_y), soil_w, val_z, 
                                          facecolor='#E3C195', hatch='...', edgecolor='none', zorder=1))
            ax.text(soil_x + soil_w/2, datum_y + val_z/2, "SOIL", ha='center', fontweight='bold', fontsize=12, zorder=3)
            
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

            ax.plot([tank_x, tank_x + tank_w], [wl_top, wl_top], color='blue', lw=2, zorder=2)
            ax.plot([left_tank_x, left_tank_x + tank_w], [wl_bot, wl_bot], color='blue', lw=2, zorder=2)
            ax.plot(tank_x + tank_w/2, wl_top, marker='v', color='blue', markersize=8, zorder=2)
            ax.plot(left_tank_x + tank_w/2, wl_bot, marker='v', color='blue', markersize=8, zorder=2)

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
    # TAB 2: PERMEABILITY
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
                h = st.number_input("Head Difference (h) [cm]", value=40.0)
                A = st.number_input("Specimen Area (A) [cm²]", value=40.0)
                t = st.number_input("Time Interval (t) [sec]", value=60.0)
                
                st.markdown("---")
                if st.button("Calculate Permeability (k)", type="primary"):
                    if A*h*t > 0: 
                        k_val = (Q*L)/(A*h*t)
                        k_formatted = format_scientific(k_val)
                        st.success(f"**Permeability Coefficient (k)**\n\n$${k_formatted} \\text{{ cm/sec}}$$")
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
                h1 = st.number_input("Initial Head (h1) [cm]", value=50.0)
                h2 = st.number_input("Final Head (h2) [cm]", value=30.0)
                t_fall = st.number_input("Time Interval (t) [sec]", value=300.0)

                st.markdown("---")
                if st.button("Calculate Permeability (k)", type="primary"):
                    if A_soil*t_fall > 0 and h2 > 0: 
                        k_val = (2.303*a*L_fall/(A_soil*t_fall))*np.log10(h1/h2)
                        k_formatted = format_scientific(k_val)
                        st.success(f"**Permeability Coefficient (k)**\n\n$${k_formatted} \\text{{ cm/sec}}$$")
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

    # ============================================================
    # TAB 3 — FLOW NETS (FINAL CORRECTED VERSION)
    # ============================================================
    with tab3:
        st.markdown("### 2D Flow Net Analysis")
        st.caption("**Flow Net Principles:** Blue lines = flow paths (streamlines). "
                  "Red dashed = head drops (equipotentials). Must intersect at 90°.")
            # SHOW MAINTENANCE BANNER
        show_maintenance_banner()
        col_in, col_gr = st.columns([1, 1.4])

        with col_in:
            mode = st.radio(
                "Structure Type",
                ["Sheet Pile Only", "Concrete Dam Only", "Combined (Dam + Pile)"],
                help="Select the seepage barrier configuration"
            )

            st.markdown("---")
            st.markdown("#### Boundary Conditions")
            h_up = st.number_input("Upstream Head (h₁) [m]", value=10.0, min_value=0.1)
            h_down = st.number_input("Downstream Head (h₂) [m]", value=2.0, min_value=0.0)
            soil_d = st.number_input("Impervious Layer Depth [m]", value=12.0, min_value=1.0)

            st.markdown("---")
            st.markdown("#### Structure Parameters")
            
            dam_w = 0.0
            pile_d = 0.0
            pile_x = 0.0

            if "Dam" in mode:
                dam_w = st.number_input("Dam Base Width (B) [m]", value=6.0, min_value=0.1)

            if "Pile" in mode:
                pile_d = st.number_input("Sheet Pile Depth (D) [m]", value=5.0, min_value=0.1)
                
                limit = dam_w / 2 if "Dam" in mode else 10.0
                pile_x = st.number_input(
                    "Pile X Location [m]",
                    value=0.0,
                    min_value=-limit,
                    max_value=limit,
                    help="Position along dam base (0 = center)"
                )

            st.markdown("---")
            st.markdown("#### Flow Net Density")
            Nd = max(2, int(st.number_input("Equipotential Drops (Nd)", value=10, min_value=2, max_value=20)))
            Nf = max(1, int(st.number_input("Flow Channels (Nf)", value=5, min_value=1, max_value=10)))

            st.markdown("---")
            st.markdown("#### Pore Pressure Calculation")
            px = st.number_input("Point X Coordinate [m]", value=2.0)
            py = st.number_input("Point Y Coordinate [m]", value=-4.0, max_value=0.0)

            res = calculate_pore_pressure(px, py, mode, pile_d, pile_x, dam_w, h_up, h_down, soil_d)
            
            if res:
                st.success(f"**Pore Pressure (u):** {res['u']:.2f} kPa")
                st.info(f"**Total Head (H):** {res['h_total']:.2f} m\n\n"
                       f"**Pressure Head (h_p):** {res['pressure_head']:.2f} m")
            else:
                st.warning("Point must be below ground surface (y ≤ 0)")

        with col_gr:
            fig, ax = plt.subplots(figsize=(8, 7))
            ax.set_xlim(-12, 12)
            ax.set_ylim(-soil_d - 1, h_up + 2)
            ax.set_aspect("equal")
            ax.set_facecolor('#f5f5dc')

            # Create high-resolution mesh
            gx = np.linspace(-12, 12, 400)
            gy = np.linspace(-soil_d, 0, 300)
            X, Y = np.meshgrid(gx, gy)

            # Calculate complex potential
            W = get_complex_potential(X, Y, mode, pile_d, pile_x, dam_w, h_up, h_down, soil_d)
            
            # Extract Phi and Psi
            Phi = np.real(W)  # Equipotentials
            Psi = np.imag(W)  # Streamlines

            # Clean data
            Phi = np.where(np.isfinite(Phi), Phi, np.nan)
            Psi = np.where(np.isfinite(Psi), Psi, np.nan)

            # Determine contour levels
            phi_vals = Phi[np.isfinite(Phi)]
            psi_vals = Psi[np.isfinite(Psi)]
            
            if len(phi_vals) > 100:
                phi_min, phi_max = np.percentile(phi_vals, [15, 85])
                equi_levels = np.linspace(phi_min, phi_max, Nd + 1)
            else:
                equi_levels = Nd + 1

            if len(psi_vals) > 100:
                psi_min, psi_max = np.percentile(psi_vals, [15, 85])
                stream_levels = np.linspace(psi_min, psi_max, Nf + 1)
            else:
                stream_levels = Nf + 1

            # Plot STREAMLINES (Blue solid - flow paths)
            try:
                cs1 = ax.contour(X, Y, Psi,
                               levels=stream_levels,
                               colors="blue", linewidths=2.5, alpha=0.8)
            except:
                pass

            # Plot EQUIPOTENTIALS (Red dashed - head drops)
            try:
                cs2 = ax.contour(X, Y, Phi,
                               levels=equi_levels,
                               colors="red", linestyles="--", linewidths=2.0, alpha=0.75)
            except:
                pass

            # Draw boundaries
            ax.axhline(0, color="saddlebrown", lw=3.5, label="Ground Surface", zorder=5)
            ax.axhline(-soil_d, color="black", lw=4.5, label="Impervious Layer", zorder=5)

            # Water levels
            ax.fill_between([-12, -dam_w/2 if "Dam" in mode else 0], 
                          [0, 0], [h_up, h_up], 
                          color='lightblue', alpha=0.4, label='Upstream Water', zorder=1)
            ax.fill_between([dam_w/2 if "Dam" in mode else 0, 12], 
                          [0, 0], [h_down, h_down], 
                          color='lightcyan', alpha=0.4, label='Downstream Water', zorder=1)

            # Draw structures
            if "Dam" in mode:
                dam_rect = patches.Rectangle(
                    (-dam_w/2, 0), dam_w, h_up,
                    facecolor="gray", edgecolor="black", 
                    linewidth=2.5, hatch='//', alpha=0.8,
                    label="Concrete Dam", zorder=10
                )
                ax.add_patch(dam_rect)
                ax.plot([-dam_w/2, dam_w/2], [-0.5, -0.5], 'k-', lw=3, zorder=10)
                ax.text(0, -1.0, f'B = {dam_w:.1f}m', ha='center', 
                       fontweight='bold', fontsize=11,
                       bbox=dict(boxstyle='round', facecolor='white', edgecolor='black'))

            if "Pile" in mode:
                pile_rect = patches.Rectangle(
                    (pile_x - 0.25, -pile_d),
                    0.5, pile_d,
                    facecolor="black", edgecolor="yellow", 
                    linewidth=3, label="Sheet Pile", zorder=10
                )
                ax.add_patch(pile_rect)
                
                # Pile depth annotation
                ax.annotate('', xy=(pile_x + 1.5, -pile_d), xytext=(pile_x + 1.5, 0),
                          arrowprops=dict(arrowstyle='<->', color='black', lw=2.5))
                ax.text(pile_x + 2.0, -pile_d/2, f'D = {pile_d:.1f}m', 
                       rotation=90, va='center', fontweight='bold', fontsize=11,
                       bbox=dict(boxstyle='round', facecolor='white', edgecolor='black'))

            # Mark calculation point
            if res:
                ax.scatter(px, py, c="red", s=250, zorder=15, 
                         edgecolors='white', linewidths=3, marker='o')
                ax.text(px + 0.8, py + 0.6, 
                       f"u = {res['u']:.1f} kPa",
                       color="darkred", fontweight="bold", fontsize=12,
                       bbox=dict(facecolor='yellow', alpha=0.95, 
                               edgecolor='red', boxstyle='round,pad=0.7', linewidth=2.5))

            ax.set_xlabel("Horizontal Distance (m)", fontweight='bold', fontsize=12)
            ax.set_ylabel("Elevation (m)", fontweight='bold', fontsize=12)
            ax.set_title(f"Flow Net: {mode}\nΔh = {h_up - h_down:.1f}m | "
                        f"Nf = {Nf} flow channels | Nd = {Nd} equipotential drops", 
                        fontweight='bold', fontsize=13)
            ax.legend(loc='upper right', fontsize=10, framealpha=0.95)
            ax.grid(True, alpha=0.25, linestyle=':', linewidth=0.8)
            
            st.pyplot(fig)

            # Educational notes
            with st.expander(" Understanding Sheet Pile Flow Nets"):
                st.markdown(f"""
                **Configuration:** {mode}  
                **Upstream Head:** {h_up:.1f}m | **Downstream Head:** {h_down:.1f}m | **Head Loss:** {h_up - h_down:.1f}m
                
                ---
                
                ### **What You're Seeing:**
                
                The **sheet pile** at x = {pile_x:.1f}m extends to depth D = {pile_d:.1f}m, acting as a **vertical barrier**.  
                Water cannot flow through it, so it must travel **underneath the pile tip**.
                
                ### **Flow Pattern Explanation:**
                
                ** Blue Solid Lines (STREAMLINES):**
                - These show the **actual paths** water particles follow
                - Flow starts from upstream (left), travels horizontally
                - **Curves DOWN** to pass under the pile tip
                - Continues horizontally downstream (right)
                - Like following a single water molecule from start to finish
                
                ** Red Dashed Lines (EQUIPOTENTIALS):**
                - These connect points with the **same hydraulic head** (pressure + elevation)
                - Nearly **vertical** far from the pile
                - **Bend around the pile tip** where flow concentrates
                - Each line represents an equal drop in head = {(h_up - h_down) / Nd:.2f}m
                
                ### **Critical Engineering Points:**
                
                1. **Pile Tip = Highest Risk Zone:**
                   - Maximum hydraulic gradient occurs here
                   - Potential for **piping failure** (soil erosion)
                   - Pore pressures are highest at exit point
                
                2. **Seepage Quantity:**
                   $$q = k \\times \\Delta h \\times \\frac{{N_f}}{{N_d}}$$
                   Where k = soil permeability coefficient
                
                3. **Flow Path Length:**
                   - Deeper pile = Longer flow path = Less seepage
                   - Each meter of pile depth significantly reduces flow
                
                4. **Orthogonality Check:**
                   - Flow lines should intersect equipotentials at **90°**
                   - Creates approximately **square mesh elements**
                   - Validates the flow net accuracy
                
                ### **Design Implications:**
                
                - If gradient at pile tip > critical gradient → **Piping risk**
                - Pile depth determines effectiveness of cutoff
                - Exit gradient = {(h_up - h_down) / max(pile_d, 0.1):.2f} (approximate)
                
                 **Note:** This is a simplified 2D analysis. Real-world designs require 3D modeling and safety factors.
                """)

if __name__ == "__main__":
    app()
