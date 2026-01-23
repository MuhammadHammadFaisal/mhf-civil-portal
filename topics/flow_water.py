import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def app():
    st.markdown("---")
    st.subheader("💧 Flow of Water & Seepage Analysis")

    # TABS FOR DIFFERENT PROBLEM TYPES
    tab1, tab2, tab3 = st.tabs(["1️⃣ 1D Seepage (Effective Stress)", "2️⃣ Permeability Tests", "3️⃣ Flow Nets & Piping"])

    # =================================================================
    # TAB 1: 1D SEEPAGE (The "Diagram" Problem)
    # =================================================================
    with tab1:
        st.caption("Determine Effective Stress under Upward or Downward Flow conditions.")
        
        col_setup, col_plot = st.columns([1, 1])
        
        with col_setup:
            st.markdown("### 1. Define Problem from Diagram")
            
            # Flow Direction
            flow_dir = st.radio("Flow Direction:", ["Downward Flow ⬇️", "Upward Flow ⬆️"], horizontal=True)
            
            # Geometric Inputs
            H_water = st.number_input("Height of Water above Soil (H1) [m]", 0.0, step=0.5, value=1.0)
            H_soil = st.number_input("Height of Soil Specimen (H2) [m]", 0.1, step=0.5, value=2.0)
            
            # Head Loss Input
            h_diff = st.number_input("Head Difference / Head Loss (h) [m]", 0.0, step=0.1, value=1.0, 
                                   help="Difference in water level between top and bottom piezometers.")
            
            # Soil Property
            gamma_sat = st.number_input("Saturated Unit Weight (γ_sat) [kN/m³]", 18.0, step=0.1)
            gamma_w = 9.81
            
            # Point of Interest
            z_point = st.slider("Depth of Point 'C' from Soil Surface (z) [m]", 0.0, H_soil, H_soil/2)

       # --- DYNAMIC MATPLOTLIB DIAGRAM (PROFESSIONAL VERSION) ---
        with col_plot:
            fig, ax = plt.subplots(figsize=(6, 6))
            
            # Dimensions
            W = 4      # Width of container
            H_s = H_soil
            H_w = H_water
            
            # 1. Main Container (Glass Cylinder)
            ax.plot([0, 0], [-0.5, H_s + H_w + 1], 'k-', linewidth=2.5) # Left Wall
            ax.plot([W, W], [-0.5, H_s + H_w + 1], 'k-', linewidth=2.5) # Right Wall
            ax.plot([0, W], [-0.5, -0.5], 'k-', linewidth=2.5) # Bottom Cap
            
            # 2. Porous Stones (Top & Bottom)
            # Bottom Stone
            rect_stone_bot = patches.Rectangle((0, 0), W, 0.2, facecolor='gray', hatch='///', alpha=0.5)
            ax.add_patch(rect_stone_bot)
            # Top Stone
            rect_stone_top = patches.Rectangle((0, H_s-0.2), W, 0.2, facecolor='gray', hatch='///', alpha=0.5)
            ax.add_patch(rect_stone_top)
            
            # 3. Soil Sample
            rect_soil = patches.Rectangle((0, 0.2), W, H_s-0.4, facecolor='#C19A6B', alpha=0.6, hatch='...')
            ax.add_patch(rect_soil)
            ax.text(W/2, H_s/2, f"SOIL SAMPLE\nL = {H_s}m\nγ_sat = {gamma_sat}", 
                   ha='center', va='center', fontsize=10, fontweight='bold', color='#4B3621')

            # 4. Water Above Soil (Reservoir)
            rect_water = patches.Rectangle((0, H_s), W, H_w, facecolor='#A4D8E8', alpha=0.4)
            ax.add_patch(rect_water)
            
            # 5. Piezometers & Head Levels
            # Top Level (Constant)
            wl_top = H_s + H_w
            ax.plot([0, W], [wl_top, wl_top], 'b-', linewidth=1.5)
            ax.text(W/2, wl_top + 0.1, "Water Level (Top)", ha='center', color='blue', fontsize=8)
            # Triangle symbol for water surface
            ax.plot([W/2], [wl_top], marker='v', color='blue')

            # Draw External Piezometer Tube for Bottom Pressure
            # Tube Body
            tube_x = -1.5
            ax.plot([tube_x, tube_x+0.4], [0.2, 0.2], 'k-', linewidth=1) # Connection to soil bottom
            ax.plot([tube_x, tube_x], [0.2, wl_top+h_diff+1], 'k-', linewidth=1) # Vertical tube
            ax.plot([tube_x+0.4, tube_x+0.4], [0.2, wl_top+h_diff+1], 'k-', linewidth=1)
            
            # Calculate Bottom Head Level
            if "Downward" in flow_dir:
                wl_bot = wl_top - h_diff
                flow_arrow_y = wl_top + 0.5
                flow_arrow_dir = -1
                color_h = 'red'
            else: # Upward
                wl_bot = wl_top + h_diff
                flow_arrow_y = -0.5
                flow_arrow_dir = 1
                color_h = 'green'

            # Fill Piezometer Water
            rect_piezo = patches.Rectangle((tube_x, 0.2), 0.4, wl_bot-0.2, facecolor='#A4D8E8', alpha=0.8)
            ax.add_patch(rect_piezo)
            
            # Water Level in Piezometer
            ax.plot([tube_x, tube_x+0.4], [wl_bot, wl_bot], 'b-', linewidth=2)
            ax.plot([tube_x+0.2], [wl_bot], marker='v', color='blue')

            # 6. Dimension Lines for Head Difference (h)
            # Dotted extension lines
            ax.plot([tube_x+0.4, W+1], [wl_bot, wl_bot], linestyle='--', color='gray', linewidth=0.8)
            ax.plot([0, W+1], [wl_top, wl_top], linestyle='--', color='gray', linewidth=0.8)
            
            # The 'h' arrow
            ax.annotate('', xy=(W+0.8, wl_top), xytext=(W+0.8, wl_bot), arrowprops=dict(arrowstyle='<->', color=color_h))
            ax.text(W+1.0, (wl_top+wl_bot)/2, f"h = {h_diff}m", va='center', color=color_h, fontweight='bold')

            # 7. Point C (Target Depth)
            z_elev = H_s - z_point
            ax.plot([0, W], [z_elev, z_elev], 'r--', linewidth=1.5)
            ax.text(W+0.1, z_elev, f"Point C\n(z={z_point}m)", va='center', color='red', fontsize=9)

            # 8. Flow Arrows (Big indicators)
            if "Downward" in flow_dir:
                ax.arrow(W+0.5, wl_top+0.5, 0, -1.5, head_width=0.3, color='blue', alpha=0.6)
                ax.text(W+0.5, wl_top-1, "FLOW", color='blue', rotation=270, va='center')
            else:
                ax.arrow(W+0.5, 0, 0, 1.5, head_width=0.3, color='green', alpha=0.6)
                ax.text(W+0.5, 1, "FLOW", color='green', rotation=90, va='center')

            ax.set_xlim(-2.5, W+2)
            ax.set_ylim(-1, max(wl_top, wl_bot) + 1)
            ax.axis('off')
            st.pyplot(fig)

        # --- CALCULATION SECTION ---
        if st.button("🚀 Calculate Effective Stress"):
            
            # 1. Calculate Hydraulic Gradient (i)
            # i = h / L (where L is length of soil, here H_soil)
            i = h_diff / H_soil
            
            # 2. Method 1: Total Stress - Pore Pressure
            sigma_total = (H_water * gamma_w) + (z_point * gamma_sat)
            
            # Pore Pressure u at depth z
            # Start with static head (H_water + z)
            # If Downward, pressure decreases by i*z*gamma_w (loss)
            # If Upward, pressure increases by i*z*gamma_w (gain) ??
            # Wait, easier way: Find head at point C.
            # Head Loss is linear. h_loss(z) = i * z
            
            if "Downward" in flow_dir:
                # Pressure Head at C = (Static Head) - (Head Loss)
                # Static Head = H_water + z
                # Head Loss consumed so far = i * z
                h_p_C = (H_water + z_point) - (i * z_point)
                sign_str = "-"
                effect_str = "Decreases u, Increases σ'"
            else:
                # Upward
                # Pressure Head at C = (Static Head) + (Head Gain from bottom push)
                # Actually, Total Head drops in direction of flow.
                # Upward: Flow from Bottom to Top. 
                # Head at Bottom > Head at Top.
                # Head loss is linear from Bottom to Top.
                # Let's use the Effective Stress Formula directly as requested.
                h_p_C = (H_water + z_point) + (i * z_point) 
                sign_str = "+"
                effect_str = "Increases u, Decreases σ'"

            u_val = h_p_C * gamma_w
            sigma_prime_1 = sigma_total - u_val

            # 3. Method 2: The Critical Formula z(gamma' +- i*gamma_w)
            gamma_sub = gamma_sat - gamma_w
            
            if "Downward" in flow_dir:
                # Downward increases effective stress
                # Formula: sigma' = z * gamma' + (i * z * gamma_w)
                term2 = i * z_point * gamma_w
                sigma_prime_2 = (z_point * gamma_sub) + term2
                formula_latex = r"\sigma' = z\gamma' + i \cdot z \cdot \gamma_w"
            else:
                # Upward decreases effective stress
                # Formula: sigma' = z * gamma' - (i * z * gamma_w)
                term2 = i * z_point * gamma_w
                sigma_prime_2 = (z_point * gamma_sub) - term2
                formula_latex = r"\sigma' = z\gamma' - i \cdot z \cdot \gamma_w"

            # --- DISPLAY RESULTS SIDE-BY-SIDE ---
            st.markdown(f"### 📊 Results at Depth z = {z_point} m")
            st.info(f"Hydraulic Gradient, $i = h/L = {h_diff}/{H_soil} = {i:.3f}$")

            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("Method 1: $\sigma - u$")
                st.markdown("**1. Total Stress ($\sigma$)**")
                st.latex(rf"\sigma = (H_1 \gamma_w) + (z \gamma_{{sat}})")
                st.latex(rf"\sigma = ({H_water} \cdot 9.81) + ({z_point} \cdot {gamma_sat}) = \mathbf{{{sigma_total:.2f} \, kPa}}")
                
                st.markdown("**2. Pore Pressure ($u$)**")
                st.latex(rf"u = (H_{{static}} {sign_str} h_{{loss}}) \gamma_w")
                st.latex(rf"u = [({H_water} + {z_point}) {sign_str} ({i:.3f} \cdot {z_point})] \cdot 9.81 = \mathbf{{{u_val:.2f} \, kPa}}")
                
                st.markdown("**3. Effective Stress**")
                st.latex(rf"\sigma' = {sigma_total:.2f} - {u_val:.2f} = \mathbf{{{sigma_prime_1:.2f} \, kPa}}")

            with c2:
                st.subheader("Method 2: $z(\gamma' \pm i\gamma_w)$")
                st.markdown("**1. Submerged Unit Wt ($\gamma'$)**")
                st.latex(rf"\gamma' = \gamma_{{sat}} - \gamma_w = {gamma_sat} - 9.81 = {gamma_sub:.2f}")
                
                st.markdown("**2. Direct Formula**")
                st.latex(formula_latex)
                st.latex(rf"\sigma' = ({z_point} \cdot {gamma_sub:.2f}) {sign_str} ({i:.3f} \cdot {z_point} \cdot 9.81)")
                st.latex(rf"\sigma' = \mathbf{{{sigma_prime_2:.2f} \, kPa}}")

            # Final Verification
            if abs(sigma_prime_1 - sigma_prime_2) < 0.1:
                st.success("✅ Both methods give the same result!")
            else:
                st.error("Something went wrong. Check inputs.")


    # =================================================================
    # TAB 2: PERMEABILITY (Lab Tests)
    # =================================================================
    with tab2:
        st.subheader("🧪 Permeability Tests")
        test_type = st.radio("Test Type", ["Constant Head", "Falling Head"], horizontal=True)
        
        if "Constant" in test_type:
            st.latex(r"k = \frac{Q \cdot L}{A \cdot h \cdot t}")
            c1, c2, c3 = st.columns(3)
            Q = c1.number_input("Volume (Q) [cm³]", 0.0)
            L = c2.number_input("Length (L) [cm]", 0.0)
            h = c3.number_input("Head (h) [cm]", 0.0)
            c4, c5 = st.columns(2)
            A = c4.number_input("Area (A) [cm²]", 0.0)
            t = c5.number_input("Time (t) [sec]", 0.0)
            
            if st.button("Calculate k (Constant)"):
                if A*h*t > 0:
                    k = (Q*L)/(A*h*t)
                    st.success(f"k = {k:.4e} cm/sec")
                else: st.error("Inputs cannot be zero")
                
        else:
            st.latex(r"k = 2.303 \frac{a \cdot L}{A \cdot t} \log_{10}\left(\frac{h_1}{h_2}\right)")
            c1, c2 = st.columns(2)
            a = c1.number_input("Standpipe Area (a)", 0.0, format="%.4f")
            A_soil = c2.number_input("Soil Area (A)", 0.0)
            L = c1.number_input("Length (L)", 0.0)
            t = c2.number_input("Time (t)", 0.0)
            h1 = c1.number_input("Start Head (h1)", 0.0)
            h2 = c2.number_input("End Head (h2)", 0.0)
            
            if st.button("Calculate k (Falling)"):
                if A_soil*t > 0 and h1>h2:
                    k = (2.303 * a * L / (A_soil * t)) * np.log10(h1/h2)
                    st.success(f"k = {k:.4e} cm/sec")

    # =================================================================
    # TAB 3: QUICK CONDITION & FLOW NETS
    # =================================================================
    with tab3:
        st.subheader("⚠️ Quick Sand & Seepage")
        
        st.markdown("**1. Critical Hydraulic Gradient**")
        st.latex(r"i_{cr} = \frac{G_s - 1}{1+e}")
        Gs = st.number_input("Gs", 2.65)
        e = st.number_input("Void Ratio e", 0.6)
        
        icr = (Gs - 1)/(1+e)
        st.metric("Critical Gradient (i_cr)", f"{icr:.3f}")
        
        st.markdown("---")
        st.markdown("**2. Flow Net Calculation**")
        st.latex(r"q = k \cdot H \cdot \frac{N_f}{N_d}")
        k_net = st.number_input("Permeability k", 0.0, format="%.5f")
        H_net = st.number_input("Total Head Loss H", 0.0)
        Nf = st.number_input("Flow Channels (Nf)", 1.0)
        Nd = st.number_input("Equipotential Drops (Nd)", 1.0)
        
        if st.button("Calculate Seepage q"):
            q = k_net * H_net * (Nf/Nd)
            st.success(f"Seepage q = {q:.4f}")
