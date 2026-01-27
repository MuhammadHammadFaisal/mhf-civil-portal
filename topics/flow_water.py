import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

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

def get_complex_potential(x, y, mode, pile_depth, pile_x, dam_width):
    z = x + 1j * y

    # singularity avoidance logic
    if np.isscalar(z):
        avoid_x = pile_x if "Pile" in mode else 0
        if abs(z - avoid_x) < 0.05:
            z += 0.05j

    with np.errstate(all="ignore"):
        if mode == "Sheet Pile Only":
            d = max(pile_depth, 0.1)
            # Center the coordinate system on the pile
            return np.arcsinh((z - pile_x) / d)

        if mode == "Concrete Dam Only":
            c = max(dam_width / 2, 0.1)
            # Dam base creates a wider flow path
            return np.arccosh(z / c)

        if mode == "Combined (Dam + Pile)":
            # --- HEURISTIC SUPERPOSITION ---
            # 1. Effect of Dam (base width)
            c = max(dam_width / 2, 0.1)
            
            # 2. Effect of Pile (depth)
            d = max(pile_depth, 0.1)

            # Simple visualization hack: Use the pile formula but increase the 
            # effective depth based on the dam width to simulate longer path
            effective_depth = d + (c * 0.5) 
            return np.arcsinh((z - pile_x) / effective_depth)
        
    return 0 + 0j

def solve_smart_point(px, py, h_up, h_down, datum, mode, pile_d, pile_x, dam_w):
    """
    Calculates pore pressure at a specific point (px, py).
    """
    # 1. Calculate Complex Potential at the specific point
    w_pt = get_complex_potential(px, py, mode, pile_d, pile_x, dam_w)
    
    # Based on the plotting logic in Tab 3:
    # Psi (Real) = Stream Function
    # Phi (Imag) = Potential Function
    phi_pt = np.imag(w_pt)

    # 2. Determine Boundary Potentials to interpolate Head
    # We sample points far upstream and downstream just below the surface
    # to find the range of Phi values corresponding to h_up and h_down.
    y_sample = -0.1
    x_far_left = -15.0
    x_far_right = 15.0
    
    w_up = get_complex_potential(x_far_left, y_sample, mode, pile_d, pile_x, dam_w)
    w_down = get_complex_potential(x_far_right, y_sample, mode, pile_d, pile_x, dam_w)
    
    phi_up = np.imag(w_up)
    phi_down = np.imag(w_down)

    # 3. Interpolate Total Head (H)
    # Linear interpolation of Phi between boundaries
    if abs(phi_up - phi_down) < 1e-6:
        ratio = 0.5
    else:
        ratio = (phi_pt - phi_down) / (phi_up - phi_down)
    
    # Calculate Total Head
    h_total = h_down + ratio * (h_up - h_down)

    # 4. Calculate Pore Pressure (u)
    # Bernoulli: Total Head = Elevation Head + Pressure Head
    # h_total = y + (u / gamma_w)
    # u = (h_total - y) * gamma_w
    
    elevation_head = py # Assuming y is elevation relative to datum 0
    pressure_head = h_total - elevation_head
    
    gamma_w = 9.81
    u = pressure_head * gamma_w
    
    return {"u": u, "h_total": h_total}

# ============================================================
# MAIN APP
# ============================================================

