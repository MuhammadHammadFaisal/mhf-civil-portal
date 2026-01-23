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
            fig, ax = plt.subplots(figsize=(6, 7))
            
            # Dimensions
            W = 3.0       # Width of soil sample
            H_s = H_soil
            H_w = H_water
            
           # ================= TEXTBOOK-STYLE PERMEAMETER =================

# --- SOIL BOX ---
soil_x = 2.0
soil_y = 0.0
soil_w = 3.0
soil_h = H_s

ax.add_patch(
    patches.Rectangle(
        (soil_x, soil_y),
        soil_w,
        soil_h,
        edgecolor='black',
        facecolor='none',
        linewidth=2
    )
)
ax.text(soil_x + soil_w/2, soil_h/2, "SOIL",
        ha='center', va='center', fontsize=12)

# --- TOP RESERVOIR ---
ax.add_patch(
    patches.Rectangle(
        (soil_x, soil_h + 1),
        soil_w,
        1,
        edgecolor='black',
        facecolor='none',
        linewidth=2
    )
)
ax.plot(
    [soil_x + 0.2, soil_x + soil_w - 0.2],
    [soil_h + 1.6, soil_h + 1.6],
    'k'
)

# --- LEFT RESERVOIR ---
ax.add_patch(
    patches.Rectangle(
        (0.4, soil_h + 0.5),
        1.6,
        1,
        edgecolor='black',
        facecolor='none',
        linewidth=2
    )
)
ax.plot([0.6, 1.8], [soil_h + 1.1, soil_h + 1.1], 'k')

# --- PIPES ---
ax.plot([soil_x + soil_w/2, soil_x + soil_w/2],
        [soil_h + 1, soil_h], 'k', linewidth=2)

ax.plot([1.2, 1.2], [soil_h + 0.5, 0.3], 'k', linewidth=2)
ax.plot([1.2, soil_x], [0.3, 0.3], 'k', linewidth=2)

# --- HEAD LEVELS ---
wl_top = soil_h + 1.6
X_level = soil_h - 2
Y_level = 0

ax.hlines(wl_top, 0, 7, linestyles='dashed')
ax.text(7.1, wl_top, "Top head")

ax.hlines(X_level, 0, 7, linestyles='dashed')
ax.text(7.1, X_level, "X–X")

ax.hlines(Y_level, 0, 7, linestyles='dashed')
ax.text(7.1, Y_level, "Y–Y (Datum)")

# --- DIMENSIONS ---
ax.annotate("2 m", xy=(6.5, wl_top), xytext=(6.5, X_level),
            arrowprops=dict(arrowstyle='<->'))
ax.annotate("4 m", xy=(6.5, X_level), xytext=(6.5, Y_level),
            arrowprops=dict(arrowstyle='<->'))

# --- FLOW LABEL ---
flow_symbol = r'$\downarrow$' if "Downward" in flow_dir else r'$\uparrow$'
ax.text(soil_x + soil_w/2, soil_h/2,
        f"FLOW {flow_symbol}",
        ha='center', va='center', fontsize=12, fontweight='bold')

# ================= END TEXTBOOK DIAGRAM =================

            # Settings
            ax.set_xlim(-1, W+4)
            ax.set_ylim(-1, max(wl_top, wl_bot) + 2)
            ax.axis('off')
            ax.set_title("Permeameter Setup", fontsize=14)
            
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
