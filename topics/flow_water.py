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

        # --- DYNAMIC MATPLOTLIB DIAGRAM (TEXTBOOK STYLE) ---
        with col_plot:
            # Create Figure
            fig, ax = plt.subplots(figsize=(6, 6))
            
            # Dimensions
            W = 3.0       # Width of soil sample
            H_s = H_soil
            H_w = H_water
            
            # --- 1. DRAW THE SOIL COLUMN ---
            # Soil Fill
            rect_soil = patches.Rectangle((0, 0), W, H_s, facecolor='#E3C195', edgecolor='black', hatch='.', linewidth=2)
            ax.add_patch(rect_soil)
            ax.text(W/2, H_s/2, f"SOIL SPECIMEN\nL = {H_s}m\nγ_sat = {gamma_sat}", 
                   ha='center', va='center', fontweight='bold', color='#5C4033', fontsize=10)

            # Porous Stones (Top and Bottom)
            ax.add_patch(patches.Rectangle((0, -0.2), W, 0.2, facecolor='lightgray', hatch='///', edgecolor='black'))
            ax.add_patch(patches.Rectangle((0, H_s), W, 0.2, facecolor='lightgray', hatch='///', edgecolor='black'))

            # Water Reservoir (Top)
            rect_water = patches.Rectangle((0, H_s+0.2), W, H_w, facecolor='#A4D8E8', edgecolor='none', alpha=0.5)
            ax.add_patch(rect_water)
            
            # Container Walls
            ax.plot([0, 0], [-0.5, H_s + H_w + 1.5], 'k-', linewidth=3) # Left
            ax.plot([W, W], [-0.5, H_s + H_w + 1.5], 'k-', linewidth=3) # Right
            
            # --- 2. WATER LEVELS & PIEZOMETERS ---
            # Top Water Level (Reference)
            wl_top = H_s + H_w + 0.2
            
            # Calculate Bottom Head Level based on Flow
            if "Downward" in flow_dir:
                wl_bot = wl_top - h_diff
                gradient_color = 'red'
                flow_symbol = r'$\downarrow$'
            else:
                wl_bot = wl_top + h_diff
                gradient_color = 'green'
                flow_symbol = r'$\uparrow$'

            # Draw Water Level Line (Top)
            ax.hlines(wl_top, -1, W+3, colors='blue', linewidth=2)
            ax.plot(W+1, wl_top, marker='v', markersize=10, color='blue') # Triangle Symbol
            ax.text(W+1.2, wl_top, "Top Level", va='center', color='blue', fontsize=9)

            # Draw Piezometer Level (Bottom) - Represented as a Standpipe on the right
            pipe_x = W + 2.5
            # Connection tube from bottom of soil to standpipe
            ax.plot([W, W+0.5, pipe_x, pipe_x], [0, 0, 0, wl_bot+1], 'k-', linewidth=1.5) 
            
            # The Water inside Pipe
            ax.add_patch(patches.Rectangle((pipe_x-0.15, 0), 0.3, wl_bot, facecolor='#A4D8E8', edgecolor='black'))
            
            # The Level Line (Bottom)
            ax.hlines(wl_bot, pipe_x-0.5, pipe_x+0.5, colors='blue', linewidth=2)
            ax.plot(pipe_x, wl_bot, marker='v', markersize=10, color='blue')
            ax.text(pipe_x+0.6, wl_bot, "Piezometric Level\n(At Bottom)", va='center', color='blue', fontsize=9)

            # --- 3. THE HYDRAULIC GRADIENT LINE (The "Teaching" Line) ---
            # This line connects Top Head to Bottom Head, visually showing the pressure drop
            ax.plot([W+1, pipe_x], [wl_top, wl_bot], color=gradient_color, linestyle='--', linewidth=2, label='Hydraulic Gradient')
            
            # Label 'h' (Head Loss)
            mid_y = (wl_top + wl_bot) / 2
            ax.annotate('', xy=(pipe_x, wl_top), xytext=(pipe_x, wl_bot), arrowprops=dict(arrowstyle='<->', color='black'))
            ax.text(pipe_x + 0.2, mid_y, f"h = {h_diff}m", va='center', fontweight='bold')

            # --- 4. POINT C & DATUM ---
            # Datum at Bottom
            ax.hlines(0, -1, W+4, colors='black', linestyles='-.', linewidth=1)
            ax.text(-0.8, 0, "DATUM (z=0)", va='bottom', fontsize=8)
            
            # Point C
            z_c = H_s - z_point # Elevation of C
            ax.hlines(z_c, 0, W, colors='red', linestyles='-', linewidth=2)
            ax.text(0.2, z_c + 0.1, f"Point C (Depth z={z_point}m)", color='red', fontweight='bold')
            
            # --- 5. FLOW ARROW ---
            ax.text(W/2, H_s + H_w/2, f"FLOW {flow_symbol}", ha='center', va='center', fontsize=12, fontweight='bold', color='blue', bbox=dict(facecolor='white', alpha=0.7, edgecolor='none'))

            # Plot Settings
            ax.set_xlim(-1, W+4)
            ax.set_ylim(-1, max(wl_top, wl_bot) + 2)
            ax.axis('off')
            ax.set_title("Permeameter Setup", fontsize=14)
            
            st.pyplot(fig)

        st.divider()

        # --- CALCULATION SECTION ---
        if st.button("🚀 Calculate Effective Stress"):
            
            # 1. Calculate Hydraulic Gradient (i)
            # i = h / L (where L is length of soil, here H_soil)
            i = h_diff / H_soil
            
            # 2. Method 1: Total Stress - Pore Pressure
            sigma_total = (H_water * gamma_w) + (z_point * gamma_sat)
            
            # Logic for Pore Pressure (u) and Effective Stress (sigma')
            if "Downward" in flow_dir:
                # Downward Flow: Effective Stress INCREASES
                h_p_C = (H_water + z_point) - (i * z_point)
                sign_str = "-"
                gamma_sub = gamma_sat - gamma_w
                
                # Method 2 Formula
                formula_latex = r"\sigma' = z\gamma' + i \cdot z \cdot \gamma_w"
                term2 = i * z_point * gamma_w
                sigma_prime_2 = (z_point * gamma_sub) + term2

            else:
                # Upward Flow: Effective Stress DECREASES
                h_p_C = (H_water + z_point) + (i * z_point) 
                sign_str = "+"
                gamma_sub = gamma_sat - gamma_w
                
                # Method 2 Formula
                formula_latex = r"\sigma' = z\gamma' - i \cdot z \cdot \gamma_w"
                term2 = i * z_point * gamma_w
                sigma_prime_2 = (z_point * gamma_sub) - term2

            u_val = h_p_C * gamma_w
            sigma_prime_1 = sigma_total - u_val

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
