import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ======================================
# 1. HELPER: TS 500 PARAMETERS & LOGIC
# ======================================
def get_k1_ts500(fck):
    """
    Returns equivalent stress block depth factor k1 per TS 500 (Slide 26).
    """
    if fck <= 25: return 0.85
    elif fck == 30: return 0.82
    elif fck == 35: return 0.79
    elif fck == 40: return 0.76
    elif fck == 45: return 0.73
    elif fck >= 50: return 0.70
    return 0.85 

def solve_quadratic_c(b, As, Es, epsilon_cu, d, fcd, k1):
    """
    Solves for c when steel does NOT yield (Slide 59).
    Equilibrium: Fc - Fs = 0 
    => 0.85 * fcd * b * k1 * c = As * Es * epsilon_cu * (d - c) / c
    Rearranging gives: A*c^2 + B*c + C = 0
    """
    # A * c^2 + B * c - D = 0
    A = 0.85 * fcd * b * k1
    B = As * Es * epsilon_cu
    C = - (As * Es * epsilon_cu * d)
    
    # Quadratic formula: (-B + sqrt(B^2 - 4AC)) / 2A
    delta = B**2 - 4 * A * C
    if delta < 0: return d/2 # Fallback safety
    c_sol = (-B + np.sqrt(delta)) / (2 * A)
    return c_sol

# ======================================
# 2. HELPER: DRAWING FUNCTIONS
# ======================================
def draw_beam_section(b, h, d, cover, num_bars, bar_dia):
    """Draws the physical cross-section of the beam"""
    fig, ax = plt.subplots(figsize=(4, 4))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    
    # Concrete section
    ax.add_patch(patches.Rectangle((0, 0), b, h, fill=True, facecolor='#e0e0e0', edgecolor='black', linewidth=2))
    
    # Rebar visualization
    padding = cover + bar_dia/2
    width_avail = b - 2*padding
    
    if num_bars == 1:
        x_positions = [b/2]
    else:
        gap = width_avail / (num_bars - 1)
        x_positions = [padding + i*gap for i in range(num_bars)]
        
    y_bar = cover + bar_dia/2 
    for x in x_positions:
        ax.add_patch(patches.Circle((x, y_bar), bar_dia/2, color="#d32f2f", zorder=10))
        
    # Markers
    ax.annotate(r"$b$", xy=(b/2, h+10), ha='center', color='black')
    ax.annotate(r"$h$", xy=(-10, h/2), ha='right', color='black')
    ax.annotate(r"$d$", xy=(b+20, y_bar), xytext=(b+20, h), arrowprops=dict(arrowstyle='<->'), ha='center')
    
    ax.set_xlim(-50, b + 50)
    ax.set_ylim(-50, h + 50)
    ax.axis('off')
    ax.set_aspect('equal')
    return fig

