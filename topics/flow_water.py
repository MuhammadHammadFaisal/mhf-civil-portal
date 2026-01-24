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

# --- DYNAMIC MATPLOTLIB DIAGRAM (RESERVOIR STYLE) ---
        with col_plot:
            fig, ax = plt.subplots(figsize=(7, 8))
            
            # --- COORDINATES ---
            # Soil Box (Center)
            soil_w = 2.5
            soil_h = H2
            soil_x = 3.0
            soil_y = 2.0  # Elevate soil so we can draw tubes below
            
            # Water Heights (Relative to Datum at y=0)
            # In your sketch: 
            # 'y' is the total head at the top (measured from datum)
            # 'x' is the total head at the bottom (measured from datum)
            # Let's map inputs: H1 = Head Difference, H2 = Soil Height.
            # We need to assume a Datum. Let's say Datum is at bottom of soil tube.
            
            # For drawing, let's just use the visual proportions from your sketch
            # Top Water Level (Head y)
            wl_top = soil_y + soil_h + H1 
            # Bottom Water Level (Head x) -> If flow is downward, x < y
            # If flow is upward, x > y.
            if "Downward" in flow_dir:
                wl_bot = wl_top - h_loss
            else:
                wl_bot = wl_top + h_loss
                
            # --- 1. DRAW SOIL CHAMBER ---
            # Main Box
            ax.add_patch(patches.Rectangle((soil_x, soil_y), soil_w, soil_h, 
                                           facecolor='#E3C195', hatch='...', edgecolor='black', lw=2))
            ax.text(soil_x + soil_w/2, soil_y + soil_h/2, "SOIL", ha='center', fontweight='bold')
            
            # --- 2. TOP RESERVOIR (Head 'y') ---
            # Neck connecting soil to top tank
            neck_w = 0.8
            neck_x = soil_x + (soil_w - neck_w)/2
            neck_h = wl_top - (soil_y + soil_h) - 0.5 # Stop a bit before water level
            
            # Draw Neck
            ax.add_patch(patches.Rectangle((neck_x, soil_y + soil_h), neck_w, neck_h + 1.5, 
                                           facecolor='#D6EAF8', edgecolor='black', lw=2))
            
            # Draw Top Tank (Wide)
            tank_w = 2.0
            tank_x = soil_x + (soil_w - tank_w)/2
            tank_y = wl_top - 0.5
            tank_h = 1.0
            
            # Tank Box
            ax.add_patch(patches.Rectangle((tank_x, tank_y), tank_w, tank_h, 
                                           facecolor='white', edgecolor='black', lw=2))
            # Water in Tank
            ax.add_patch(patches.Rectangle((tank_x, tank_y), tank_w, 0.5, 
                                           facecolor='#D6EAF8'))
            # Water Surface Line
            ax.plot([tank_x, tank_x + tank_w], [wl_top, wl_top], 'b-', lw=2)
            ax.plot(tank_x + tank_w/2, wl_top, marker='v', color='blue')

            # --- 3. LEFT RESERVOIR (Head 'x') ---
            # Connected to bottom of soil
            # Tube coordinates
            tube_w = 0.6
            tube_x_start = soil_x + (soil_w - tube_w)/2
            tube_y_start = soil_y
            
            left_tank_x = 0.5
            
            # Draw "U-Tube" path
            # Vertical down from soil
            ax.add_patch(patches.Rectangle((tube_x_start, soil_y - 1.0), tube_w, 1.0, 
                                           facecolor='#D6EAF8', edgecolor='black', lw=2)) # Down segment
            
            # Horizontal to left
            ax.add_patch(patches.Rectangle((left_tank_x + tank_w/2 - tube_w/2, soil_y - 1.0), 
                                           tube_x_start - (left_tank_x + tank_w/2 - tube_w/2) + tube_w, tube_w, 
                                           facecolor='#D6EAF8', edgecolor='black', lw=2))
            
            # Vertical up to Left Tank
            up_tube_x = left_tank_x + tank_w/2 - tube_w/2
            ax.add_patch(patches.Rectangle((up_tube_x, soil_y - 1.0), tube_w, wl_bot - (soil_y - 1.0), 
                                           facecolor='#D6EAF8', edgecolor='black', lw=2))

            # Left Tank (Wide)
            l_tank_y = wl_bot - 0.5
            ax.add_patch(patches.Rectangle((left_tank_x, l_tank_y), tank_w, tank_h, 
                                           facecolor='white', edgecolor='black', lw=2))
            # Water in Left Tank
            ax.add_patch(patches.Rectangle((left_tank_x, l_tank_y), tank_w, 0.5, 
                                           facecolor='#D6EAF8'))
            # Water Surface Line
            ax.plot([left_tank_x, left_tank_x + tank_w], [wl_bot, wl_bot], 'b-', lw=2)
            ax.plot(left_tank_x + tank_w/2, wl_bot, marker='v', color='blue')

            # --- 4. DIMENSIONS (Matching Sketch) ---
            # Datum Line at bottom of U-tube
            datum_y = soil_y - 1.0
            ax.plot([-0.5, 7], [datum_y, datum_y], 'k-.')
            ax.text(0, datum_y - 0.3, "Datum")

            # Dimension 'x' (Left Head)
            ax.annotate('', xy=(left_tank_x - 0.3, datum_y), xytext=(left_tank_x - 0.3, wl_bot), arrowprops=dict(arrowstyle='<->'))
            ax.text(left_tank_x - 0.6, (datum_y + wl_bot)/2, "x", fontsize=14, fontweight='bold')
            
            # Dimension 'y' (Top Head)
            dim_x_right = soil_x + soil_w + 1.0
            ax.annotate('', xy=(dim_x_right, datum_y), xytext=(dim_x_right, wl_top), arrowprops=dict(arrowstyle='<->'))
            ax.text(dim_x_right + 0.2, (datum_y + wl_top)/2, "y", fontsize=14, fontweight='bold')
            
            # Dimension 'z' (Soil Height)
            ax.annotate('', xy=(soil_x + soil_w + 0.3, soil_y), xytext=(soil_x + soil_w + 0.3, soil_y + soil_h), arrowprops=dict(arrowstyle='<->'))
            ax.text(soil_x + soil_w + 0.4, soil_y + soil_h/2, "z", fontsize=12)

            # Dimension 'A' (Point Height)
            pt_A_y = soil_y + (soil_h - z) # z input is depth from top, so height from bottom is H-z
            # Wait, in sketch 'A' is height from bottom.
            # Let's verify 'z' input slider. The slider says "Depth of Point C".
            # If slider value is 'depth', then height A = soil_h - depth.
            height_A = soil_h - z
            
            # Draw Point A
            ax.scatter(soil_x + soil_w/2, soil_y + height_A, color='red', zorder=5)
            ax.text(soil_x + soil_w/2 + 0.2, soil_y + height_A, "Point A", color='red', fontweight='bold')
            
            # Draw dimension A
            ax.annotate('', xy=(soil_x + soil_w/2, soil_y), xytext=(soil_x + soil_w/2, soil_y + height_A), 
                        arrowprops=dict(arrowstyle='<->', color='red'))
            ax.text(soil_x + soil_w/2 + 0.1, soil_y + height_A/2, "A", color='red')

            ax.set_xlim(-1, 8)
            ax.set_ylim(datum_y - 1, wl_top + 1)
            ax.axis('off')
            st.pyplot(fig)

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
