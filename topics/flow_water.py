import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- HELPER FUNCTIONS ---

def format_scientific(val):
    if val == 0: return "0"
    exponent = int(np.floor(np.log10(abs(val))))
    mantissa = val / (10**exponent)
    if -3 < exponent < 4: return f"{val:.4f}"
    else: return f"{mantissa:.2f} \\times 10^{{{exponent}}}"

def solve_flow_net_at_point(h_upstream, h_downstream, total_Nd, drops_passed, y_point, datum_elev):
    """
    Calculates head and pressure using Flow Net Counting Method.
    Works for Dam, Pile, or Combined structures.
    """
    H_diff = h_upstream - h_downstream
    delta_h = H_diff / total_Nd if total_Nd > 0 else 0
    h_point = h_upstream - (drops_passed * delta_h)
    z = y_point - datum_elev
    hp = h_point - z
    gamma_w = 9.81
    u = hp * gamma_w
    
    return {
        "H_diff": H_diff, "delta_h": delta_h, "h_point": h_point,
        "hp": hp, "u": u, "z": z, "nd_passed": drops_passed,
        "Nd_total": total_Nd, "datum": datum_elev
    }

# --- MAIN APP ---

def app():
    st.markdown("---")
    st.subheader("Flow of Water & Seepage Analysis")

    # TABS
    tab1, tab2, tab3 = st.tabs(["1D Seepage (Effective Stress)", "Permeability Tests", "Flow Nets & Piping"])

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
            val_A = st.slider("Height of Point 'A' from Datum [m]", 0.0, val_z, val_z/2)

            st.markdown("---")
            if st.button("Calculate Effective Stress", type="primary"):
                H_top = val_z + val_y
                H_bot = val_x
                h_loss = H_top - H_bot
                
                if h_loss > 0: flow_type, effect_msg = "Downward", "Downward Flow increases Effective Stress (+i·z·γw)"
                elif h_loss < 0: flow_type, effect_msg = "Upward", "Upward Flow decreases Effective Stress (-i·z·γw)"
                else: flow_type, effect_msg = "No Flow", "Hydrostatic Condition"

                gamma_w = 9.81
                sigma_total = (val_y * gamma_w) + ((val_z - val_A) * gamma_sat)
                H_A = H_bot + (val_A / val_z) * (H_top - H_bot)
                h_p_A = H_A - val_A
                u_val = h_p_A * gamma_w
                sigma_prime = sigma_total - u_val
                
                st.success(f"**Flow Condition:** {flow_type}\n\n*{effect_msg}*")
                st.metric("Total Stress (σ)", f"{sigma_total:.2f} kPa")
                st.metric("Pore Pressure (u)", f"{u_val:.2f} kPa")
                st.metric("Effective Stress (σ')", f"{sigma_prime:.2f} kPa")

        with col_plot:
            fig, ax = plt.subplots(figsize=(7, 8))
            datum_y, soil_w, soil_x = 0.0, 2.5, 3.5
            wl_top, wl_bot = val_z + val_y, val_x
            flow_arrow = "⬇️" if wl_top > wl_bot else ("⬆️" if wl_bot > wl_top else "No Flow")

            ax.add_patch(patches.Rectangle((soil_x, datum_y), soil_w, val_z, facecolor='#E3C195', hatch='...', edgecolor='none'))
            ax.text(soil_x + soil_w/2, datum_y + val_z/2, "SOIL", ha='center', fontweight='bold', fontsize=12)
            
            # Tanks & Pipes Visuals (Simplified for brevity in fix)
            tank_w, tank_x = 2.0, soil_x + (soil_w - 2.0)/2
            tank_base_y = max(datum_y + val_z, wl_top - 0.5)
            ax.add_patch(patches.Rectangle((tank_x, tank_base_y), tank_w, wl_top - tank_base_y, facecolor='#D6EAF8'))
            
            # Walls
            ax.plot([tank_x, tank_x], [wl_top+0.5, tank_base_y], 'k-', lw=2)
            ax.plot([tank_x+tank_w, tank_x+tank_w], [wl_top+0.5, tank_base_y], 'k-', lw=2)
            ax.plot([soil_x, soil_x], [datum_y, val_z+datum_y], 'k-', lw=2)
            ax.plot([soil_x+soil_w, soil_x+soil_w], [datum_y, val_z+datum_y], 'k-', lw=2)

            # Water Levels
            ax.plot([tank_x, tank_x+tank_w], [wl_top, wl_top], 'b-', lw=2)
            ax.text(tank_x-0.5, wl_top, f"H_top={wl_top:.2f}", color='blue', fontsize=8)
            
            # Piezometer Level
            ax.plot([soil_x-1, soil_x], [wl_bot, wl_bot], 'b--', lw=1)
            ax.text(soil_x-1.2, wl_bot, f"H_bot={wl_bot:.2f}", color='blue', ha='right', fontsize=8)

            # Point A
            ax.scatter(soil_x + soil_w/2, datum_y + val_A, c='red', s=100, zorder=5)
            ax.text(soil_x + soil_w/2 + 0.2, datum_y + val_A, "A", color='red', fontweight='bold')

            ax.set_ylim(-1, max(wl_top, wl_bot)+1)
            ax.axis('off')
            st.pyplot(fig)

    # =================================================================
    # TAB 2: PERMEABILITY
    # =================================================================
    with tab2:
        st.write("Permeability Test Calculator (Standard Formulae)")
        # (Content preserved from previous versions implies standard implementation)
        st.info("Select a test type to calculate k.")
        test_type = st.radio("Method:", ["Constant Head", "Falling Head"])
        
        if test_type == "Constant Head":
            Q = st.number_input("Q (cm³)", 500.0)
            L = st.number_input("L (cm)", 15.0)
            h = st.number_input("h (cm)", 40.0)
            A = st.number_input("A (cm²)", 40.0)
            t = st.number_input("t (sec)", 60.0)
            if st.button("Calculate k"):
                k = (Q*L)/(A*h*t)
                st.success(f"k = {format_scientific(k)} cm/sec")
        else:
            a_stand = st.number_input("a (cm²)", 0.5)
            L = st.number_input("L (cm)", 15.0)
            A = st.number_input("A (cm²)", 40.0)
            h1 = st.number_input("h1 (cm)", 50.0)
            h2 = st.number_input("h2 (cm)", 30.0)
            t = st.number_input("t (sec)", 300.0)
            if st.button("Calculate k"):
                k = (2.303*a_stand*L)/(A*t) * np.log10(h1/h2)
                st.success(f"k = {format_scientific(k)} cm/sec")

    # =================================================================
    # TAB 3: FLOW NETS (CORRECTED VISUALS)
    # =================================================================
    with tab3:
        st.markdown("### Flow Net Analysis")
        st.caption("Design Flow Nets for Dams, Sheet Piles, or Combined systems.")
        
        col_input, col_plot = st.columns([1, 1.2])

        with col_input:
            st.markdown("#### 1. Configuration")
            has_dam = st.checkbox("Include Concrete Dam", value=True)
            has_pile = st.checkbox("Include Sheet Pile (Cutoff)", value=False)
            
            dam_width = 0.0; pile_depth = 0.0; pile_x = 0.0
            if has_dam:
                dam_width = st.number_input("Dam Base Width (B) [m]", value=6.0, step=0.5)
            if has_pile:
                c_p1, c_p2 = st.columns(2)
                pile_depth = c_p1.number_input("Pile Depth (D) [m]", value=5.0, step=0.5)
                limit_x = dam_width/2.0 if has_dam else 8.0
                pile_x = c_p2.number_input("Pile X Location [m]", value=0.0, step=0.5, min_value=-limit_x, max_value=limit_x)

            st.markdown("#### 2. Soil Profile")
            soil_depth = st.number_input("Depth of Impervious Layer (T) [m]", value=12.0, step=1.0)

            st.markdown("#### 3. Hydraulics & Counting")
            c_h1, c_h2 = st.columns(2)
            h_up = c_h1.number_input("Upstream Head ($H_{up}$) [m]", value=4.5)
            h_down = c_h2.number_input("Downstream Head ($H_{down}$) [m]", value=0.5)
            
            c_net1, c_net2 = st.columns(2)
            Nd = c_net1.number_input("Total Potential Drops ($N_d$)", value=12, step=1)
            Nf = c_net2.number_input("Total Flow Channels ($N_f$)", value=4, step=1)
            
            st.markdown("#### 4. Point Calculator")
            datum = st.number_input("Datum Elevation ($z=0$)", value=-soil_depth, step=1.0)
            
            c_pt1, c_pt2, c_pt3 = st.columns(3)
            x_point = c_pt1.number_input("Point X", value=2.0)
            y_point = c_pt2.number_input("Point Y", value=-4.0)
            nd_point = c_pt3.number_input("Drops Passed ($n_d$)", value=4.5, step=0.1)
            
            results = solve_flow_net_at_point(h_up, h_down, Nd, nd_point, y_point, datum)
            
            st.markdown(f"""
            <div style="background-color: #e3f2fd; color: #333333; border: 1px solid #90caf9; border-radius: 8px; padding: 10px; margin-top: 10px;">
                <h4 style="color: #1565c0; margin: 0;">Point Results</h4>
                <b>Total Head (h):</b> {results['h_point']:.2f} m <br>
                <b>Pore Pressure (u):</b> <span style="color: #d63384; font-weight: bold;">{results['u']:.2f} kPa</span>
            </div>
            """, unsafe_allow_html=True)
            
            k_val = st.number_input("k [m/sec]", value=1e-6, format="%.1e")
            q = k_val * results['H_diff'] * (Nf / Nd)
            st.info(f"Seepage q = {format_scientific(q)} m³/sec/m")

        with col_plot:
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.set_xlim(-10, 10)
            ax.set_ylim(-soil_depth - 1, max(h_up, h_down) + 2)
            ax.set_aspect('equal')
            
            # --- 1. BOUNDARIES ---
            ax.axhline(0, color='black', linewidth=1.5) # Ground
            ax.axhline(-soil_depth, color='black', linewidth=2) # Bedrock
            ax.add_patch(patches.Rectangle((-10, -soil_depth - 2), 20, 2, facecolor='gray', hatch='///'))
            ax.text(0, -soil_depth - 0.8, "IMPERVIOUS BOUNDARY", ha='center', fontsize=8, fontweight='bold')
            ax.axhline(datum, color='green', ls='-.', alpha=0.6)

            # --- 2. MATH ENGINE (FIXED FOR PILE) ---
            gx = np.linspace(-10, 10, 250)
            gy = np.linspace(-soil_depth, 0, 250)
            X, Y = np.meshgrid(gx, gy)
            Z = X + 1j * Y
            
            # Complex Potential W = Phi + i*Psi
            # For Pile: Use arcsinh((Z-x)/D) -> Vertical Cut behavior
            # For Dam: Use arccosh(Z/B) -> Horizontal Cut behavior
            
            if has_pile:
                # Vertical Cut Math
                Z_shifted = (X - pile_x) + 1j * Y
                # arcsinh creates a cut on the imaginary axis from -i to i.
                # mapping: z = d * sinh(w) -> w = arcsinh(z/d)
                with np.errstate(invalid='ignore', divide='ignore'):
                    W = np.arcsinh(Z_shifted / pile_depth)
                
                # In arcsinh map:
                # Real(W) = Equipotentials (Hyperbolas wrapping ground)
                # Imag(W) = Streamlines (Ellipses wrapping pile)
                Phi = np.real(W) # Potentials
                Psi = np.imag(W) # Flow lines
                
                # Fix range for plotting
                # Psi goes from -PI/2 (left of pile) to +PI/2 (right of pile)
                # We want flow lines to look like loops. 
                # Actually, standard arcsinh flow lines wrap the tip.
                # Let's shift Psi to be 0 at the pile surface for easier contouring?
                # Actually, strictly: Psi=const are ellipses. 
                # We want to visualize "Channels".
                
            elif has_dam:
                # Horizontal Cut Math (Standard Dam)
                C = dam_width / 2.0
                with np.errstate(invalid='ignore', divide='ignore'):
                    W = np.arccosh(Z / C)
                Phi = np.real(W) # Potentials (Hyperbolas)
                Psi = np.abs(np.imag(W)) # Flow (Ellipses) - Force positive
                
            else:
                Phi = np.zeros_like(X)
                Psi = np.zeros_like(Y)

            # --- 3. DRAW GRID ---
            if has_pile or has_dam:
                # Flow Lines (Blue)
                # We need to clamp the contours to stop at bedrock
                # Calculate max Psi at bedrock center
                if has_pile:
                    # For arcsinh, Psi varies. We want N lines.
                    # Max Psi is actually PI/2.
                    ax.contour(X, Y, Psi, levels=Nf+1, colors='blue', linewidths=1, linestyles='solid', alpha=0.6)
                    # Equipotentials (Red)
                    ax.contour(X, Y, Phi, levels=Nd+1, colors='red', linewidths=1, linestyles='dashed', alpha=0.6)
                elif has_dam:
                    # Bedrock check
                    z_rock = 0 + 1j * (-soil_depth)
                    w_rock = np.arccosh(z_rock / (dam_width/2.0))
                    psi_max = np.abs(np.imag(w_rock))
                    if np.isnan(psi_max): psi_max = 3.14
                    
                    ax.contour(X, Y, Psi, levels=np.linspace(0, psi_max, Nf+1), colors='blue', linewidths=1, linestyles='solid', alpha=0.6)
                    ax.contour(X, Y, Phi, levels=Nd+1, colors='red', linewidths=1, linestyles='dashed', alpha=0.6)

            # --- 4. DRAW STRUCTURES & MASKING ---
            if has_dam:
                C = dam_width / 2.0
                ax.add_patch(patches.Rectangle((-C, 0), 2*C, h_up+1, facecolor='#666', edgecolor='black', zorder=10))
                ax.text(0, 1, "DAM", ha='center', color='white', fontweight='bold', zorder=11)

            if has_pile:
                pw = 0.4 # Slightly wider for visibility
                # Draw Pile
                ax.add_patch(patches.Rectangle((pile_x - pw/2, -pile_depth), pw, pile_depth + h_up + 1, facecolor='#333', edgecolor='black', zorder=10))
                
                # **CRITICAL FIX**: Masking flow lines inside the pile
                # We draw a "white" (or background color) rectangle slightly smaller than pile to cover lines
                # But zorder=10 on the pile rect above already covers them!
                # The issue before was math. arcsinh wraps correctly.
                ax.text(pile_x, -pile_depth/2, "PILE", rotation=90, color='white', ha='center', va='center', fontsize=8, zorder=11)

            # --- 5. WATER ---
            ax.add_patch(patches.Rectangle((-10, 0), 10, h_up, facecolor='#D6EAF8', alpha=0.5, zorder=1))
            ax.plot([-10, 0], [h_up, h_up], 'b-', lw=2)
            ax.add_patch(patches.Rectangle((0, 0), 10, h_down, facecolor='#D6EAF8', alpha=0.5, zorder=1))
            ax.plot([0, 10], [h_down, h_down], 'b-', lw=2)

            # --- 6. POINT ---
            ax.scatter(x_point, y_point, c='red', marker='X', s=120, zorder=20, edgecolors='black')
            ax.text(x_point+0.4, y_point, f"n_d={nd_point}", color='red', fontweight='bold', zorder=20, bbox=dict(facecolor='white', alpha=0.8, pad=1, edgecolor='none'))

            # Legend
            ax.plot([], [], 'b-', label='Flow Line')
            ax.plot([], [], 'r--', label='Equipotential')
            ax.legend(loc='lower center', ncol=2, fontsize=8)
            ax.axis('off')
            st.pyplot(fig)

if __name__ == "__main__":
    app()
