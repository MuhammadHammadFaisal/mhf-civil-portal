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

# --- DYNAMIC MATPLOTLIB DIAGRAM (PROFESSIONAL TEXTBOOK STYLE) ---
        with col_plot:
            fig, ax = plt.subplots(figsize=(6, 7))
            
            # --- SETUP COORDINATES ---
            soil_w = 3.5
            soil_x = 2.0
            S_bot = 0.0
            S_top = H2
            W_top = S_top + H1
            
            # Calculate Head Levels
            TH_top = W_top
            if "Downward" in flow_dir:
                TH_bot = TH_top - h_loss
                grad_color = '#E74C3C' # Red for loss
                flow_sym = "⬇️"
            else:
                TH_bot = TH_top + h_loss
                grad_color = '#27AE60' # Green for upward gain
                flow_sym = "⬆️"

            # --- 1. DRAW SOIL COLUMN & COMPONENTS ---
            # Main Glass Cylinder (Behind everything)
            ax.add_patch(patches.Rectangle((soil_x, -0.5), soil_w, S_top + H1 + 1.5, 
                                           facecolor='#F8F9F9', edgecolor='#2C3E50', linewidth=2.5))
            
            # Soil Specimen with professional hatching
            rect_soil = patches.Rectangle((soil_x, S_bot), soil_w, H2, 
                                           facecolor='#D2B48C', hatch='...', edgecolor='#5D4037', alpha=0.9, linewidth=1.5)
            ax.add_patch(rect_soil)
            
            # Porous Stones (Top & Bottom)
            ax.add_patch(patches.Rectangle((soil_x, S_bot-0.2), soil_w, 0.2, facecolor='#7F8C8D', hatch='///', edgecolor='black'))
            ax.add_patch(patches.Rectangle((soil_x, S_top), soil_w, 0.2, facecolor='#7F8C8D', hatch='///', edgecolor='black'))

            # Water Layer Above Soil
            ax.add_patch(patches.Rectangle((soil_x, S_top+0.2), soil_w, H1-0.2, facecolor='#AED6F1', alpha=0.6))

            # --- 2. PIEZOMETER STANDPIPES ---
            # Left Piezometer (Connected to Top of Soil)
            px_left = soil_x - 1.5
            ax.add_patch(patches.Rectangle((px_left, S_bot), 0.4, TH_top + 0.5, facecolor='white', edgecolor='black', alpha=0.3))
            ax.add_patch(patches.Rectangle((px_left, S_bot), 0.4, TH_top, facecolor='#3498DB', alpha=0.5))
            ax.plot([px_left, px_left+0.4], [TH_top, TH_top], 'b-', lw=2) # Water surface
            ax.plot(px_left+0.2, TH_top, marker='v', color='blue', markersize=8) # Triangle
            
            # Right Piezometer (Connected to Bottom of Soil)
            px_right = soil_x + soil_w + 1.1
            ax.add_patch(patches.Rectangle((px_right, S_bot), 0.4, TH_bot + 0.5, facecolor='white', edgecolor='black', alpha=0.3))
            ax.add_patch(patches.Rectangle((px_right, S_bot), 0.4, TH_bot, facecolor='#3498DB', alpha=0.5))
            ax.plot([px_right, px_right+0.4], [TH_bot, TH_bot], 'b-', lw=2)
            ax.plot(px_right+0.2, TH_bot, marker='v', color='blue', markersize=8)

            # Connections
            ax.plot([px_left+0.4, soil_x], [S_top+0.1, S_top+0.1], 'k-', lw=1.5) # Top connection
            ax.plot([soil_x+soil_w, px_right], [S_bot-0.1, S_bot-0.1], 'k-', lw=1.5) # Bottom connection

            # --- 3. THE "TEACHING" LINE (Hydraulic Gradient) ---
            ax.plot([px_left+0.2, px_right+0.2], [TH_top, TH_bot], color=grad_color, linestyle='--', lw=2.5)
            
            # Head Loss Dimension (h)
            dim_x = px_right + 0.8
            ax.annotate('', xy=(dim_x, TH_top), xytext=(dim_x, TH_bot), arrowprops=dict(arrowstyle='<->', lw=2, color=grad_color))
            ax.text(dim_x+0.2, (TH_top+TH_bot)/2, f'h = {h_loss}m', color=grad_color, fontweight='bold', va='center')

            # --- 4. DIMENSIONS & LABELS ---
            # Soil Height (L)
            ax.annotate('', xy=(soil_x-0.5, S_bot), xytext=(soil_x-0.5, S_top), arrowprops=dict(arrowstyle='<->', color='black'))
            ax.text(soil_x-0.6, (S_bot+S_top)/2, f'L = {H2}m', rotation=90, va='center', ha='right')
            
            # Point A Indicator
            y_A = S_top - z
            ax.scatter(soil_x + soil_w/2, y_A, color='red', s=100, edgecolor='black', zorder=5)
            ax.text(soil_x + soil_w/2 + 0.3, y_A, 'Point A', color='red', fontweight='bold', fontsize=12)

            # Datum Line
            ax.axhline(S_bot-0.1, ls='-.', color='black', alpha=0.5)
            ax.text(soil_x-1.4, S_bot-0.4, "DATUM (Elev=0)", style='italic', fontsize=9)

            # Flow Arrow
            ax.text(soil_x + soil_w/2, W_top + 0.5, f"FLOW {flow_sym}", ha='center', fontweight='bold', color='#2980B9', fontsize=14)

            # Final Polish
            ax.set_xlim(px_left - 1, dim_x + 1.5)
            ax.set_ylim(-1, max(TH_top, TH_bot) + 2)
            ax.set_aspect('equal')
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
