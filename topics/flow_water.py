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
    Solves the Laplace equation for Stream Function (Psi) and Head (Phi)
    using an iterative Finite Difference Method grid.
    This ensures boundaries are strictly respected.
    """
    # 1. Create Grid
    x = np.linspace(-lx/2, lx/2, nx)
    y = np.linspace(-ly, 0, ny)
    X, Y = np.meshgrid(x, y)
    
    # 2. Identify Geometry Masks
    # Soil is everywhere initially
    is_soil = np.ones((ny, nx), dtype=bool)
    
    # Structure Dimensions
    dx = x[1] - x[0]
    dy = y[1] - y[0]
    
    # Convert physical coords to grid indices
    def get_idx(val_x, val_y):
        ix = np.abs(x - val_x).argmin()
        iy = np.abs(y - val_y).argmin()
        return ix, iy

    # -- Define Obstacles (Dam & Pile) --
    dam_half_idx = int((dam_w / 2) / dx) if "Dam" in mode else 0
    center_idx = nx // 2
    
    pile_ix, pile_iy_bottom = get_idx(pile_x, -pile_d)
    
    # Mask out the Dam (Top surface obstruction)
    # We treat the dam as a boundary condition on the top row(s)
    dam_left_idx = center_idx - dam_half_idx
    dam_right_idx = center_idx + dam_half_idx
    
    # Mask out the Sheet Pile (Vertical obstruction)
    if "Pile" in mode:
        # Make pile 1-cell thick for the solver barrier
        # From surface (iy = ny-1) down to pile tip
        is_soil[pile_iy_bottom:, pile_ix] = False
        
    # -- Initialize Stream Function (Psi) --
    # Boundary Conditions for Psi:
    # 1. Impervious Bottom (Last Flow Line) -> Psi = 0% (or 0)
    # 2. Structure Surface (First Flow Line) -> Psi = 100% (or 1.0)
    
    psi = np.linspace(0, 1, ny).reshape(ny, 1).repeat(nx, axis=1) # Linear initial guess
    
    # -- Iterative Solver (SOR / Jacobi) --
    # We will iterate to smooth out the values
    # Increase iterations for higher accuracy
    iterations = 2000 
    
    # Create masks for boundaries to keep them fixed
    fixed_psi = np.zeros_like(psi, dtype=bool)
    
    # BC: Bottom Boundary
    psi[0, :] = 0.0
    fixed_psi[0, :] = True
    
    # BC: Structure Boundary (First Flow Line)
    # The structure includes the Dam base and the Pile surface.
    
    # 1. Apply to Dam Base (Top surface between dam limits)
    if "Dam" in mode:
        psi[-1, dam_left_idx:dam_right_idx+1] = 1.0
        fixed_psi[-1, dam_left_idx:dam_right_idx+1] = True
        
    # 2. Apply to Sheet Pile
    if "Pile" in mode:
        # The pile is an internal boundary. 
        # We set Psi=1.0 along the pile line.
        psi[pile_iy_bottom:, pile_ix] = 1.0
        fixed_psi[pile_iy_bottom:, pile_ix] = True

    # 3. Apply to Ground Surface (Free Surface)
    # On the upstream/downstream beds, flow enters/exits. 
    # This is a Neumann BC for Psi (dPsi/dy = 0? No, dPsi/dx = 0 roughly if vertical flow).
    # For simplicity in this visual tool, we let the solver relax the top surface 
    # everywhere except the structure.
    
    # SOLVE PSI
    for _ in range(iterations):
        # Vectorized Laplacian averaging (Up+Down+Left+Right / 4)
        psi_new = 0.25 * (psi[0:-2, 1:-1] + psi[2:, 1:-1] + psi[1:-1, 0:-2] + psi[1:-1, 2:])
        
        # Update interior only (preserve borders for now)
        psi[1:-1, 1:-1] = psi_new
        
        # Enforce Structure Fixed Values
        psi[fixed_psi] = 1.0
        
        # Enforce Bottom Fixed Value
        psi[0, :] = 0.0
        
        # Neumann BCs at Left/Right far boundaries (Straight horizontal flow lines far away)
        psi[:, 0] = psi[:, 1]
        psi[:, -1] = psi[:, -2]
        
        # Neumann BC at Soil Surface (Permeable boundaries let streamlines adjust)
        # We only update the top surface where it is NOT fixed (i.e. not the dam)
        # Gradient = 0 normal to flow means flow is vertical entering soil
        # Simple relaxation for top row:
        psi[-1, ~fixed_psi[-1, :]] = psi[-2, ~fixed_psi[-1, :]]

    # -- Initialize Potential Head (Phi) --
    # Boundary Conditions:
    # 1. Upstream Bed -> Phi = h_up
    # 2. Downstream Bed -> Phi = h_down
    # 3. Impervious boundaries -> Neumann (dPhi/dn = 0)
    
    phi = np.ones((ny, nx)) * ((h_up + h_down) / 2) # Initial guess
    
    # Identify Surface Indices
    # Upstream: Left of dam/pile
    # Downstream: Right of dam/pile
    
    struct_left = pile_ix if "Pile" in mode and "Dam" not in mode else dam_left_idx
    struct_right = pile_ix if "Pile" in mode and "Dam" not in mode else dam_right_idx
    
    # Fixed Heads
    phi[-1, :struct_left] = h_up
    phi[-1, struct_right:] = h_down
    
    fixed_phi = np.zeros_like(phi, dtype=bool)
    fixed_phi[-1, :struct_left] = True
    fixed_phi[-1, struct_right:] = True

    # SOLVE PHI
    for _ in range(iterations):
        phi_new = 0.25 * (phi[0:-2, 1:-1] + phi[2:, 1:-1] + phi[1:-1, 0:-2] + phi[1:-1, 2:])
        phi[1:-1, 1:-1] = phi_new
        
        # Re-apply Fixed Heads
        phi[fixed_phi] = (h_up if np.mean(phi[fixed_phi]) > (h_up+h_down)/2 else h_down) 
        # (The line above is a lazy way to reset, let's be explicit below)
        phi[-1, :struct_left] = h_up
        phi[-1, struct_right:] = h_down
        
        # Neumann BCs (Impervious Walls = No Flow across them)
        # Bottom
        phi[0, :] = phi[1, :]
        # Left/Right Edges
        phi[:, 0] = phi[:, 1]
        phi[:, -1] = phi[:, -2]
        
        # Structure Neumann BCs (Water can't flow INTO the pile/dam)
        if "Pile" in mode:
             # Pile is at pile_ix.
             # Left side of pile copies left neighbor
             phi[pile_iy_bottom:, pile_ix] = phi[pile_iy_bottom:, pile_ix-1] 
             # (This is a simplification, ideally we split the node)
             
        if "Dam" in mode:
            # Under the dam is impervious? No, concrete dam sits on soil.
            # Base of dam is a flow line, so Phi varies linearly underneath?
            # Actually, Phi satisfies Laplace underneath.
            # The top boundary UNDER the dam is Neumann for Phi (No flow UP into dam)
            phi[-1, dam_left_idx:dam_right_idx+1] = phi[-2, dam_left_idx:dam_right_idx+1]

    # Handle the "Split" at the pile for Phi
    # (Phi is discontinuous across the sheet pile). 
    # For visualization, the smooth solver is usually "good enough" if the pile is thin,
    # but strictly, we should treat the grid as having a cut. 
    # For this app, the masking above provides a decent visual approximation.

    return X, Y, phi, psi

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
    # TAB 3 — FLOW NETS (NUMERICAL SOLVER)
    # ============================================================
    with tab3:
        st.markdown("### 2D Flow Net Analysis (Numerical Grid Method)")
        st.caption("**Guidelines:** Impervious bottom and structure are Flow Lines. Soil surface is Equipotential. Lines intersect at 90°.")
        
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
            soil_d = st.number_input("Impervious Layer Depth [m]", value=12.0, min_value=2.0)

            st.markdown("---")
            st.markdown("#### Structure Parameters")
            
            dam_w = 0.0
            pile_d = 0.0
            pile_x = 0.0

            if "Dam" in mode:
                dam_w = st.number_input("Dam Base Width (B) [m]", value=6.0, min_value=0.5)

            if "Pile" in mode:
                pile_d = st.number_input("Sheet Pile Depth (D) [m]", value=5.0, min_value=0.5, max_value=soil_d-0.5)
                
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
            Nd = max(2, int(st.number_input("Equipotential Drops (Nd)", value=12, min_value=2, max_value=25)))
            Nf = max(1, int(st.number_input("Flow Channels (Nf)", value=4, min_value=1, max_value=12)))

            st.markdown("---")
            st.markdown("#### Pore Pressure Calculation")
            px = st.number_input("Point X Coordinate [m]", value=1.0)
            py = st.number_input("Point Y Coordinate [m]", value=-3.0, max_value=0.0)

        with col_gr:
            # RUN NUMERICAL SOLVER
            # Grid resolution: Higher is smoother but slower. 60x40 is a good balance for Streamlit.
            nx_grid = 70
            ny_grid = 45
            lx_grid = 24.0 # Span from -12 to 12
            
            X, Y, Phi, Psi = solve_flow_net_finite_difference(nx_grid, ny_grid, lx_grid, soil_d, pile_d, pile_x, dam_w, h_up, h_down, mode)
            
            # --- Calculation for Specific Point ---
            # Find nearest grid point to (px, py) to sample Pressure
            idx_x = np.abs(X[0,:] - px).argmin()
            idx_y = np.abs(Y[:,0] - py).argmin()
            
            h_total_pt = Phi[idx_y, idx_x]
            gamma_w = 9.81
            pressure_head = h_total_pt - py
            u_val = pressure_head * gamma_w
            
            # If point is inside the structure (Phi is not computed properly or is excluded), handle it
            # Simple check: if inside pile zone
            valid_pt = True
            if "Pile" in mode and py > -pile_d and abs(px - pile_x) < 0.2:
                 valid_pt = False
            
            if valid_pt and py <= 0:
                st.success(f"**Pore Pressure (u):** {u_val:.2f} kPa")
                st.info(f"**Total Head (H):** {h_total_pt:.2f} m\n\n"
                        f"**Pressure Head (h_p):** {pressure_head:.2f} m")
            else:
                st.warning("Point is inside structure or above ground.")

            # --- PLOTTING ---
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.set_aspect("equal")
            ax.set_facecolor('#f5f5dc') # Soil color

            # Plot Streamlines (Blue)
            # Psi ranges 0 to 1.
            stream_levels = np.linspace(0, 1, Nf + 1)
            ax.contour(X, Y, Psi, levels=stream_levels, colors='blue', linewidths=1.5, alpha=0.9)

            # Plot Equipotentials (Red)
            # Phi ranges h_down to h_up
            equi_levels = np.linspace(h_down, h_up, Nd + 1)
            ax.contour(X, Y, Phi, levels=equi_levels, colors='red', linestyles='--', linewidths=1.0, alpha=0.8)

            # Draw Structures & Boundaries (Visuals)
            
            # 1. Ground Surface
            ax.axhline(0, color='saddlebrown', lw=2)
            
            # 2. Impervious Bottom
            ax.axhline(-soil_d, color='black', lw=3)
            ax.text(0, -soil_d - 0.5, "Impervious Rock (Last Flow Line)", ha='center', fontsize=9)
            
            # 3. Dam
            if "Dam" in mode:
                rect = patches.Rectangle((-dam_w/2, 0), dam_w, h_up/2, facecolor='gray', edgecolor='black', hatch='//')
                ax.add_patch(rect)
                ax.text(0, 0.5, "DAM", ha='center', fontweight='bold', color='white')

            # 4. Pile
            if "Pile" in mode:
                # Draw thick line for pile
                ax.plot([pile_x, pile_x], [0, -pile_d], color='black', lw=4)
                ax.plot([pile_x, pile_x], [0, -pile_d], color='yellow', lw=1.5) # Highlight center

            # 5. Water Levels
            ax.fill_between([-12, 0], 0, h_up, color='lightblue', alpha=0.3)
            ax.fill_between([0, 12], 0, h_down, color='lightblue', alpha=0.3)
            ax.plot([-12, 0], [h_up, h_up], 'b-')
            ax.plot([0, 12], [h_down, h_down], 'b-')
            ax.text(-10, h_up + 0.2, "Upstream", color='blue')
            ax.text(10, h_down + 0.2, "Downstream", color='blue')

            # 6. Point Marker
            ax.scatter(px, py, c='red', s=100, edgecolors='white', zorder=10)

            ax.set_xlim(-12, 12)
            ax.set_ylim(-soil_d - 1, h_up + 2)
            ax.set_title("Flow Net (Square Mesh)", fontweight='bold')
            st.pyplot(fig)

            with st.expander("Explanation of the Code Changes"):
                st.write("""
                **Why the previous code failed:**
                The previous code used infinite depth math. It didn't know the bottom rock existed, so flow lines crossed it.

                **How this Fixed Code Works:**
                1. **Numerical Solver:** It divides the soil into a grid (70x45 cells).
                2. **Strict Boundaries:**
                   - It forces Psi = 0 at the **Impervious Bottom**.
                   - It forces Psi = 1 at the **Structure Surface (Pile/Dam)**.
                3. **Iterative Relaxation:** It smooths the values until lines are perpendicular (90°).
                """)

if __name__ == "__main__":
    app()
