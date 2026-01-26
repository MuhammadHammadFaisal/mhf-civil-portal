import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

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
                
                st.success(f"**Flow Condition:** {flow_type}\n\n*{effect_msg}*")
                st.metric("Total Stress (σ)", f"{sigma_total:.2f} kPa")
                st.metric("Pore Pressure (u)", f"{u_val:.2f} kPa")
                st.metric("Effective Stress (σ')", f"{sigma_prime:.2f} kPa")
                    
                with st.expander("View Step-by-Step Derivation"):
                    st.latex(rf"H_{{top}} = {H_top:.2f} m, \quad H_{{bot}} = {H_bot:.2f} m")
                    st.latex(rf"\sigma = {sigma_total:.2f} kPa")
                    st.latex(rf"u = {u_val:.2f} kPa")

        with col_plot:
            # Reusing the previous 1D Seepage Logic (Hidden for brevity, same as before)
            fig, ax = plt.subplots(figsize=(7, 8))
            datum_y, soil_w, soil_x = 0.0, 2.5, 3.5
            wl_top = val_z + val_y  
            wl_bot = val_x          
            
            # Draw Soil
            ax.add_patch(patches.Rectangle((soil_x, datum_y), soil_w, val_z, facecolor='#E3C195', hatch='...', edgecolor='none'))
            ax.text(soil_x + soil_w/2, datum_y + val_z/2, "SOIL", ha='center', fontweight='bold')
            
            # Draw Water
            tank_w = 2.0
            tank_base_y = max(datum_y + val_z, wl_top - 0.5)
            # Top Tank
            ax.add_patch(patches.Rectangle((soil_x + (soil_w-tank_w)/2, tank_base_y), tank_w, wl_top - tank_base_y, facecolor='#D6EAF8', edgecolor='blue'))
            # Draw Walls
            ax.plot([soil_x, soil_x], [datum_y, datum_y+val_z], 'k-', lw=2)
            ax.plot([soil_x+soil_w, soil_x+soil_w], [datum_y, datum_y+val_z], 'k-', lw=2)
            
            # Dimensions
            ax.plot([-0.5, 8], [datum_y, datum_y], 'k-.') # Datum
            ax.annotate('', xy=(soil_x-0.4, datum_y), xytext=(soil_x-0.4, datum_y+val_z), arrowprops=dict(arrowstyle='<->'))
            ax.text(soil_x-0.5, val_z/2, f"z={val_z}m", ha='right')

            # Point A
            ax.scatter(soil_x + soil_w/2, val_A, c='black', zorder=5)
            ax.text(soil_x + soil_w/2 + 0.2, val_A, "A", fontweight='bold')
            
            ax.set_xlim(0, 8)
            ax.set_ylim(-1, wl_top+1)
            ax.axis('off')
            st.pyplot(fig)


    # =================================================================
    # TAB 2: PERMEABILITY (Lab Tests) - UPDATED RESULT DISPLAY
    # =================================================================
    with tab2:
        st.caption("Calculate Coefficient of Permeability (k). Input variables are marked on the diagram.")
        col_input_2, col_plot_2 = st.columns([1, 1.2])

        with col_input_2:
            st.markdown("### 1. Test Configuration")
            test_type = st.radio("Select Method", ["Constant Head", "Falling Head"], horizontal=True)
            st.markdown("---")

            if "Constant" in test_type:
                # Constant Head Setup
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
                        # --- NEW PROFESSIONAL RESULT DISPLAY ---
                        st.markdown(f"""
                        <div style="background-color: #d1e7dd; padding: 20px; border-radius: 10px; border: 1px solid #0f5132; text-align: center; margin-top: 20px;">
                            <p style="color: #0f5132; margin-bottom: 5px; font-size: 16px; font-weight: 600;">Permeability Coefficient (k)</p>
                            <h2 style="color: #0f5132; margin: 0; font-size: 32px; font-weight: 800;">{k_val:.4e} cm/sec</h2>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Inputs must be positive.")

            else:
                # Falling Head Setup
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
                        # --- NEW PROFESSIONAL RESULT DISPLAY ---
                        st.markdown(f"""
                        <div style="background-color: #d1e7dd; padding: 20px; border-radius: 10px; border: 1px solid #0f5132; text-align: center; margin-top: 20px;">
                            <p style="color: #0f5132; margin-bottom: 5px; font-size: 16px; font-weight: 600;">Permeability Coefficient (k)</p>
                            <h2 style="color: #0f5132; margin: 0; font-size: 32px; font-weight: 800;">{k_val:.4e} cm/sec</h2>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("Inputs invalid. h2 must be > 0.")

        with col_plot_2:
            fig2, ax2 = plt.subplots(figsize=(6, 8))
            ax2.set_xlim(0, 10)
            ax2.set_ylim(0, 10)
            ax2.axis('off')
            
            # Common Style
            soil_color = '#E3C195'
            water_color = '#D6EAF8'
            wall_color = 'black'

            if "Constant" in test_type:
                # --- CONSTANT HEAD (Vertical Stack) ---
                # 1. Top Supply Tank (y=8 to 9.5)
                ax2.add_patch(patches.Rectangle((2, 8), 4, 1.5, facecolor=water_color, edgecolor=wall_color))
                ax2.text(2.2, 8.2, "Supply\nTank", fontsize=8)
                ax2.plot([2, 6], [9, 9], 'b-', lw=2)
                ax2.plot(4, 9, marker='v', color='blue')
                
                # 2. Connection Pipe
                ax2.add_patch(patches.Rectangle((3.8, 6), 0.4, 2, facecolor=water_color, edgecolor='none'))
                ax2.plot([3.8, 3.8], [6, 8], 'k-')
                ax2.plot([4.2, 4.2], [6, 8], 'k-')

                # 3. Soil Chamber (y=4 to 6)
                ax2.add_patch(patches.Rectangle((3, 4), 2, 2, facecolor=soil_color, hatch='X', edgecolor=wall_color, lw=2))
                ax2.text(4, 5, "SOIL\nArea A", ha='center', va='center', fontweight='bold')
                
                # 4. Bottom Outlet Tank (y=1 to 2.5)
                ax2.add_patch(patches.Rectangle((3.8, 2.5), 0.4, 1.5, facecolor=water_color, edgecolor='none'))
                ax2.plot([3.8, 3.8], [2.5, 4], 'k-')
                ax2.plot([4.2, 4.2], [2.5, 4], 'k-')
                ax2.add_patch(patches.Rectangle((3.5, 1), 3, 1.5, facecolor=water_color, edgecolor=wall_color))
                ax2.text(6, 0.5, "Collection\nTank", ha='center')
                ax2.plot([3.5, 6.5], [2.2, 2.2], 'b-', lw=2)
                ax2.plot(6, 2.2, marker='v', color='blue')

                # Dimensions
                ax2.annotate('', xy=(8, 2.2), xytext=(8, 9), arrowprops=dict(arrowstyle='<->', lw=1.5))
                ax2.text(8.2, 5.5, "h (Head Diff)", ha='left', fontweight='bold', fontsize=12, color='blue')
                ax2.plot([6, 8.2], [9, 9], 'k--', lw=0.5)
                ax2.plot([6.5, 8.2], [2.2, 2.2], 'k--', lw=0.5)

                ax2.annotate('', xy=(1.5, 4), xytext=(1.5, 6), arrowprops=dict(arrowstyle='<->', lw=1.5))
                ax2.text(1.2, 5, "L", ha='right', fontweight='bold', fontsize=12)
                ax2.plot([1.5, 3], [4, 4], 'k--', lw=0.5)
                ax2.plot([1.5, 3], [6, 6], 'k--', lw=0.5)
                
                ax2.text(6.8, 1.5, "-> Q (Vol)", ha='left', fontstyle='italic')

            else:
                # --- FALLING HEAD (Standpipe on Top) ---
                ax2.add_patch(patches.Rectangle((3.8, 6), 0.4, 3.5, facecolor=water_color, edgecolor=wall_color))
                ax2.text(3.5, 8, "Standpipe\n(Area a)", ha='right', fontsize=9)
                
                ax2.add_patch(patches.Rectangle((3, 4), 2, 2, facecolor=soil_color, hatch='X', edgecolor=wall_color, lw=2))
                ax2.text(4, 5, "SOIL\nArea A", ha='center', va='center', fontweight='bold')
                
                ax2.add_patch(patches.Rectangle((3.8, 2), 0.4, 2, facecolor=water_color, edgecolor='none'))
                ax2.plot([3.8, 3.8], [2, 4], 'k-')
                ax2.plot([4.2, 4.2], [2, 4], 'k-')
                ax2.add_patch(patches.Rectangle((3.5, 1), 3, 1.5, facecolor=water_color, edgecolor=wall_color))
                ax2.plot([3.5, 6.5], [2, 2], 'b-', lw=2)
                ax2.plot(6, 2, marker='v', color='blue')

                # Dimensions
                ax2.plot([3.8, 4.2], [9, 9], 'r-', lw=2)
                ax2.text(4.4, 9, "Start", fontsize=8, color='red')
                ax2.plot([3.8, 4.2], [7, 7], 'r-', lw=2)
                ax2.text(4.4, 7, "End", fontsize=8, color='red')

                ax2.annotate('', xy=(8, 2), xytext=(8, 9), arrowprops=dict(arrowstyle='<->', color='red'))
                ax2.text(8.2, 9, "h1", ha='left', fontweight='bold', color='red')
                ax2.plot([4.2, 8.2], [9, 9], 'r--', lw=0.5)
                
                ax2.annotate('', xy=(7, 2), xytext=(7, 7), arrowprops=dict(arrowstyle='<->', color='red'))
                ax2.text(7.2, 7, "h2", ha='left', fontweight='bold', color='red')
                ax2.plot([4.2, 7.2], [7, 7], 'r--', lw=0.5)
                
                ax2.plot([6.5, 8.2], [2, 2], 'b--', lw=0.5)

                ax2.annotate('', xy=(1.5, 4), xytext=(1.5, 6), arrowprops=dict(arrowstyle='<->', lw=1.5))
                ax2.text(1.2, 5, "L", ha='right', fontweight='bold', fontsize=12)
                ax2.plot([1.5, 3], [4, 4], 'k--', lw=0.5)
                ax2.plot([1.5, 3], [6, 6], 'k--', lw=0.5)

            st.pyplot(fig2)

    # =================================================================
    # TAB 3: FLOW NETS (Quick Sand) - SAME AS BEFORE
    # =================================================================
    with tab3:
        st.caption("Calculate Critical Hydraulic Gradient and visualize Seepage Force.")
        col_input_3, col_plot_3 = st.columns([1, 1.2])

        with col_input_3:
            st.markdown("### 1. Soil Parameters")
            st.latex(r"i_{cr} = \frac{G_s - 1}{1+e}")
            Gs = st.number_input("Specific Gravity (Gs)", 2.0, 3.0, 2.65, step=0.01)
            e = st.number_input("Void Ratio (e)", 0.1, 2.0, 0.60, step=0.01)
            st.markdown("---")
            if st.button("Calculate Critical Gradient", type="primary"):
                icr = (Gs - 1) / (1 + e)
                st.success("Calculation Successful")
                st.metric("Critical Gradient (i_cr)", f"{icr:.3f}")

        with col_plot_3:
            fig3, ax3 = plt.subplots(figsize=(6, 6))
            ax3.set_xlim(0, 10); ax3.set_ylim(0, 10); ax3.axis('off')
            ax3.add_patch(patches.Rectangle((3, 3), 4, 4, facecolor='#E3C195', hatch='X', edgecolor='black', lw=2))
            ax3.text(5, 5, "Soil\nElement", ha='center', fontweight='bold')
            ax3.annotate('', xy=(5, 4), xytext=(5, 8.5), arrowprops=dict(arrowstyle='->', color='black', lw=3))
            ax3.text(5.2, 8, "Weight (Down)", ha='left')
            ax3.annotate('', xy=(5, 6), xytext=(5, 1.5), arrowprops=dict(arrowstyle='->', color='red', lw=3))
            ax3.text(5.2, 2, "Seepage (Up)", ha='left', color='red', fontweight='bold')
            st.pyplot(fig3)

if __name__ == "__main__":
    app()
