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

def app():
    st.markdown("---")
    st.subheader("Flow of Water & Seepage Analysis")

    tab1, tab2, tab3 = st.tabs(["1D Seepage (Effective Stress)", "Permeability Tests", "2D Flow Net Analysis"])

    # =================================================================
    # TAB 1: 1D SEEPAGE (Effective Stress) - FULLY RESTORED
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
            datum_y, soil_w, soil_x = 0.0, 2.5, 3.5
            wl_top = val_z + val_y  
            wl_bot = val_x          
            
            # Flow Arrow Logic
            if wl_top > wl_bot: flow_arrow = "⬇️"
            elif wl_bot > wl_top: flow_arrow = "⬆️"
            else: flow_arrow = "No Flow"

            # 1. Soil Fill
            ax.add_patch(patches.Rectangle((soil_x, datum_y), soil_w, val_z, facecolor='#E3C195', hatch='...', edgecolor='none'))
            ax.text(soil_x + soil_w/2, datum_y + val_z/2, "SOIL", ha='center', fontweight='bold', fontsize=12)
            
            # 2. Water & Tanks
            tank_w = 2.0
            tank_x = soil_x + (soil_w - tank_w)/2
            neck_w = 0.8
            neck_x = soil_x + (soil_w - neck_w)/2
            tank_base_y = max(datum_y + val_z, wl_top - 0.5)
            
            ax.add_patch(patches.Rectangle((tank_x, tank_base_y), tank_w, wl_top - tank_base_y, facecolor='#D6EAF8', edgecolor='black'))
            ax.add_patch(patches.Rectangle((neck_x, datum_y + val_z), neck_w, tank_base_y - (datum_y + val_z) + 0.1, facecolor='#D6EAF8', edgecolor='none'))
            
            # Draw Walls
            ax.plot([soil_x, soil_x], [datum_y, datum_y+val_z], 'k-', lw=2.5)
            ax.plot([soil_x+soil_w, soil_x+soil_w], [datum_y, datum_y+val_z], 'k-', lw=2.5)
            ax.plot([tank_x, tank_x], [tank_base_y, wl_top+0.5], 'k-', lw=2.5)
            ax.plot([tank_x+tank_w, tank_x+tank_w], [tank_base_y, wl_top+0.5], 'k-', lw=2.5)

            # Water Levels
            ax.plot([tank_x, tank_x+tank_w], [wl_top, wl_top], 'b-', lw=2)
            ax.plot(tank_x+tank_w/2, wl_top, marker='v', color='blue')

            # Dimensions
            ax.plot([-0.5, 8], [0, 0], 'k-.') # Datum
            ax.text(7, -0.2, "Datum (z=0)", fontsize=9)
            
            ax.annotate('', xy=(soil_x-0.4, 0), xytext=(soil_x-0.4, val_z), arrowprops=dict(arrowstyle='<->', color='black'))
            ax.text(soil_x-0.6, val_z/2, f"z={val_z}m", ha='right')

            # Point A
            ax.scatter(soil_x + soil_w/2, val_A, c='black', zorder=5, s=80)
            ax.text(soil_x + soil_w/2 + 0.2, val_A, "Point A", fontweight='bold')
            ax.text(soil_x + soil_w/2, wl_top + 0.5, f"FLOW {flow_arrow}", ha='center', fontsize=12, fontweight='bold')

            ax.set_xlim(0, 8); ax.set_ylim(-1, wl_top+1); ax.axis('off')
            st.pyplot(fig)


    # =================================================================
    # TAB 2: PERMEABILITY (Lab Tests) - FULLY RESTORED
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
                        st.markdown(f"""<div style="background-color: #d1e7dd; padding: 20px; border-radius: 10px; border: 1px solid #0f5132; text-align: center; margin-top: 20px;"><p style="color: #0f5132; margin-bottom: 8px; font-size: 16px; font-weight: 600;">Permeability Coefficient (k)</p><h2 style="color: #0f5132; margin: 0; font-size: 28px; font-weight: 800;">$${k_formatted} \\text{{ cm/sec}}$$</h2></div>""", unsafe_allow_html=True)
                    else: st.error("Inputs must be positive.")

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
                        st.markdown(f"""<div style="background-color: #d1e7dd; padding: 20px; border-radius: 10px; border: 1px solid #0f5132; text-align: center; margin-top: 20px;"><p style="color: #0f5132; margin-bottom: 8px; font-size: 16px; font-weight: 600;">Permeability Coefficient (k)</p><h2 style="color: #0f5132; margin: 0; font-size: 28px; font-weight: 800;">$${k_formatted} \\text{{ cm/sec}}$$</h2></div>""", unsafe_allow_html=True)
                    else: st.error("Inputs invalid.")

        with col_plot_2:
            fig2, ax2 = plt.subplots(figsize=(6, 8))
            ax2.set_xlim(0, 10); ax2.set_ylim(0, 10); ax2.axis('off')
            soil_color, water_color, wall_color = '#E3C195', '#D6EAF8', 'black'

            if "Constant" in test_type:
                # Constant Head Diagram
                ax2.add_patch(patches.Rectangle((2, 8), 4, 1.5, facecolor=water_color, edgecolor=wall_color)) # Supply
                ax2.plot([2, 6], [9, 9], 'b-', lw=2); ax2.plot(4, 9, marker='v', color='blue')
                
                ax2.add_patch(patches.Rectangle((3.8, 6), 0.4, 2, facecolor=water_color, edgecolor='none')) # Pipe
                ax2.plot([3.8, 3.8], [6, 8], 'k-'); ax2.plot([4.2, 4.2], [6, 8], 'k-')

                ax2.add_patch(patches.Rectangle((3, 4), 2, 2, facecolor=soil_color, hatch='X', edgecolor=wall_color, lw=2)) # Soil
                ax2.text(4, 5, "SOIL\nArea A", ha='center', va='center', fontweight='bold')
                
                ax2.add_patch(patches.Rectangle((3.8, 2.5), 0.4, 1.5, facecolor=water_color, edgecolor='none')) # Bottom Pipe
                ax2.plot([3.8, 3.8], [2.5, 4], 'k-'); ax2.plot([4.2, 4.2], [2.5, 4], 'k-')
                
                ax2.add_patch(patches.Rectangle((3.5, 1), 3, 1.5, facecolor=water_color, edgecolor=wall_color)) # Collection
                ax2.plot([3.5, 6.5], [2.2, 2.2], 'b-', lw=2); ax2.plot(6, 2.2, marker='v', color='blue')

                ax2.annotate('', xy=(8, 2.2), xytext=(8, 9), arrowprops=dict(arrowstyle='<->', lw=1.5))
                ax2.text(8.2, 5.5, "h (Diff)", ha='left', fontweight='bold', color='blue')
                ax2.plot([6, 8.2], [9, 9], 'k--', lw=0.5); ax2.plot([6.5, 8.2], [2.2, 2.2], 'k--', lw=0.5)

                ax2.annotate('', xy=(1.5, 4), xytext=(1.5, 6), arrowprops=dict(arrowstyle='<->', lw=1.5))
                ax2.text(1.2, 5, "L", ha='right', fontweight='bold')
                ax2.plot([1.5, 3], [4, 4], 'k--', lw=0.5); ax2.plot([1.5, 3], [6, 6], 'k--', lw=0.5)

            else:
                # Falling Head Diagram
                ax2.add_patch(patches.Rectangle((3.8, 6), 0.4, 3.5, facecolor=water_color, edgecolor=wall_color)) # Standpipe
                ax2.text(3.5, 8, "Standpipe\n(Area a)", ha='right')
                
                ax2.add_patch(patches.Rectangle((3, 4), 2, 2, facecolor=soil_color, hatch='X', edgecolor=wall_color, lw=2)) # Soil
                ax2.text(4, 5, "SOIL\nArea A", ha='center', va='center', fontweight='bold')
                
                ax2.add_patch(patches.Rectangle((3.8, 2), 0.4, 2, facecolor=water_color, edgecolor='none')) # Pipe
                ax2.plot([3.8, 3.8], [2, 4], 'k-'); ax2.plot([4.2, 4.2], [2, 4], 'k-')
                
                ax2.add_patch(patches.Rectangle((3.5, 1), 3, 1.5, facecolor=water_color, edgecolor=wall_color)) # Bottom Tank
                ax2.plot([3.5, 6.5], [2, 2], 'b-', lw=2); ax2.plot(6, 2, marker='v', color='blue')

                ax2.plot([3.8, 4.2], [9, 9], 'r-', lw=2); ax2.text(4.4, 9, "Start (h1)", fontsize=8, color='red')
                ax2.plot([3.8, 4.2], [7, 7], 'r-', lw=2); ax2.text(4.4, 7, "End (h2)", fontsize=8, color='red')

                ax2.annotate('', xy=(8, 2), xytext=(8, 9), arrowprops=dict(arrowstyle='<->', color='red'))
                ax2.text(8.2, 9, "h1", ha='left', fontweight='bold', color='red')
                ax2.annotate('', xy=(7, 2), xytext=(7, 7), arrowprops=dict(arrowstyle='<->', color='red'))
                ax2.text(7.2, 7, "h2", ha='left', fontweight='bold', color='red')
                ax2.plot([6.5, 8.2], [2, 2], 'b--', lw=0.5)

                ax2.annotate('', xy=(1.5, 4), xytext=(1.5, 6), arrowprops=dict(arrowstyle='<->', lw=1.5))
                ax2.text(1.2, 5, "L", ha='right', fontweight='bold')
                ax2.plot([1.5, 3], [4, 4], 'k--', lw=0.5); ax2.plot([1.5, 3], [6, 6], 'k--', lw=0.5)

            st.pyplot(fig2)

    # =================================================================
    # TAB 3: 2D FLOW NET ANALYSIS (Advanced Conformal Mapping)
    # =================================================================
    with tab3:
        st.markdown("### Graphical Solution (Flow Net)")
        st.caption("Visualizes flow using exact mathematical conformal mapping to ensure orthogonality.")
        
        col_input, col_plot = st.columns([1, 1.5])

        with col_input:
            st.markdown("#### 1. Geometry & Head")
            struct_type = st.radio("Structure", ["Concrete Dam", "Sheet Pile"], horizontal=True)
            
            if struct_type == "Concrete Dam":
                dim_width = st.number_input("Dam Base Width (B) [m]", value=10.0, step=1.0)
                dim_depth = 0 
            else:
                dim_width = 0 
                dim_depth = st.number_input("Pile Embedment Depth (D) [m]", value=5.0, step=0.5)

            c_h1, c_h2 = st.columns(2)
            h_up = c_h1.number_input("Upstream H [m]", value=10.0)
            h_down = c_h2.number_input("Downstream H [m]", value=2.0)
            H_net = h_up - h_down

            st.markdown("#### 2. Flow Net Density")
            Nf = st.number_input("Flow Channels (Nf)", value=4, min_value=2, max_value=10)
            Nd = st.number_input("Potential Drops (Nd)", value=10, min_value=4, max_value=20)
            
            st.markdown("#### 3. Soil")
            k_val = st.number_input("Permeability (k) [m/day]", value=0.0864, format="%.4f")

            if st.button("Calculate Flow (q)", type="primary"):
                q = k_val * H_net * (Nf / Nd)
                st.markdown(f"""
                <div style="border: 2px solid #198754; background-color: #d1e7dd; padding: 15px; border-radius: 8px; text-align: center;">
                    <h3 style="color: #198754; margin:0;">q = {q:.4f} m³/day/m</h3>
                    <p style="margin:0; font-size: 14px;">Shape Factor (Nf/Nd) = {Nf/Nd:.2f}</p>
                </div>
                """, unsafe_allow_html=True)

        with col_plot:
            fig, ax = plt.subplots(figsize=(8, 6))
            
            # --- MATHEMATICAL CONFORMAL MAPPING ---
            gx = np.linspace(-15, 15, 200)
            gy = np.linspace(-15, 0, 150) # Soil domain only (y < 0)
            X, Y = np.meshgrid(gx, gy)
            Z = X + 1j * Y
            
            if struct_type == "Concrete Dam":
                # Z = C * cosh(W) -> W = arccosh(Z/C)
                C = dim_width / 2.0
                with np.errstate(invalid='ignore', divide='ignore'):
                    W = np.arccosh(Z / C)
                Phi, Psi = np.real(W), np.imag(W)
                
                # Draw Dam
                ax.add_patch(patches.Rectangle((-C, 0), 2*C, h_up+2, facecolor='gray', edgecolor='black', zorder=3))
                ax.text(0, 1, "DAM", ha='center', fontweight='bold', color='white')
                
                levels_psi = np.linspace(0, np.pi, Nf + 1)
                levels_phi = np.linspace(np.nanmin(Phi), np.nanmax(Phi), Nd + 2)

            else: # Sheet Pile
                # Parabolic Coordinates: Z_shifted = Z + iD -> W = -i * sqrt(Z_shifted)
                D = dim_depth
                Z_shift = Z + 1j*D 
                with np.errstate(invalid='ignore'):
                    W = -1j * np.sqrt(Z_shift)
                Phi, Psi = np.real(W), np.imag(W)
                
                # Draw Pile
                ax.add_patch(patches.Rectangle((-0.2, -D), 0.4, D + h_up, facecolor='gray', edgecolor='black', zorder=3))
                
                levels_psi = np.linspace(np.nanmin(Psi), np.nanmax(Psi), Nf + 2)
                levels_phi = np.linspace(np.nanmin(Phi), np.nanmax(Phi), Nd + 2)

            # Plot Contours (Orthogonal Grid)
            ax.contour(X, Y, Psi, levels=levels_psi, colors='blue', linewidths=1.5, linestyles='solid', alpha=0.7)
            ax.contour(X, Y, Phi, levels=levels_phi, colors='red', linewidths=1.5, linestyles='dashed', alpha=0.7)

            # Water & Soil
            ax.add_patch(patches.Rectangle((-15, 0), 15, h_up, facecolor='#D6EAF8', alpha=0.5))
            ax.plot([-15, 0], [h_up, h_up], 'b-', lw=2)
            ax.add_patch(patches.Rectangle((0, 0), 15, h_down, facecolor='#D6EAF8', alpha=0.5))
            ax.plot([0, 15], [h_down, h_down], 'b-', lw=2)
            ax.plot([-15, 15], [0, 0], 'k-', lw=2) # Ground

            ax.set_ylim(-12, max(h_up, h_down)+2)
            ax.set_xlim(-12, 12)
            ax.set_aspect('equal'); ax.axis('off')
            
            # Legend
            ax.plot([], [], 'b-', label='Flow Line (Streamline)')
            ax.plot([], [], 'r--', label='Equipotential Line')
            ax.legend(loc='lower center', ncol=2, fontsize=8)

            st.pyplot(fig)

if __name__ == "__main__":
    app()