def draw_stress_strain_ts500(c, d, h, epsilon_s, epsilon_cu, fcd, k1, fs_final):
    """
    Draws 3 panels: Strain, Actual Stress (Parabolic), Equivalent Block (Rectangular).
    Ref: TS 500 Slide 26.
    """
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(10, 4))
    fig.patch.set_alpha(0)
    for ax in [ax1, ax2, ax3]: ax.patch.set_alpha(0)

    # Common Axis Setup
    for ax in [ax1, ax2, ax3]:
        ax.axvline(x=0, color='gray', linewidth=0.8) # Reference line
        ax.axhline(y=h, color='black', linewidth=1)  # Top of beam
        ax.axhline(y=0, color='black', linewidth=1)  # Bottom of beam
        ax.set_ylim(-0.1*h, 1.1*h)
        ax.axis('off')

    # --- 1. STRAIN PROFILE ---
    ax1.set_title("1. Strain", color="white", fontsize=10)
    y_na = h - c
    
    # Scale x-values for visibility
    scale_factor = 0.8 / max(epsilon_cu, abs(epsilon_s) + 1e-9)
    x_top = -epsilon_cu * scale_factor
    x_bot = epsilon_s * scale_factor
    
    ax1.plot([x_top, x_bot], [h, h-d], color='#2196F3', linewidth=2, marker='o', markersize=4)
    ax1.plot([x_top, 0], [h, h], color='#2196F3', linestyle='--')
    
    # Neutral Axis
    ax1.axhline(y=y_na, color='red', linestyle=':', linewidth=1)
    ax1.text(0, y_na + 5, f"NA (c={c:.0f})", color='red', fontsize=8)
    
    ax1.text(x_top, h+15, f"$\\epsilon_{{cu}}$\n{epsilon_cu}", ha='center', color='white', fontsize=8)
    ax1.text(x_bot, h-d-35, f"$\\epsilon_s$\n{epsilon_s:.4f}", ha='center', color='white', fontsize=8)

    # --- 2. ACTUAL STRESS PROFILE (Parabolic-Rectangular) ---
    ax2.set_title("2. Actual Stress", color="white", fontsize=10)
    
    # Generate points for the stress curve
    y_vals = np.linspace(h - c, h, 100)
    stress_vals = []
    
    # Concrete Model: Parabolic up to eps_c0 (0.002), then constant
    eps_c0 = 0.002
    
    for y in y_vals:
        dist_from_na = y - (h - c)
        eps_y = (dist_from_na / c) * epsilon_cu
        
        if eps_y < 0: 
            sigma = 0
        elif eps_y < eps_c0:
            sigma = fcd * (1 - (1 - eps_y/eps_c0)**2)
        else:
            sigma = fcd
        stress_vals.append(-sigma) 

    # Scale stress for plotting
    max_stress_display = 0.8
    stress_scale = max_stress_display / fcd
    x_stress = [s * stress_scale for s in stress_vals]
    
    # Fill the curve
    ax2.fill_betweenx(y_vals, x_stress, 0, facecolor='#90CAF9', alpha=0.6, edgecolor='#1565C0')
    ax2.text(-max_stress_display, h+15, f"$f_{{cd}}$\n{fcd:.1f} MPa", ha='center', color='white', fontsize=8)
    
    # Tension Steel Force Arrow
    ax2.arrow(0, h-d, 0.4, 0, head_width=15, head_length=0.1, color='#F44336', linewidth=2)

    # --- 3. EQUIVALENT BLOCK (Whitney) ---
    ax3.set_title("3. Equiv. Block", color="white", fontsize=10)
    
    a = k1 * c
    y_block_bot = h - a
    
    # Rectangular Block
    rect_width = 0.85 * fcd * stress_scale # Scaled visually
    rect = patches.Rectangle((-rect_width, y_block_bot), rect_width, a, 
                             facecolor='#EF9A9A', edgecolor='#D32F2F', alpha=0.7)
    ax3.add_patch(rect)
    
    # Force Vector Fc
    ax3.arrow(-rect_width/2, h - a/2, rect_width/2, 0, head_width=20, head_length=0.1, color='red', linewidth=2)
    ax3.text(-rect_width/2, h - a/2 + 10, "$F_c$", color='red', fontweight='bold', ha='center')
    
    # Force Vector Fs
    ax3.arrow(0, h-d, 0.5, 0, head_width=20, head_length=0.1, color='#F44336', linewidth=2)
    ax3.text(0.5, h-d+10, "$F_s$", color='#F44336', fontweight='bold', ha='center')
    
    # Dimension 'a'
    ax3.annotate(f"a={a:.0f}", xy=(0.1, h-a/2), xytext=(0.3, h-a/2),
                 arrowprops=dict(arrowstyle='-[, widthB=1.5', color='white'), color='white', fontsize=8)

    return fig

