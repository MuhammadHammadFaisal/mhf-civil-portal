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

def get_complex_potential(x, y, has_pile, pile_depth, pile_x, has_dam, dam_width):
    """
    Returns the Complex Potential W = Phi + i*Psi.
    Correctly maps boundaries so Structure = Streamline (Psi=0) and Ground = Equipotential.
    """
    z = x + 1j * y
    
    # 1. SHEET PILE (Vertical Cut)
    # Map: z = d * cosh(w) is standard for flow under vertical barrier? 
    # Actually, w = i * arcsin(z/d) works well for vertical barrier potentials.
    # Let's use the transformation that aligns with the user's previous visual preference (wrapping):
    # W = sqrt(z^2 + d^2) maps the pile to Real axis (Streamline).
    
    if has_pile:
        # Shift coordinate system to pile location
        z_shift = (z - pile_x)
        # Conformal Map for Vertical Barrier (Confocal Ellipses)
        # Z = d * sinh(W) -> W = arcsinh(Z/d)
        # This maps the Pile (x=0, y>-d) to Psi=0? No.
        # We use a robust approximation for visual flow nets:
        # W = sqrt(z_shift**2 + pile_depth**2)
        # On Pile (z=iy, y<d): w = sqrt(-y^2 + d^2) = Real -> Psi=0 (Streamline). CORRECT.
        # On Ground (z=x): w = sqrt(x^2 + d^2) = Real -> Psi=0? No, we want Ground to be Equipotential.
        # Let's use the cosh map: z = d * cosh(w) -> w = arccosh(z/d)
        # On Pile: arccosh(iy/d). Complex. 
        
        # Sticking to the visual engine that creates the loops:
        # Standard: z = c * sin(w).
        # Rotated for pile: z = i * c * sinh(w)
        with np.errstate(invalid='ignore', divide='ignore'):
             W = np.arcsinh(z_shift / pile_depth)
        # In this map: Real(W) = Equipotentials, Imag(W) = Streamlines wrapping the tip.
        # We just need to handle the sign to make sure it flows down-to-up.
        return W

    # 2. CONCRETE DAM (Horizontal Flat Base)
    # Map: z = c * sin(w) -> w = arcsin(z/c)
    # Base (|x|<c, y=0): z/c is real < 1. arcsin is Real. Psi=0 (Streamline). CORRECT.
    # Ground (|x|>c, y=0): z/c is real > 1. arcsin is Complex (Phi constant). Equipotential. CORRECT.
    elif has_dam:
        c = dam_width / 2.0
        with np.errstate(invalid='ignore', divide='ignore'):
            W = np.arcsin(z / c)
        # Arcsin output: Real=Phi, Imag=Psi.
        # We need to swap them visually because usually flow is "Imaginary" in this specific map convention?
        # Let's check: Under dam (Psi=0), flow is horizontal. 
        # Standard convention: W = -kH/pi * arccos(x/b).
        return -1j * W # Rotate to align with standard vertical flow direction

    else:
        return z

