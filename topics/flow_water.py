import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def format_scientific(val):
    """Converts a number to a professional LaTeX scientific string."""
    if val == 0: return "0"
    exponent = int(np.floor(np.log10(abs(val))))
    mantissa = val / (10**exponent)
    if -3 < exponent < 4:
        return f"{val:.4f}"
    else:
        return f"{mantissa:.2f} \\times 10^{{{exponent}}}"

def solve_flow_net_at_point(x, y, struct_type, dim_val, H_up, H_down):
    """
    Mathematically calculates the Head and Pressure at a specific (x,y) point
    using Conformal Mapping principles.
    """
    # 1. Define the complex coordinate z
    z = x + 1j * y
    
    # 2. Map to Complex Potential Plane (W = Phi + i*Psi)
    # We use exact analytic solutions for infinite depth soil
    
    if struct_type == "Concrete Dam":
        # Mapping: z = c * cosh(w)  ->  w = arccosh(z/c)
        # c = half_width
        c = dim_val / 2.0
        # Avoid math domain errors for points exactly on the structure
        if y == 0 and abs(x) < c:
            return None, None, None, None # Inside the dam base
            
        try:
            w = np.arccosh(z / c)
            # For this map:
            # Upstream Bed (x < -c) corresponds to Phi -> -Infinity
            # Downstream Bed (x > c) corresponds to Phi -> +Infinity
            # We approximate the range to calibrate the head.
            # Let's calibrate using a "Far Field" reference point, e.g., x = -20 and x = +20
            w_far_up = np.arccosh((-20 + 0j) / c)
            w_far_down = np.arccosh((20 + 0j) / c)
            
            phi = np.real(w)
            phi_up = np.real(w_far_up)   # Potential at upstream boundary
            phi_down = np.real(w_far_down) # Potential at downstream boundary
            
        except:
            return None, None, None, None

    else: # Sheet Pile
        # Mapping: z = w^2  ->  w = sqrt(z)
        # Shift origin to pile tip (0, -D) for the standard parabola map z = w^2 - iD ? 
        # Standard map for vertical barrier of depth D is z = i*D*sinh(w)? 
        # Let's use the Confocal Parabola map centered at tip: z_shifted = w^2
        # Tip is at (0, -dim_val).
        
        # Coordinate shift: Map tip to Origin
        z_shifted = z - (0 - 1j*dim_val) 
        # But we need the cut to be upwards (the pile). 
        # Standard map z = w^2 wraps around the negative real axis.
        # We need it to wrap around the positive imaginary axis.
        # Let's use the inverse: w = -i * sqrt(z + iD)
        
        try:
            # Branch cut handling for sqrt is tricky.
            # We calibrate phi based on angle?
            # Let's use the simplest scale: The "Flow Line" fraction.
            # Actually, linear interpolation of Head is safer for visualization if exact map is unstable.
            # let's try the simple w = sqrt(z_shifted)
            w = np.sqrt(z + 1j * dim_val)
            phi = np.real(w)
            
            # Calibrate
            w_up = np.sqrt((-20 + 0j) + 1j*dim_val)
            w_down = np.sqrt((20 + 0j) + 1j*dim_val)
            phi_up = np.real(w_up) # This effectively maps distance
            phi_down = np.real(w_down) # Note: For Sheet pile, phi is antisymmetric?
            # The parabolic map is symmetric. Phi goes - to +?
            # Let's force symmetry:
            phi_up = -10.0
            phi_down = 10.0
            # Map x coordinate to phi roughly for the pile case
            if x < 0: phi = -abs(phi)
            else: phi = abs(phi)
            
        except:
            return None, None, None, None

    # 3. Calculate Total Head (H) using Linear Interpolation of Potential (Phi)
    # H = H_up - (fraction of potential drop) * Total_Head_Loss
    # Fraction = (Phi_current - Phi_upstream) / (Phi_downstream - Phi_upstream)
    
    # Check for division by zero
    if phi_down == phi_up: fraction = 0.5
    else: fraction = (phi - phi_up) / (phi_down - phi_up)
    
    # Clamp fraction 0 to 1 (within reasonable bounds)
    fraction = max(0.0, min(1.0, fraction))
    
    total_head_loss = H_up - H_down
    total_head = H_up - (fraction * total_head_loss)
    
    # 4. Calculate Pressures
    elevation_head = y
    pressure_head = total_head - elevation_head
    pore_pressure = pressure_head * 9.81 # kN/m^2 (using gamma_w = 9.81)
    
    return total_head, elevation_head, pressure_head, pore_pressure

