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
        st.caption("Determine Effective Stress at Point A using the Total Head Line method.")
        
        col_setup, col_plot = st.columns([1, 1.2])
        
        with col_setup:
            st.markdown("### 1. Problem Setup")
            
            # Flow Direction
            flow_dir = st.radio("Flow Direction:", ["Downward Flow ⬇️", "Upward Flow ⬆️"], horizontal=True)
            
            # Geometric Inputs
            H1 = st.number_input("Water height above soil (χ) [m]", 0.0, step=0.5, value=2.0)
            H2 = st.number_input("Soil specimen height (z) [m]", 0.1, step=0.5, value=4.0)
            
            # Head Loss Input
            h_loss = st.number_input("Head Loss (γ) [m]", 0.0, step=0.1, value=1.5, 
                                   help="Difference between Top Water Level and Bottom Piezometer Level.")
            
            # Soil Property
            gamma_sat = st.number_input("Saturated Unit Weight (γ_sat) [kN/m³]", 18.0, step=0.1)
            gamma_w = 9.81
            
            # Point of Interest
            z = st.slider("Depth of Point 'A' from top [m]", 0.0, H2, H2/2)

        # --- DYNAMIC MATPLOTLIB DIAGRAM (SKETCH STYLE) ---
        with col_plot:
            fig, ax = plt.subplots(figsize=(7, 8))
            
            # SOIL CONTAINER DIMENSIONS
            soil_width = 3
            soil_x_start = 2
            
            # DRAW MAIN SOIL CONTAINER
            # Bottom plate
            bottom_y = 0
            ax.add_patch(patches.Rectangle((soil_x_start-0.2, bottom_y-0.3), 
                                          soil_width+0.4, 0.3, 
                                          facecolor='gray', edgecolor='black', linewidth=2))
            
            # Soil mass
            rect_soil = patches.Rectangle((soil_x_start, bottom_y), soil_width, H2, 
                                         facecolor='#E3C195', hatch='..', 
                                         edgecolor='black', linewidth=2)
            ax.add_patch(rect_soil)
            ax.text(soil_x_start + soil_width/2, H2/2, "soil", 
                   ha='center', va='center', fontsize=12, style='italic')
            
            # Top porous stone
            ax.add_patch(patches.Rectangle((soil_x_start, H2), soil_width, 0.15, 
                                          facecolor='#666', hatch='///', linewidth=2))
            
            # Side walls
            ax.plot([soil_x_start, soil_x_start], [bottom_y, H2+H1+0.5], 
                   'k-', linewidth=2.5)
            ax.plot([soil_x_start+soil_width, soil_x_start+soil_width], [bottom_y, H2+H1+0.5], 
                   'k-', linewidth=2.5)
            
            # Top water reservoir
            if H1 > 0:
                rect_water = patches.Rectangle((soil_x_start, H2+0.15), soil_width, H1, 
                                              facecolor='#A4D8E8', alpha=0.5, 
                                              edgecolor='black', linewidth=2)
                ax.add_patch(rect_water)
            
            # DEFINE HEAD LEVELS
            TH_top = H2 + H1 + 0.15
            
            if "Downward" in flow_dir:
                TH_bot = TH_top - h_loss
                grad_color = 'red'
            else:
                TH_bot = TH_top + h_loss
                grad_color = 'green'
            
            # LEFT PIEZOMETER (Top)
            left_piezo_x = soil_x_start - 1.2
            piezo_width = 0.35
            
            # Left tube
            ax.add_patch(patches.Rectangle((left_piezo_x, bottom_y), piezo_width, TH_top, 
                                          facecolor='white', edgecolor='black', linewidth=2))
            # Water in left tube
            ax.add_patch(patches.Rectangle((left_piezo_x, bottom_y), piezo_width, TH_top, 
                                          facecolor='#A4D8E8', alpha=0.6))
            # Connection to top
            ax.plot([left_piezo_x + piezo_width, soil_x_start], [H2+0.15, H2+0.15], 
                   'k-', linewidth=1.5)
            # Funnel top
            ax.plot([left_piezo_x, left_piezo_x-0.15], [TH_top, TH_top+0.3], 'k-', linewidth=2)
            ax.plot([left_piezo_x+piezo_width, left_piezo_x+piezo_width+0.15], 
                   [TH_top, TH_top+0.3], 'k-', linewidth=2)
            ax.plot([left_piezo_x-0.15, left_piezo_x+piezo_width+0.15], 
                   [TH_top+0.3, TH_top+0.3], 'k-', linewidth=2)
            
            # RIGHT PIEZOMETER (Bottom)
            right_piezo_x = soil_x_start + soil_width + 0.5
            
            # Right tube
            ax.add_patch(patches.Rectangle((right_piezo_x, bottom_y), piezo_width, TH_bot, 
                                          facecolor='white', edgecolor='black', linewidth=2))
            # Water in right tube
            ax.add_patch(patches.Rectangle((right_piezo_x, bottom_y), piezo_width, TH_bot, 
                                          facecolor='#A4D8E8', alpha=0.6))
            # Connection to bottom
            ax.plot([soil_x_start+soil_width, right_piezo_x], [bottom_y, bottom_y], 
                   'k-', linewidth=1.5)
            # Funnel top
            ax.plot([right_piezo_x, right_piezo_x-0.15], [TH_bot, TH_bot+0.3], 'k-', linewidth=2)
            ax.plot([right_piezo_x+piezo_width, right_piezo_x+piezo_width+0.15], 
                   [TH_bot, TH_bot+0.3], 'k-', linewidth=2)
            ax.plot([right_piezo_x-0.15, right_piezo_x+piezo_width+0.15], 
                   [TH_bot+0.3, TH_bot+0.3], 'k-', linewidth=2)
            
            # DIMENSION LABELS
            # χ (chi) - water height above soil
            if H1 > 0:
                mid_x_left = left_piezo_x - 0.6
                ax.annotate('', xy=(mid_x_left, H2+0.15), xytext=(mid_x_left, TH_top),
                           arrowprops=dict(arrowstyle='<->', color='blue', lw=1.5))
                ax.text(mid_x_left-0.2, (H2+0.15+TH_top)/2, 'χ', 
                       fontsize=14, color='blue', fontweight='bold', style='italic')
            
            # z - soil height
            mid_x_right = right_piezo_x + piezo_width + 0.6
            ax.annotate('', xy=(mid_x_right, bottom_y), xytext=(mid_x_right, H2),
                       arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
            ax.text(mid_x_right+0.2, H2/2, 'z', 
                   fontsize=14, color='black', fontweight='bold', style='italic')
            
            # γ (gamma) - head loss
            dim_x = soil_x_start + soil_width + 1.8
            ax.annotate('', xy=(dim_x, TH_top), xytext=(dim_x, TH_bot),
                       arrowprops=dict(arrowstyle='<->', color=grad_color, lw=2))
            ax.text(dim_x+0.3, (TH_top+TH_bot)/2, 'γ', 
                   fontsize=14, color=grad_color, fontweight='bold', style='italic')
            
            # POINT A
            point_a_y = H2 - z
            ax.plot(soil_x_start + soil_width/2, point_a_y, 'ko', markersize=8)
            ax.text(soil_x_start + soil_width/2 + 0.3, point_a_y, 'A', 
                   fontsize=14, fontweight='bold')
            
            # DATUM LINE
            ax.hlines(-0.5, 0, soil_x_start + soil_width + 2.5, 
                     colors='black', linestyle='-.', linewidth=1)
            ax.text(0.5, -0.7, "Datum", fontsize=10, style='italic')
            
            # WATER LEVEL INDICATORS
            # Left tube water level
            ax.hlines(TH_top, left_piezo_x, left_piezo_x+piezo_width, 
                     colors='blue', linewidth=2)
            # Right tube water level
            ax.hlines(TH_bot, right_piezo_x, right_piezo_x+piezo_width, 
                     colors='blue', linewidth=2)
            
            # Plot settings
            ax.set_xlim(0, 7)
            ax.set_ylim(-1.5, max(TH_top, TH_bot) + 1.5)
            ax.set_aspect('equal')
            ax.axis('off')
            ax.set_title('Permeameter Setup', fontsize=12, fontweight='bold', pad=10)
            
            st.pyplot(fig)

        st.divider()

        # --- CALCULATION LOGIC ---
        if st.button("🚀 Calculate Effective Stress"):
            i = h_loss / H2 # Hydraulic Gradient
            
            # Determine Sign based on Flow Direction
            if "Downward" in flow_dir:
                sign_txt = "-"
                effect_txt = "Downward flow increases Effective Stress"
                sigma_prime_2 = z * (gamma_sat - gamma_w) + (i * z * gamma_w)
                formula_latex = r"\sigma' = z\gamma' + i z \gamma_w"
                u_val = ((H1 + z) - (i * z)) * gamma_w
                
            else:
                sign_txt = "+"
                effect_txt = "Upward flow decreases Effective Stress"
                sigma_prime_2 = z * (gamma_sat - gamma_w) - (i * z * gamma_w)
                formula_latex = r"\sigma' = z\gamma' - i z \gamma_w"
                u_val = ((H1 + z) + (i*z)) * gamma_w

            sigma_total = (H1 * gamma_w) + (z * gamma_sat)
            sigma_prime_1 = sigma_total - u_val

            st.success(f"**Condition:** {effect_txt}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Method 1: σ - u**")
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

# For testing
if __name__ == "__main__":
    app()