# ======================================
# 3. MAIN APP
# ======================================
def app():
    st.markdown("## TS 500: Flexural Analysis of Beams")
    st.caption("Singly Reinforced Rectangular Section Analysis")
    
    # --- INPUTS ---
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        st.subheader("1. Material Properties")
        st.caption("Partial Safety Factors: $\gamma_c=1.5, \gamma_s=1.15$")
        
        fck = st.selectbox("Concrete Class ($C$)", [20, 25, 30, 35, 40, 45, 50], index=2)
        fyk = st.selectbox("Steel Grade ($S$)", [220, 420, 500], index=1)
        
        # Design Strengths (TS 500)
        fcd = fck / 1.5
        fyd = fyk / 1.15
        
        st.info(f"**Design Values:**\n\n$f_{{cd}} = {fcd:.2f}$ MPa\n\n$f_{{yd}} = {fyd:.2f}$ MPa")

    with col2:
        st.subheader("2. Geometry")
        c1, c2 = st.columns(2)
        with c1:
            bw = st.number_input("Width ($b_w$) [mm]", value=300.0, step=50.0)
            h = st.number_input("Height ($h$) [mm]", value=500.0, step=50.0)
        with c2:
            cover = st.number_input("Effective Cover ($d'$)", value=40.0, step=5.0)
            d = h - cover
            st.write(f"Effective depth $d = {d:.1f}$ mm")
            
        st.subheader("3. Reinforcement")
        # Direct Area Input or Bar Selection
        input_method = st.radio("Input Method", ["Total Area ($A_s$)", "Bar Selection"], horizontal=True)
        if input_method == "Total Area ($A_s$)":
            As = st.number_input("Steel Area ($A_s$) [mm²]", value=1257.0) # approx 4phi20
            bar_dia = 20 # default for drawing
            num_bars = 4
        else:
            bar_dia = st.selectbox("Bar Diameter", [12, 14, 16, 20, 24, 28, 32], index=3)
            num_bars = st.number_input("Number of Bars", value=4, min_value=1)
            As = num_bars * np.pi * (bar_dia/2)**2
            st.write(f"Calculated $A_s = {As:.0f}$ mm²")

    st.markdown("---")

    # ======================================
    # 4. CALCULATIONS (TS 500 Logic)
    # ======================================
    
    # 1. Determine Parameters
    k1 = get_k1_ts500(fck)
    Es = 200000.0 # MPa
    epsilon_cu = 0.003
    epsilon_sy = fyd / Es
    
    # 2. Assume Yielding (Step 1 from Slide 48/59)
    # Force Equilibrium: Fc = Fs => 0.85 * fcd * bw * k1 * c = As * fyd
    c_yield = (As * fyd) / (0.85 * fcd * bw * k1)
    
    # 3. Check Assumption
    epsilon_s = epsilon_cu * (d - c_yield) / c_yield
    
    is_yielded = epsilon_s >= epsilon_sy
    
    # 4. Final Calculation based on state
    if is_yielded:
        c_final = c_yield
        fs_final = fyd
        calculation_mode = "Yielded (Ductile)"
    else:
        # Solve quadratic (Slide 59 Example 5 Logic)
        c_final = solve_quadratic_c(bw, As, Es, epsilon_cu, d, fcd, k1)
        epsilon_s = epsilon_cu * (d - c_final) / c_final
        fs_final = epsilon_s * Es
        calculation_mode = "Not Yielded (Brittle/Elastic)"

    # 5. Moment Capacity
    a_final = k1 * c_final
    # Mr = Fs * (d - a/2)  (Slide 48)
    Mr = (As * fs_final * (d - a_final/2)) * 1e-6 # kNm

    # ======================================
    # 5. VISUALIZATION & REPORT
    # ======================================
    col_viz, col_res = st.columns([1.2, 1])
    
    with col_viz:
        st.subheader("Section Status")
        tab1, tab2 = st.tabs(["Forces & Stresses", "Cross Section"])
        
        with tab1:
            fig_stress = draw_stress_strain_ts500(c_final, d, h, epsilon_s, epsilon_cu, fcd, k1, fs_final)
            st.pyplot(fig_stress)
            plt.close(fig_stress)
            
        with tab2:
            fig_sec = draw_beam_section(bw, h, d, cover, num_bars, bar_dia)
            st.pyplot(fig_sec)
            plt.close(fig_sec)
        
        st.success(f"**Moment Capacity ($M_r$): {Mr:.1f} kNm**")
        st.caption(f"Neutral Axis Depth $c = {c_final:.1f}$ mm")

    with col_res:
        st.subheader("Calculation Report")
        
        # Step 1: Material Constants
        st.markdown("**1. Design Constants**")
        st.latex(fr"f_{{cd}} = {fcd:.2f} \text{{ MPa}}, \quad f_{{yd}} = {fyd:.2f} \text{{ MPa}}")
        st.latex(fr"k_1 = {k1} \quad (\text{{for }} C{fck})")
        st.latex(fr"\epsilon_{{sy}} = {epsilon_sy:.5f}")

        # Step 2: Assumption Check
        st.markdown("**2. Force Equilibrium Check**")
        st.write(f"Assuming yield, calculated $c = {c_yield:.1f}$ mm.")
        
        st.markdown("**3. Strain Compatibility**")
        st.latex(fr"\epsilon_s = 0.003 \frac{{{d}-{c_yield:.1f}}}{{{c_yield:.1f}}} = \mathbf{{{epsilon_s:.5f}}}")
        
        if is_yielded:
            st.success(f"✅ $\epsilon_s \ge \epsilon_{{sy}}$")
            st.write("Assumption Correct: **Tension Steel Yields**.")
        else:
            st.error(f"⚠️ $\epsilon_s < \epsilon_{{sy}}$")
            st.write("Assumption Incorrect: **Compression Failure**.")
            st.write("Recalculating $c$ using quadratic equation...")
            st.latex(fr"c_{{new}} = {c_final:.1f} \text{{ mm}}")
            st.latex(fr"f_s = E_s \epsilon_s = {fs_final:.1f} \text{{ MPa}}")

        # Step 4: Moment
        st.markdown("**4. Final Moment ($M_r$)**")
        st.latex(fr"M_r = A_s f_s (d - \frac{{k_1 c}}{{2}})")
        st.latex(fr"M_r = {As:.0f} \cdot {fs_final:.1f} \cdot ({d} - \frac{{{k1}\cdot{c_final:.1f}}}{{2}}) \cdot 10^{{-6}}")
        st.latex(fr"M_r = \mathbf{{{Mr:.1f} \text{{ kNm}}}}")
        
        # K check
        K = (bw * d**2) / (Mr * 1e6)
        st.caption(f"K-value check: $K = bd^2/M_r = {K:.0f}$ mm²/N")

# Run
if __name__ == "__main__":
    app()
