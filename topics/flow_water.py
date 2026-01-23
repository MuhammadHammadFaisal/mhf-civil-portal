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
        st.caption("Determine Effective Stress at Point C using the Total Head Line method.")
        
        col_setup, col_plot = st.columns([1, 1.2])
        
        with col_setup:
            st.markdown("### 1. Problem Setup")
            
            # Flow Direction
            flow_dir = st.radio("Flow Direction:", ["Downward Flow ⬇️", "Upward Flow ⬆️"], horizontal=True)
            
            # Geometric Inputs
            H1 = st.number_input("Water height above soil (H1) [m]", 0.0, step=0.5, value=2.0)
            H2 = st.number_input("Soil specimen height (H2) [m]", 0.1, step=0.5, value=4.0)
            
            # Head Loss Input
            h_loss = st.number_input("Head Loss (h) [m]", 0.0, step=0.1, value=1.5, 
                                   help="Difference between Top Water Level and Bottom Piezometer Level.")
            
            # Soil Property
            gamma_sat = st.number_input("Saturated Unit Weight (γ_sat) [kN/m³]", 18.0, step=0.1)
            gamma_w = 9.81
            
            # Point of Interest
            z = st.slider("Depth of Point 'C' (z) [m]", 0.0, H2, H2/2)

        # --- DYNAMIC MATPLOTLIB DIAGRAM (TEXTBOOK STYLE) ---
        with col_plot:
            fig, ax = plt.subplots(figsize=(6, 7))
            
            # COORDINATES (0,0 is bottom left of soil)
            # Soil is from y=0 to y=H2
            # Water is from y=H2 to y=H2+H1
            
            # 1. DRAW SOIL & CONTAINER
            # Soil Block
            rect_soil = patches.Rectangle((0, 0), 3, H2, facecolor='#E3C195', hatch='.', edgecolor='black', linewidth=1.5)
            ax.add_patch(rect_soil)
            ax.text(1.5, H2/2, f"SOIL\nL = {H2}m\nγ_sat = {gamma_sat}", ha='center', va='center', fontweight='bold', fontsize=9)

            # Container Walls
            ax.plot([0, 0], [-1, H2 + H1 + 1], 'k-', linewidth=3) # Left Wall
            ax.plot([3, 3], [-1, H2 + H1 + 1], 'k-', linewidth=3) # Right Wall
            
            # Porous Stones (Top & Bottom)
            ax.add_patch(patches.Rectangle((0, -0.2), 3, 0.2, facecolor='gray', hatch='///'))
            ax.add_patch(patches.Rectangle((0, H2), 3, 0.2, facecolor='gray', hatch='///'))

            # Top Water Reservoir
            rect_water = patches.Rectangle((0, H2+0.2), 3, H1, facecolor='#A4D8E8', alpha=0.6)
            ax.add_patch(rect_water)

            # 2. DEFINE HEAD LEVELS
            # Datum is at y=0 (Bottom of soil)
            # Top Head (Total Head at Top)
            TH_top = H2 + H1 + 0.2
            
            # Bottom Head (Total Head at Bottom)
            if "Downward" in flow_dir:
                TH_bot = TH_top - h_loss
                grad_color = 'red'
                flow_arrow_y = H2 + H1 + 0.5
                flow_sym = r'$\downarrow$'
            else:
                TH_bot = TH_top + h_loss
                grad_color = 'green'
                flow_arrow_y = -0.5
                flow_sym = r'$\uparrow$'

            # 3. DRAW WATER LEVELS & PIEZOMETERS
            
            # Top Water Level Line
            ax.hlines(TH_top, -0.5, 4.5, colors='blue', linewidth=2)
            ax.plot(3.5, TH_top, marker='v', color='blue', markersize=8)
            ax.text(3.6, TH_top, "Top Level", va='center', color='blue', fontsize=8)

            # Bottom Piezometer (Standpipe on the right)
            pipe_x = 4.5
            # Connect tube from bottom of soil (y=0) to standpipe
            ax.plot([3, 3.5, pipe_x, pipe_x], [0, 0, 0, TH_bot], 'k-', linewidth=1)
            # Water in standpipe
            ax.plot([pipe_x-0.2, pipe_x+0.2], [TH_bot, TH_bot], 'b-', linewidth=2)
            ax.plot(pipe_x, TH_bot, marker='v', color='blue', markersize=8)
            ax.text(pipe_x+0.3, TH_bot, "Bottom\nPiezometer", va='center', color='blue', fontsize=8)

            # 4. THE TOTAL HEAD LINE (The "Teaching" Line)
            # Connects Head at Top of Soil (y=H2) to Head at Bottom of Soil (y=0)
            # At Top of Soil (y=H2), Head is TH_top
            # At Bottom of Soil (y=0), Head is TH_bot
            # We draw this line visually to the right of the diagram
            
            line_x = 3.5 # X-position for the head line
            ax.plot([line_x, line_x], [TH_top, TH_bot], color=grad_color, linestyle='--', linewidth=2, label='Hydraulic Gradient')
            ax.plot([line_x-0.1, line_x+0.1], [TH_top, TH_top], 'k-') # Tick at top
            ax.plot([line_x-0.1, line_x+0.1], [TH_bot, TH_bot], 'k-') # Tick at bot
            
            # Label 'h'
            mid_h = (TH_top + TH_bot) / 2
            ax.text(line_x - 0.2, mid_h, f"h={h_loss}", ha='right', va='center', color=grad_color, fontweight='bold')
            ax.annotate('', xy=(line_x, TH_top), xytext=(line_x, TH_bot), arrowprops=dict(arrowstyle='<->', color=grad_color))

            # 5. POINT C
            z_elev = H2 - z
            ax.hlines(z_elev, 0, 3, colors='red', linestyle='-', linewidth=2)
            ax.text(0.2, z_elev + 0.1, f"Point C (z={z}m)", color='red', fontweight='bold', fontsize=10)
            
            # Datum Line
            ax.hlines(0, -1, 5, colors='black', linestyle='-.', linewidth=1)
            ax.text(-0.8, 0, "DATUM (z=0)", va='bottom', fontsize=8)

            # Flow Arrow
            ax.text(1.5, H2/2, f"FLOW {flow_sym}", ha='center', va='center', 
                   fontsize=14, color='blue', alpha=0.3, fontweight='bold')

            # Plot Limits
            ax.set_xlim(-1, 6)
            ax.set_ylim(-2, max(TH_top, TH_bot) + 2)
            ax.axis('off')
            st.pyplot(fig)

        st.divider()

        # --- CALCULATION LOGIC ---
        if st.button("🚀 Calculate Effective Stress"):
            i = h_loss / H2 # Hydraulic Gradient
            
            # Determine Sign based on Flow Direction
            if "Downward" in flow_dir:
                sign_txt = "-"
                effect_txt = "Downward flow increases Effective Stress"
                # Method 2 Formula
                sigma_prime_2 = z * (gamma_sat - gamma_w) + (i * z * gamma_w)
                formula_latex = r"\sigma' = z\gamma' + i z \gamma_w"
                
                # Pore Pressure Logic
                # u = (Static Head - Head Loss) * gamma_w
                # Static head at C = H1 + z
                # Head Loss at C = i * z
                u_val = ((H1 + z) - (i * z)) * gamma_w
                
            else:
                sign_txt = "+"
                effect_txt = "Upward flow decreases Effective Stress"
                # Method 2 Formula
                sigma_prime_2 = z * (gamma_sat - gamma_w) - (i * z * gamma_w)
                formula_latex = r"\sigma' = z\gamma' - i z \gamma_w"
                
                # Pore Pressure Logic
                # u = (Static Head + Head Gain) * gamma_w ?? 
                # Actually for Upward: Total Head drops from bottom to top.
                # Let's trust the Effective Stress formula as the primary verification.
                # u = Total Stress - Effective Stress
                # But let's calculate u from head for verification.
                # Head at bottom = H1 + H2 + h. 
                # Head at C = Head_Bottom - Loss_to_C
                # Loss_to_C = i * (H2 - z). (Distance from bottom)
                # Head_C = (H1 + H2 + h) - i*(H2-z)
                # Elevation Head = (H2 - z)
                # Pressure Head = Head_C - Elev_Head
                # This is complex to display simply. Let's stick to the Method 2 Formula which is standard for exams.
                u_val = ((H1 + z) + (i*z)) * gamma_w # Simplified approximation for display

            sigma_total = (H1 * gamma_w) + (z * gamma_sat)
            sigma_prime_1 = sigma_total - u_val

            st.success(f"**Condition:** {effect_txt}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Method 1: $\sigma - u$**")
                st.latex(rf"\sigma = {H1}\gamma_w + {z}\gamma_{{sat}} = {sigma_total:.2f}")
                st.latex(rf"u = ({H1} + {z}) \gamma_w {sign_txt} (i \cdot z \cdot \gamma_w) = {u_val:.2f}")
                st.latex(rf"\sigma' = {sigma_total:.2f} - {u_val:.2f} = \mathbf{{{sigma_prime_1:.2f} \, kPa}}")
            
            with c2:
                st.markdown("**Method 2: Direct Formula**")
                st.latex(rf"i = h/L = {h_loss}/{H2} = {i:.3f}")
                st.latex(formula_latex)
                st.latex(rf"\sigma' = \mathbf{{{sigma_prime_2:.2f} \, kPa}}")

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
            if st.button("Calculate k"):
                if A*h*t > 0: st.success(f"k = {(Q*L)/(A*h*t):.4e} cm/sec")
        else:
            st.latex(r"k = 2.303 \frac{a \cdot L}{A \cdot t} \log_{10}\left(\frac{h_1}{h_2}\right)")
            c1, c2 = st.columns(2)
            a = c1.number_input("Standpipe Area (a)", 0.0, format="%.4f")
            A_soil = c2.number_input("Soil Area (A)", 0.0)
            L = c1.number_input("Length (L)", 0.0)
            t = c2.number_input("Time (t)", 0.0)
            h1 = c1.number_input("Start Head (h1)", 0.0)
            h2 = c2.number_input("End Head (h2)", 0.0)
            if st.button("Calculate k"):
                if A_soil*t > 0: st.success(f"k = {(2.303*a*L/(A_soil*t))*np.log10(h1/h2):.4e} cm/sec")

    # =================================================================
    # TAB 3: FLOW NETS
    # =================================================================
    with tab3:
        st.subheader("⚠️ Quick Sand & Seepage")
        st.latex(r"i_{cr} = \frac{G_s - 1}{1+e}")
        Gs = st.number_input("Gs", 2.65)
        e = st.number_input("Void Ratio e", 0.6)
        if st.button("Calculate Critical Gradient"):
            st.metric("i_critical", f"{(Gs-1)/(1+e):.3f}")
