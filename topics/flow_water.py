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

# --- DYNAMIC MATPLOTLIB DIAGRAM (CORRECTED DATUM & VALUES) ---
        with col_plot:
            fig, ax = plt.subplots(figsize=(7, 8))
            
            # --- 1. COORDINATE SYSTEM ---
            # We set the Datum (y=0) at the BOTTOM of the soil
            soil_w = 2.5
            soil_h = H2  # Total height of soil
            soil_x = 3.0 # X-position of soil box
            datum_y = 0.0 # Datum is exactly at bottom of soil
            
            # --- 2. CALCULATE HEAD VALUES (Relative to Datum) ---
            # y = Total Head at Top (Elevation Head H2 + Pressure Head H1)
            val_y = H2 + H1
            
            # x = Total Head at Bottom
            # Downward Flow: Head drops from Top to Bottom (x < y)
            # Upward Flow: Head drops from Bottom to Top (x > y)
            if "Downward" in flow_dir:
                val_x = val_y - h_loss
            else:
                val_x = val_y + h_loss
                
            # Point A (Height from Bottom)
            # We need to interpret the slider 'z' as 'Height A' or invert it
            # Let's use the slider value 'z' as the depth from top for calculation (Method 2), 
            # BUT for the diagram, let's calculate the Height A from bottom.
            # Height A = Total Soil Height - Depth z
            height_A = H2 - z 

            # --- 3. DRAWING SOIL CHAMBER ---
            # Main Box (Bottom at datum_y)
            ax.add_patch(patches.Rectangle((soil_x, datum_y), soil_w, soil_h, 
                                           facecolor='#E3C195', hatch='...', edgecolor='black', lw=2))
            ax.text(soil_x + soil_w/2, datum_y + soil_h/2, "SOIL", ha='center', fontweight='bold', fontsize=12)
            
            # --- 4. TOP RESERVOIR (Head y) ---
            # Neck
            neck_w = 0.8
            neck_x = soil_x + (soil_w - neck_w)/2
            # Tank
            tank_w = 2.0
            tank_x = soil_x + (soil_w - tank_w)/2
            tank_y_base = val_y - 0.5 # Start tank slightly below water level
            
            # Draw Neck
            ax.add_patch(patches.Rectangle((neck_x, datum_y + soil_h), neck_w, (tank_y_base - (datum_y + soil_h)) + 0.1, 
                                           facecolor='#D6EAF8', edgecolor='black', lw=2))
            
            # Draw Top Tank
            ax.add_patch(patches.Rectangle((tank_x, tank_y_base), tank_w, 1.0, 
                                           facecolor='white', edgecolor='black', lw=2))
            # Water in Tank
            ax.add_patch(patches.Rectangle((tank_x, tank_y_base), tank_w, 0.5, 
                                           facecolor='#D6EAF8'))
            # Water Level Line (y)
            ax.plot([tank_x, tank_x + tank_w], [val_y, val_y], 'b-', lw=2)
            ax.plot(tank_x + tank_w/2, val_y, marker='v', color='blue')

            # --- 5. LEFT RESERVOIR (Head x) ---
            # Connected to bottom (Datum)
            tube_w = 0.6
            left_tank_x = 0.5
            
            # U-Tube Path
            # 1. Down from soil bottom
            ax.add_patch(patches.Rectangle((soil_x + (soil_w-tube_w)/2, datum_y - 1.0), tube_w, 1.0, 
                                           facecolor='#D6EAF8', edgecolor='black', lw=2))
            # 2. Horizontal
            ax.add_patch(patches.Rectangle((left_tank_x + tank_w/2 - tube_w/2, datum_y - 1.0), 
                                           (soil_x + (soil_w-tube_w)/2) - (left_tank_x + tank_w/2 - tube_w/2) + tube_w, tube_w, 
                                           facecolor='#D6EAF8', edgecolor='black', lw=2))
            # 3. Up to Left Tank
            up_tube_x = left_tank_x + tank_w/2 - tube_w/2
            ax.add_patch(patches.Rectangle((up_tube_x, datum_y - 1.0), tube_w, (val_x - 0.5) - (datum_y - 1.0) + 0.1, 
                                           facecolor='#D6EAF8', edgecolor='black', lw=2))
            
            # Left Tank Box
            l_tank_y_base = val_x - 0.5
            ax.add_patch(patches.Rectangle((left_tank_x, l_tank_y_base), tank_w, 1.0, 
                                           facecolor='white', edgecolor='black', lw=2))
            # Water in Left Tank
            ax.add_patch(patches.Rectangle((left_tank_x, l_tank_y_base), tank_w, 0.5, 
                                           facecolor='#D6EAF8'))
            # Water Level Line (x)
            ax.plot([left_tank_x, left_tank_x + tank_w], [val_x, val_x], 'b-', lw=2)
            ax.plot(left_tank_x + tank_w/2, val_x, marker='v', color='blue')

            # --- 6. DIMENSIONS & VALUES ---
            
            # DATUM LINE
            ax.plot([-0.5, 8], [datum_y, datum_y], 'k-.', lw=1)
            ax.text(soil_x + soil_w + 0.5, datum_y, "Datum (z=0)", va='center', fontsize=10, style='italic')

            # Dimension y (Top Head)
            dim_x_right = soil_x + soil_w + 1.2
            ax.annotate('', xy=(dim_x_right, datum_y), xytext=(dim_x_right, val_y), arrowprops=dict(arrowstyle='<->'))
            ax.text(dim_x_right + 0.1, val_y/2, f"y\n{val_y:.1f}m", fontsize=11, fontweight='bold', ha='left')

            # Dimension x (Bottom Head)
            ax.annotate('', xy=(left_tank_x - 0.3, datum_y), xytext=(left_tank_x - 0.3, val_x), arrowprops=dict(arrowstyle='<->'))
            ax.text(left_tank_x - 0.8, val_x/2, f"x\n{val_x:.1f}m", fontsize=11, fontweight='bold', ha='right')

            # Dimension z (Soil Height) - Note: In your sketch 'z' labeled the soil height
            ax.annotate('', xy=(soil_x + soil_w + 0.2, datum_y), xytext=(soil_x + soil_w + 0.2, datum_y + soil_h), arrowprops=dict(arrowstyle='<->'))
            ax.text(soil_x + soil_w + 0.3, soil_h/2, f"z (Soil)\n{H2:.1f}m", fontsize=10)

            # Point A (Height from Bottom)
            ax.scatter(soil_x + soil_w/2, datum_y + height_A, color='red', zorder=5, s=80)
            ax.text(soil_x + soil_w/2 + 0.2, datum_y + height_A, f"Point A", color='red', fontweight='bold')
            
            # Dimension A (From Bottom)
            ax.annotate('', xy=(soil_x + soil_w/2, datum_y), xytext=(soil_x + soil_w/2, datum_y + height_A), 
                        arrowprops=dict(arrowstyle='<->', color='red'))
            ax.text(soil_x + soil_w/2 + 0.1, height_A/2, f"A = {height_A:.1f}m", color='red', fontweight='bold')

            ax.set_xlim(-1.5, 9)
            ax.set_ylim(datum_y - 1.5, max(val_x, val_y) + 1)
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