def app():
    st.set_page_config(page_title="Soil Mechanics Analysis", layout="wide")
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

  # ============================================================
    # TAB 3 — FLOW NETS
    # ============================================================
    with tab3:
        col_in, col_gr = st.columns([1, 1.4])
     st.title("🚧 Module Under Construction")
        with col_in:
            mode = st.radio(
                "Structure Type",
                ["Sheet Pile Only", "Concrete Dam Only", "Combined (Dam + Pile)"]
            )

            # 1. Initialize variables to prevent crash if mode changes
            dam_w = 0.0
            pile_d = 0.0
            pile_x = 0.0

            # 2. Logic Fix: Independent Inputs (Fixed Indentation)
            if "Dam" in mode:
                dam_w = st.number_input("Dam Width (B)", 6.0)

            if "Pile" in mode:
                pile_d = st.number_input("Pile Depth (D)", value=5.0)
                
                limit = dam_w / 2 if "Dam" in mode else 10.0
                pile_x = st.number_input(
                    "Pile X Location",
                    value=0.0,
                    min_value=-limit,
                    max_value=limit
                )

            soil_d = st.number_input("Impervious Layer Depth", 12.0)
            h_up = st.number_input("Upstream Head", 10.0)
            h_down = st.number_input("Downstream Head", 2.0)

            Nd = max(2, int(st.number_input("Potential Drops (Nd)", 12)))
            Nf = max(1, int(st.number_input("Flow Channels (Nf)", 4)))

            datum = st.number_input("Datum Elevation", value=-soil_d)
            px = st.number_input("Point X", 2.0)
            py = st.number_input("Point Y", -4.0)

            # 3. Logic Fix: Inline Calculation for Pore Pressure
            # (Replaces the missing 'solve_smart_point' function)
            res = None
            if py <= 0:
                # A. Get Potential at the specific point
                w_pt = get_complex_potential(px, py, mode, pile_d, pile_x, dam_w)
                # For this mapping: Real=Streamline, Imag=Potential
                phi_pt = np.imag(w_pt) 

                # B. Get Boundary Potentials (Sample just below surface to catch branch cuts)
                w_up = get_complex_potential(-15.0, -0.01, mode, pile_d, pile_x, dam_w)
                w_down = get_complex_potential(15.0, -0.01, mode, pile_d, pile_x, dam_w)
                phi_up = np.imag(w_up)
                phi_down = np.imag(w_down)

                # C. Interpolate Head
                if abs(phi_up - phi_down) < 1e-6:
                    h_total = h_down # No flow/gradient
                else:
                    ratio = (phi_pt - phi_down) / (phi_up - phi_down)
                    h_total = h_down + ratio * (h_up - h_down)

                # D. Calculate Pore Pressure: u = (h_total - elevation) * gamma_w
                u_val = (h_total - py) * 9.81
                res = {"u": u_val}
                
                st.success(f"Pore Pressure u = {res['u']:.2f} kPa")
            else:
                st.warning("Point must be below ground surface")

        with col_gr:
            fig, ax = plt.subplots(figsize=(7, 6))
            ax.set_xlim(-12, 12)
            ax.set_ylim(-soil_d - 1, h_up + 2)
            ax.set_aspect("equal")

            gx = np.linspace(-12, 12, 200)
            gy = np.linspace(-soil_d, 0, 150)
            X, Y = np.meshgrid(gx, gy)

            W = get_complex_potential(X, Y, mode, pile_d, pile_x, dam_w)
            
            # Logic Check:
            # Psi (Real Part) = Streamlines (Loops connecting Upstream/Downstream)
            # Phi (Imag Part) = Equipotentials (Lines dropping from Upstream to Downstream)
            Psi, Phi = np.real(W), np.imag(W)

            # Calculate deep soil stream value for plot limits
            ref_x = pile_x if "Pile" in mode else 0
            psi_max = np.real(get_complex_potential(ref_x + 0.1, -soil_d,
                                                    mode, pile_d, pile_x, dam_w))
            
            # Sanity check to prevent empty plots if calculation fails
            if not np.isfinite(psi_max) or abs(psi_max) < 0.1:
                psi_max = 3.0

            # Plot Flow Lines (Psi) - Blue
            ax.contour(X, Y, Psi,
                       levels=np.linspace(0, psi_max, Nf + 1),
                       colors="blue", linewidths=1.5, alpha=0.7)

            # Plot Equipotential Lines (Phi) - Red
            # Use nanmin/nanmax to handle the branch cuts correctly
            ax.contour(X, Y, Phi,
                       levels=np.linspace(np.nanmin(Phi), np.nanmax(Phi), Nd + 1),
                       colors="red", linestyles="--", linewidths=1.5, alpha=0.7)

            # Boundaries
            ax.axhline(0, color="black", lw=2)
            ax.axhline(-soil_d, color="black", lw=3)

            if "Dam" in mode:
                ax.add_patch(
                    patches.Rectangle((-dam_w/2, 0), dam_w, h_up,
                                      color="gray", zorder=10)
                )

            if "Pile" in mode:
                ax.add_patch(
                    patches.Rectangle((pile_x - 0.15, -pile_d),
                                      0.3, pile_d + h_up,
                                      color="black", zorder=11)
                )

            if res:
                ax.scatter(px, py, c="red", s=100, zorder=12, edgecolors='white')
                ax.text(px + 0.5, py, f"u={res['u']:.1f} kPa",
                        color="red", fontweight="bold", zorder=12,
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

            ax.axis("off")
            st.pyplot(fig)


if __name__ == "__main__":
    app()
