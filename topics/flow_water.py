import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# ============================================================
# HELPER FUNCTIONS (Formatting)
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
# NUMERICAL SOLVER FOR FLOW NETS (Finite Difference)
# ============================================================

def solve_flow_net_finite_difference(nx, ny, lx, ly, pile_d, pile_x, dam_w, h_up, h_down, mode):
    """
    Solves the Laplace equation for Stream Function (Psi) and Head (Phi).
    Enforces strict boundary conditions so flow lines start/end at the soil surface.
    """
    # 1. Create Grid
    x = np.linspace(-lx/2, lx/2, nx)
    y = np.linspace(-ly, 0, ny)
    
    # 2. Identify Indices for Structures
    def get_x_idx(val): return np.abs(x - val).argmin()
    def get_y_idx(val): return np.abs(y - val).argmin()

    center_idx = nx // 2
    pile_ix = get_x_idx(pile_x)
    pile_iy_tip = get_y_idx(-pile_d)
    
    # Dam indices
    dam_left_ix = get_x_idx(-dam_w/2) if "Dam" in mode else center_idx
    dam_right_ix = get_x_idx(dam_w/2) if "Dam" in mode else center_idx

    # 3. Initialize Matrices
    # Psi (Stream Function): 0 = Bottom, 1 = Structure/Surface
    psi = np.zeros((ny, nx))
    
    # Initial Guess: Linear distribution
    for i in range(ny):
        psi[i, :] = i / (ny - 1)

    # 4. Iterative Solver (SOR Method)
    iterations = 3000  # High iteration count for convergence
    for k in range(iterations):
        # Laplace Equation
        psi_new = 0.25 * (psi[0:-2, 1:-1] + psi[2:, 1:-1] + psi[1:-1, 0:-2] + psi[1:-1, 2:])
        psi[1:-1, 1:-1] = psi_new
        
        # --- BOUNDARY CONDITIONS ---
        
        # A. Impervious Bottom (Last Flow Line) -> Psi = 0
        psi[0, :] = 0.0
        
        # B. Structure Boundary (First Flow Line) -> Psi = 1.0
        if "Pile" in mode:
            psi[pile_iy_tip:, pile_ix] = 1.0
            
        if "Dam" in mode:
            psi[-1, dam_left_ix:dam_right_ix+1] = 1.0

        # C. Soil Surface (Entry/Exit) - Relaxation
        if "Dam" in mode:
            # Left of dam
            psi[-1, :dam_left_ix] = psi[-2, :dam_left_ix]
            # Right of dam
            psi[-1, dam_right_ix+1:] = psi[-2, dam_right_ix+1:]
        else:
            # No dam: Relax whole top surface (except the exact pile point)
            psi[-1, :pile_ix] = psi[-2, :pile_ix]
            psi[-1, pile_ix+1:] = psi[-2, pile_ix+1:]

        # D. Left/Right Boundaries
        psi[:, 0] = psi[:, 1]
        psi[:, -1] = psi[:, -2]

    # 5. Solve for Head (Phi)
    phi = np.full((ny, nx), (h_up + h_down)/2)
    
    # Establish Fixed Head Zones
    phi[-1, : (dam_left_ix if "Dam" in mode else pile_ix)] = h_up
    phi[-1, (dam_right_ix if "Dam" in mode else pile_ix)+1 :] = h_down
    
    for k in range(iterations):
        phi_new = 0.25 * (phi[0:-2, 1:-1] + phi[2:, 1:-1] + phi[1:-1, 0:-2] + phi[1:-1, 2:])
        phi[1:-1, 1:-1] = phi_new
        
        # Fixed Heads at Surface
        mid_ix = pile_ix if "Pile" in mode and "Dam" not in mode else dam_left_ix
        end_ix = pile_ix if "Pile" in mode and "Dam" not in mode else dam_right_ix
        
        phi[-1, :mid_ix] = h_up
        phi[-1, end_ix+1:] = h_down
        
        # Impervious Boundaries
        phi[0, :] = phi[1, :]       # Bottom
        phi[:, 0] = phi[:, 1]       # Far Left
        phi[:, -1] = phi[:, -2]     # Far Right

    return x, y, phi, psi

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
    # TAB 1: 1D SEEPAGE
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
    # TAB 3 CONTENT
    # ============================================================
    with tab3:
        st.markdown("### 2D Flow Net Analysis")
        st.caption("**Principles:** Streamlines (Blue) start at upstream surface, loop under structure, end at downstream surface.")
        
        col_in, col_gr = st.columns([1, 1.4])

        with col_in:
            mode = st.radio("Structure Type", ["Sheet Pile Only", "Concrete Dam Only", "Combined (Dam + Pile)"])
            
            st.markdown("---")
            h_up = st.number_input("Upstream Head [m]", value=10.0)
            h_down = st.number_input("Downstream Head [m]", value=2.0)
            soil_d = st.number_input("Impervious Layer Depth [m]", value=12.0)

            st.markdown("---")
            dam_w, pile_d, pile_x = 0.0, 0.0, 0.0
            
            if "Dam" in mode:
                dam_w = st.number_input("Dam Width [m]", value=6.0)
            if "Pile" in mode:
                pile_d = st.number_input("Pile Depth [m]", value=6.0)
                pile_x = st.number_input("Pile X Position [m]", value=0.0)

            st.markdown("---")
            Nf = st.slider("Number of Flow Channels (Nf)", 3, 10, 4)
            Nd = st.slider("Number of Equipotential Drops (Nd)", 6, 20, 12)
            
            # Pore Pressure Input
            st.markdown("---")
            st.markdown("**Check Pore Pressure**")
            px = st.number_input("X Coord [m]", value=1.5)
            py = st.number_input("Y Coord [m]", value=-4.0, max_value=0.0)

        with col_gr:
            # Run Solver
            nx, ny = 70, 50 # Grid Resolution
            lx = 24.0 # Domain Width
            x, y, phi, psi = solve_flow_net_finite_difference(nx, ny, lx, soil_d, pile_d, pile_x, dam_w, h_up, h_down, mode)
            X, Y = np.meshgrid(x, y)
            
            # Plotting
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.set_aspect('equal')
            ax.set_facecolor('#fdf6e3')
            
            # 1. Plot STREAMLINES (Blue)
            # We explicitly include 0.0 (Bottom) and 1.0 (Structure) in the levels
            levels_psi = np.linspace(0, 1.0, Nf + 1)
            ax.contour(X, Y, psi, levels=levels_psi, colors='blue', linewidths=2)
            
            # 2. Plot EQUIPOTENTIALS (Red)
            levels_phi = np.linspace(h_down, h_up, Nd + 1)
            ax.contour(X, Y, phi, levels=levels_phi, colors='red', linestyles='--', linewidths=1)
            
            # 3. Draw Geometry
            ax.axhline(0, color='saddlebrown', lw=3) # Ground
            ax.axhline(-soil_d, color='black', lw=3) # Bedrock
            
            if "Dam" in mode:
                rect = patches.Rectangle((-dam_w/2, 0), dam_w, h_up/2, facecolor='gray', hatch='//', edgecolor='k')
                ax.add_patch(rect)
            if "Pile" in mode:
                ax.plot([pile_x, pile_x], [0, -pile_d], 'k-', lw=5) # Pile
                ax.plot([pile_x, pile_x], [0, -pile_d], 'y--', lw=1)
                
            # Water
            ax.fill_between([-12, (pile_x if "Pile" in mode and "Dam" not in mode else -dam_w/2)], 0, h_up, color='lightblue', alpha=0.3)
            ax.fill_between([(pile_x if "Pile" in mode and "Dam" not in mode else dam_w/2), 12], 0, h_down, color='lightblue', alpha=0.3)
            
            # Pore Pressure Calculation Point
            # Interpolate Phi at (px, py)
            try:
                # Simple nearest neighbor for robustness
                ix = np.abs(x - px).argmin()
                iy = np.abs(y - py).argmin()
                h_val = phi[iy, ix]
                u_val = (h_val - py) * 9.81
                
                # Check if point is in soil
                valid = True
                if "Pile" in mode and abs(px - pile_x) < 0.2 and py > -pile_d: valid = False
                
                if valid and py <= 0:
                    ax.scatter(px, py, c='red', s=100, edgecolors='white', zorder=10)
                    st.success(f"**Pore Pressure at ({px}, {py}):** {u_val:.2f} kPa")
                else:
                    st.warning("Point is inside structure or above ground.")
            except:
                pass
                
            ax.set_ylim(-soil_d - 1, h_up + 1)
            ax.set_xlim(-12, 12)
            st.pyplot(fig)

if __name__ == "__main__":
    app()