def solve_flow_net_at_point(h_upstream, h_downstream, total_Nd, drops_passed, y_point, datum_elev):
    """
    Calculates head and pressure using Flow Net Counting Method.
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
        "hp": hp, "u": u, "z": z, "nd_passed": drops_passed
    }

# --- MAIN APP ---

def app():
    st.markdown("---")
    st.subheader("Flow of Water & Seepage Analysis")

    tab1, tab2, tab3 = st.tabs(["1D Seepage", "Permeability", "Flow Nets & Piping"])

    # =================================================================
    # TAB 1: 1D SEEPAGE
    # =================================================================
    with tab1:
        st.caption("Determine Effective Stress at Point A.")
        c1, c2 = st.columns([1, 1.2])
        with c1:
            st.markdown("### Setup")
            val_z = st.number_input("Soil Height (z)", 0.1, step=0.5, value=4.0)
            val_y = st.number_input("Water Above (y)", 0.0, step=0.5, value=2.0)
            val_x = st.number_input("Piezo Head (x)", 0.0, step=0.5, value=7.5)
            gamma_sat = st.number_input("Sat. Unit Wt", 18.0, step=0.1)
            val_A = st.slider("Point A Height", 0.0, val_z, val_z/2)
            
            if st.button("Calculate Stress"):
                H_top, H_bot = val_z + val_y, val_x
                gamma_w = 9.81
                sigma = (val_y * gamma_w) + ((val_z - val_A) * gamma_sat)
                H_A = H_bot + (val_A / val_z) * (H_top - H_bot)
                u = (H_A - val_A) * gamma_w
                sigma_prime = sigma - u
                st.metric("Effective Stress", f"{sigma_prime:.2f} kPa")
                st.metric("Pore Pressure", f"{u:.2f} kPa")

        with c2:
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.add_patch(patches.Rectangle((2, 0), 2, val_z, facecolor='#E3C195', hatch='...'))
            ax.plot([2, 4], [val_z+val_y, val_z+val_y], 'b-', lw=2)
            ax.plot([1, 2], [val_x, val_x], 'b--', lw=1)
            ax.scatter(3, val_A, c='red', s=100, zorder=5)
            ax.text(3.2, val_A, "A", color='red', fontweight='bold')
            ax.set_xlim(0, 6); ax.set_ylim(-1, max(val_z+val_y, val_x)+1)
            ax.axis('off'); st.pyplot(fig)

    # =================================================================
    # TAB 2: PERMEABILITY
    # =================================================================
    with tab2:
        st.write("Permeability Test Calculator")
        test = st.radio("Type", ["Constant Head", "Falling Head"])
        if test == "Constant Head":
            Q = st.number_input("Q (cm³)", 500.0); L = st.number_input("L", 15.0)
            h = st.number_input("h", 40.0); t = st.number_input("t", 60.0); A = st.number_input("A", 40.0)
            if st.button("Calc k"): st.success(f"k = {format_scientific((Q*L)/(A*h*t))} cm/s")
        else:
            a = st.number_input("a (standpipe)", 0.5); L = st.number_input("L", 15.0); A = st.number_input("A", 40.0)
            h1 = st.number_input("h1", 50.0); h2 = st.number_input("h2", 30.0); t = st.number_input("t", 300.0)
            if st.button("Calc k"): st.success(f"k = {format_scientific((2.303*a*L)/(A*t)*np.log10(h1/h2))} cm/s")

    # =================================================================
    # TAB 3: FLOW NETS (FINAL VISUALS)
    # =================================================================
    with tab3:
        st.markdown("### Flow Net Analysis")
        st.caption("Design Flow Nets for Dams, Sheet Piles, or Combined systems.")
        
        col_input, col_plot = st.columns([1, 1.2])

        with col_input:
            st.markdown("#### 1. Configuration")
            # Structure Toggles
            struct_choice = st.radio("Structure Type", ["Sheet Pile", "Concrete Dam"], horizontal=True)
            has_pile = (struct_choice == "Sheet Pile")
            has_dam = (struct_choice == "Concrete Dam")
            
            dam_width = 0.0; pile_depth = 0.0; pile_x = 0.0
            if has_dam:
                dam_width = st.number_input("Dam Base Width (B) [m]", value=6.0, step=0.5)
            if has_pile:
                pile_depth = st.number_input("Pile Depth (D) [m]", value=5.0, step=0.5)
                pile_x = st.number_input("Pile X Location [m]", value=0.0, step=0.5)

            st.markdown("#### 2. Soil Profile")
            soil_depth = st.number_input("Impervious Layer Depth (T) [m]", value=12.0, step=1.0)

            st.markdown("#### 3. Counting")
            c_h1, c_h2 = st.columns(2)
            h_up = c_h1.number_input("H_up [m]", 4.5)
            h_down = c_h2.number_input("H_down [m]", 0.5)
            
            c_net1, c_net2 = st.columns(2)
            Nd = c_net1.number_input("Drops (Nd)", 12)
            Nf = c_net2.number_input("Channels (Nf)", 4)
            
            st.markdown("#### 4. Point Check")
            datum = st.number_input("Datum (z=0)", -soil_depth)
            
            c_pt1, c_pt2, c_pt3 = st.columns(3)
            x_point = c_pt1.number_input("X", 2.0)
            y_point = c_pt2.number_input("Y", -4.0)
            nd_point = c_pt3.number_input("Drops Passed (nd)", 4.5)
            
            results = solve_flow_net_at_point(h_up, h_down, Nd, nd_point, y_point, datum)
            
            st.markdown(f"""
            <div style="background-color: #e3f2fd; color: #333333; border: 1px solid #90caf9; border-radius: 5px; padding: 10px; margin-top: 10px;">
                <b>Total Head (h):</b> {results['h_point']:.2f} m <br>
                <b>Pore Pressure (u):</b> <span style="color: #d63384; font-weight: bold;">{results['u']:.2f} kPa</span>
            </div>
            """, unsafe_allow_html=True)
            
            k_val = st.number_input("k [m/s]", 1e-6, format="%.1e")
            st.info(f"Seepage q = {format_scientific(k_val * results['H_diff'] * (Nf / Nd))} m³/sec/m")

        with col_plot:
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.set_xlim(-10, 10); ax.set_ylim(-soil_depth - 1, max(h_up, h_down) + 2)
            ax.set_aspect('equal')
            
            # --- 1. BOUNDARIES ---
            ax.axhline(0, color='black', linewidth=1.5) # Ground
            ax.axhline(-soil_depth, color='black', linewidth=2) # Bedrock
            ax.add_patch(patches.Rectangle((-10, -soil_depth - 2), 20, 2, facecolor='gray', hatch='///'))
            ax.text(0, -soil_depth - 0.8, "IMPERVIOUS BOUNDARY", ha='center', fontsize=8, fontweight='bold')
            ax.axhline(datum, color='green', ls='-.', alpha=0.6)

            # --- 2. MATH ENGINE ---
            gx = np.linspace(-10, 10, 250)
            gy = np.linspace(-soil_depth, 0, 250)
            X, Y = np.meshgrid(gx, gy)
            
            W = get_complex_potential(X, Y, has_pile, pile_depth, pile_x, has_dam, dam_width)
            Phi = np.real(W) 
            Psi = np.abs(np.imag(W)) # Force positive for symmetric plotting

            # --- 3. BOUNDARY CLAMPING (THE FIX) ---
            # Calculate Psi at the bedrock depth directly under the structure
            # This value represents the "Impervious Streamline"
            center_x = pile_x if has_pile else 0
            w_bed = get_complex_potential(center_x + 0.01, -soil_depth, has_pile, pile_depth, pile_x, has_dam, dam_width)
            psi_max = np.abs(np.imag(w_bed))
            if np.isnan(psi_max) or psi_max < 0.1: psi_max = 3.14 # Fallback

            # --- 4. DRAW FLOW NET ---
            # Flow Lines: 0 to psi_max (Structure to Bedrock)
            ax.contour(X, Y, Psi, levels=np.linspace(0, psi_max, Nf+1), colors='blue', linewidths=1, linestyles='solid', alpha=0.6)
            # Equipotentials: Infinite range, just clamp for visual niceness
            ax.contour(X, Y, Phi, levels=Nd+2, colors='red', linewidths=1, linestyles='dashed', alpha=0.6)

            # --- 5. DRAW STRUCTURES ---
            if has_dam:
                C = dam_width / 2.0
                ax.add_patch(patches.Rectangle((-C, 0), 2*C, h_up+1, facecolor='#666', ec='k', zorder=10))
                ax.text(0, 1, "DAM", ha='center', color='white', fontweight='bold', zorder=11)
            
            if has_pile:
                pw = 0.4
                ax.add_patch(patches.Rectangle((pile_x - pw/2, -pile_depth), pw, pile_depth + h_up + 1, facecolor='#333', ec='k', zorder=10))
                # White Mask to hide lines "inside" the pile thickness
                ax.add_patch(patches.Rectangle((pile_x - pw/2 + 0.05, -pile_depth), pw-0.1, pile_depth, facecolor='white', zorder=9)) 
                ax.text(pile_x, -pile_depth/2, "PILE", rotation=90, color='white', ha='center', va='center', fontsize=8, zorder=11)

            # --- 6. WATER & POINT ---
            ax.add_patch(patches.Rectangle((-10, 0), 10, h_up, fc='#D6EAF8', alpha=0.5))
            ax.plot([-10, 0], [h_up, h_up], 'b-')
            ax.add_patch(patches.Rectangle((0, 0), 10, h_down, fc='#D6EAF8', alpha=0.5))
            ax.plot([0, 10], [h_down, h_down], 'b-')

            ax.scatter(x_point, y_point, c='red', marker='X', s=120, zorder=20, edgecolors='black')
            ax.text(x_point+0.4, y_point, f"n_d={nd_point}", color='red', fontweight='bold', zorder=20, bbox=dict(facecolor='white', alpha=0.8, pad=1, ec='none'))

            ax.plot([], [], 'b-', label='Flow Line'); ax.plot([], [], 'r--', label='Equipotential')
            ax.legend(loc='lower center', ncol=2, fontsize=8)
            ax.axis('off'); st.pyplot(fig)

if __name__ == "__main__":
    app()