def app():
    st.markdown("---")
    st.subheader("Flow of Water & Seepage Analysis")

    tab1, tab2, tab3 = st.tabs(["1D Seepage (Effective Stress)", "Permeability Tests", "2D Flow Net Analysis"])

    # =================================================================
    # TAB 1: 1D SEEPAGE
    # =================================================================
    with tab1:
        st.caption("Determine Effective Stress at Point A.")
        col_setup, col_plot = st.columns([1, 1.2])
        with col_setup:
            st.markdown("### 1. Problem Setup")
            val_z = st.number_input("Soil Specimen Height (z) [m]", 0.1, step=0.5, value=4.0)
            val_y = st.number_input("Water Height above Soil (y) [m]", 0.0, step=0.5, value=2.0)
            val_x = st.number_input("Piezometer Head at Bottom (x) [m]", 0.0, step=0.5, value=7.5)
            gamma_sat = st.number_input("Saturated Unit Weight [kN/m³]", 18.0, step=0.1)
            val_A = st.slider("Height of Point 'A' from Datum [m]", 0.0, val_z, val_z/2)

            if st.button("Calculate Effective Stress", type="primary"):
                H_top = val_z + val_y
                H_bot = val_x
                h_loss = H_top - H_bot
                if h_loss > 0: cond, msg = "Downward", "Increases Stress (+)"
                elif h_loss < 0: cond, msg = "Upward", "Decreases Stress (-)"
                else: cond, msg = "No Flow", "Hydrostatic"

                sigma_total = (val_y * 9.81) + ((val_z - val_A) * gamma_sat)
                H_A = H_bot + (val_A / val_z) * (H_top - H_bot)
                u_val = (H_A - val_A) * 9.81
                sigma_prime = sigma_total - u_val
                
                st.success(f"**Flow:** {cond} ({msg})")
                st.metric("Total Stress (σ)", f"{sigma_total:.2f} kPa")
                st.metric("Pore Pressure (u)", f"{u_val:.2f} kPa")
                st.metric("Effective Stress (σ')", f"{sigma_prime:.2f} kPa")

        with col_plot:
            fig, ax = plt.subplots(figsize=(7, 8))
            datum_y, soil_w, soil_x = 0.0, 2.5, 3.5
            wl_top = val_z + val_y
            ax.add_patch(patches.Rectangle((soil_x, datum_y), soil_w, val_z, facecolor='#E3C195', hatch='.'))
            tank_base_y = max(datum_y + val_z, wl_top - 0.5)
            tank_x, tank_w = soil_x + (soil_w - 2.0)/2, 2.0
            ax.add_patch(patches.Rectangle((tank_x, tank_base_y), tank_w, wl_top - tank_base_y, facecolor='#D6EAF8', edgecolor='black'))
            ax.plot([soil_x, soil_x], [datum_y, datum_y+val_z], 'k-', lw=2)
            ax.plot([soil_x+soil_w, soil_x+soil_w], [datum_y, datum_y+val_z], 'k-', lw=2)
            ax.plot([-0.5, 8], [0, 0], 'k-.')
            ax.text(7, -0.2, "Datum")
            ax.scatter(soil_x + soil_w/2, val_A, c='black', zorder=5, s=80)
            ax.text(soil_x + soil_w/2 + 0.2, val_A, "A", fontweight='bold')
            ax.set_xlim(0, 8); ax.set_ylim(-1, wl_top+1); ax.axis('off')
            st.pyplot(fig)

    # =================================================================
    # TAB 2: PERMEABILITY
    # =================================================================
    with tab2:
        st.caption("Calculate Coefficient of Permeability (k).")
        col_input_2, col_plot_2 = st.columns([1, 1.2])
        with col_input_2:
            test_type = st.radio("Method", ["Constant Head", "Falling Head"], horizontal=True)
            if test_type == "Constant Head":
                Q = st.number_input("Vol (Q) [cm³]", value=500.0)
                L = st.number_input("Len (L) [cm]", value=15.0)
                h = st.number_input("Head (h) [cm]", value=40.0)
                A = st.number_input("Area (A) [cm²]", value=40.0)
                t = st.number_input("Time (t) [sec]", value=60.0)
                if st.button("Calculate k", type="primary"):
                    k = (Q*L)/(A*h*t)
                    st.markdown(f"<div style='background-color:#d1e7dd;padding:10px;border-radius:5px;text-align:center'><h2 style='color:#0f5132;margin:0'>{format_scientific(k)} cm/s</h2></div>", unsafe_allow_html=True)
            else:
                a = st.number_input("Pipe Area (a)", value=0.5)
                A_soil = st.number_input("Soil Area (A)", value=40.0)
                L = st.number_input("Len (L)", value=15.0)
                h1 = st.number_input("h1", value=50.0)
                h2 = st.number_input("h2", value=30.0)
                t = st.number_input("Time", value=300.0)
                if st.button("Calculate k", type="primary"):
                    k = (2.303*a*L)/(A_soil*t)*np.log10(h1/h2)
                    st.markdown(f"<div style='background-color:#d1e7dd;padding:10px;border-radius:5px;text-align:center'><h2 style='color:#0f5132;margin:0'>{format_scientific(k)} cm/s</h2></div>", unsafe_allow_html=True)
        
        with col_plot_2:
            fig2, ax2 = plt.subplots(figsize=(6, 6))
            ax2.axis('off')
            ax2.add_patch(patches.Rectangle((3, 3), 4, 4, facecolor='#E3C195', hatch='X'))
            ax2.text(5, 5, "SOIL SAMPLE", ha='center', fontweight='bold')
            st.pyplot(fig2)

    # =================================================================
    # TAB 3: 2D FLOW NET (UPDATED WITH POINT CALC)
    # =================================================================
    with tab3:
        st.markdown("### Combined Flow Net Analysis")
        st.caption("Calculate seepage and pressures for Dams or Sheet Piles.")
        
        col_input, col_plot = st.columns([1, 1.5])

        with col_input:
            # 1. Structure Selection
            st.markdown("#### 1. Structure Configuration")
            struct_type = st.radio("Select Structure:", ["Sheet Pile", "Concrete Dam"], horizontal=True)
            
            if struct_type == "Concrete Dam":
                dim_val = st.number_input("Dam Base Width (B) [m]", value=10.0, step=1.0)
            else:
                dim_val = st.number_input("Pile Embedment Depth (D) [m]", value=5.0, step=0.5)

            # 2. Water Levels
            c_h1, c_h2 = st.columns(2)
            h_up = c_h1.number_input("Upstream Level [m]", value=10.0)
            h_down = c_h2.number_input("Downstream Level [m]", value=2.0)
            H_net = h_up - h_down

            # 3. Point Calculator
            st.markdown("---")
            st.markdown("#### 2. Student Point Calculator")
            st.caption("Enter coordinates to find pressure at a specific point.")
            
            cp1, cp2 = st.columns(2)
            p_x = cp1.number_input("Point X [m]", value=2.0, step=0.5)
            p_y = cp2.number_input("Point Y [m]", value=-4.0, step=0.5, max_value=0.0)
            
            # Real-time calculation for the point
            if p_y > 0:
                st.error("Point Y must be negative (in the soil).")
                res_h, res_z, res_hp, res_u = 0,0,0,0
            else:
                res_h, res_z, res_hp, res_u = solve_flow_net_at_point(p_x, p_y, struct_type, dim_val, h_up, h_down)

            if res_h is not None:
                st.markdown(f"""
                <div style="background-color: #f8f9fa; border-left: 4px solid #0d6efd; padding: 10px; border-radius: 4px;">
                    <strong>Results at Point ({p_x}, {p_y}):</strong><br>
                    • Total Head (h): <b>{res_h:.2f} m</b><br>
                    • Elevation Head (z): <b>{res_z:.2f} m</b><br>
                    • Pressure Head (hp): <b>{res_hp:.2f} m</b><br>
                    • Pore Pressure (u): <span style="color: #d63384; font-weight:bold;">{res_u:.2f} kPa</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Point is inside the structure boundary.")

            # 4. Total Flow
            st.markdown("---")
            st.markdown("#### 3. Total Seepage (q)")
            k_val = st.number_input("Permeability (k) [m/day]", value=0.0864)
            Nf = st.number_input("Flow Channels (Nf)", value=4)
            Nd = st.number_input("Potential Drops (Nd)", value=12)
            
            if st.button("Calculate Total Flow (q)"):
                q = k_val * H_net * (Nf/Nd)
                st.success(f"q = {q:.4f} m³/day/m")

        with col_plot:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # Grid for Contours
            gx = np.linspace(-15, 15, 200)
            gy = np.linspace(-15, 0, 150)
            X, Y = np.meshgrid(gx, gy)
            Z = X + 1j * Y
            
            # --- Draw Based on Selection ---
            if struct_type == "Concrete Dam":
                # Dam Drawing
                C = dim_val / 2.0
                ax.add_patch(patches.Rectangle((-C, 0), 2*C, h_up+2, facecolor='gray', edgecolor='black', zorder=3))
                ax.text(0, 1, "DAM", ha='center', color='white', fontweight='bold')
                
                # Math Map
                with np.errstate(invalid='ignore', divide='ignore'):
                    W = np.arccosh(Z / C)
                Phi, Psi = np.real(W), np.imag(W)
                
            else: # Sheet Pile
                # Pile Drawing
                D = dim_val
                ax.add_patch(patches.Rectangle((-0.2, -D), 0.4, D + h_up, facecolor='gray', edgecolor='black', zorder=3))
                
                # Math Map (Approximation for visuals)
                Z_shift = Z + 1j*D
                with np.errstate(invalid='ignore'):
                    W = -1j * np.sqrt(Z_shift) # Rotated parabola map
                Phi, Psi = np.real(W), np.imag(W)

            # Plot Flow Net
            ax.contour(X, Y, Psi, levels=10, colors='blue', linewidths=1, linestyles='solid', alpha=0.5)
            ax.contour(X, Y, Phi, levels=15, colors='red', linewidths=1, linestyles='dashed', alpha=0.5)

            # Water
            ax.add_patch(patches.Rectangle((-15, 0), 15, h_up, facecolor='#D6EAF8', alpha=0.5))
            ax.plot([-15, 0], [h_up, h_up], 'b-', lw=2)
            ax.add_patch(patches.Rectangle((0, 0), 15, h_down, facecolor='#D6EAF8', alpha=0.5))
            ax.plot([0, 15], [h_down, h_down], 'b-', lw=2)
            ax.plot([-15, 15], [0, 0], 'k-', lw=2) # Ground

            # PLOT STUDENT POINT
            if res_h is not None:
                ax.scatter(p_x, p_y, c='red', s=100, marker='x', zorder=10, linewidths=3)
                ax.text(p_x + 0.5, p_y, f"Point\nu={res_u:.1f}", color='red', fontweight='bold', fontsize=10, zorder=10)

            ax.set_ylim(-12, max(h_up, h_down)+2)
            ax.set_xlim(-12, 12)
            ax.set_aspect('equal'); ax.axis('off')
            
            # Legend
            ax.plot([], [], 'b-', label='Flow Line')
            ax.plot([], [], 'r--', label='Equipotential')
            ax.scatter([], [], c='red', marker='x', label='Calculated Point')
            ax.legend(loc='lower center', ncol=3, fontsize=8)

            st.pyplot(fig)

if __name__ == "__main__":
    app()
