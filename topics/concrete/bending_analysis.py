import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ==========================================
# 1. MATH ENGINE (TS 500 LOGIC)
# ==========================================
def get_ts500_properties(fck, fyk):
    """Returns design strengths and modulus."""
    gamma_c = 1.5
    gamma_s = 1.15
    fcd = fck / gamma_c
    fyd = fyk / gamma_s
    fctd = 0.35 * np.sqrt(fck) / gamma_c # Design Tensile Strength
    Es = 200000.0
    eps_cu = 0.003
    return fcd, fyd, fctd, Es, eps_cu

def get_k1(fck):
    """Equivalent Stress Block Factor k1"""
    if fck <= 25: return 0.85
    elif fck == 30: return 0.82
    elif fck == 35: return 0.79
    elif fck == 40: return 0.76
    elif fck == 45: return 0.73
    else: return 0.70

def solve_singly_capacity(b, d, As, fcd, fyd, Es, eps_cu, k1):
    """
    Calculates Mr, c, and strain state.
    """
    # 1. Force Equilibrium (Assume Yield)
    # T = C -> As * fyd = 0.85 * fcd * b * a
    # a = k1 * c
    
    # Solve for c assuming yield
    c = (As * fyd) / (0.85 * fcd * b * k1)
    
    # 2. Check Compatibility
    eps_s = eps_cu * (d - c) / c
    eps_y = fyd / Es
    
    status = "Yields (Ductile)"
    fs = fyd
    
    # 3. Adjust if not yielded
    if eps_s < eps_y:
        status = "Elastic (Brittle)"
        # Solve Quadratic: 0.85*fcd*b*k1*c^2 + As*Es*eps_cu*c - As*Es*eps_cu*d = 0
        A_q = 0.85 * fcd * b * k1
        B_q = As * Es * eps_cu
        C_q = - (As * Es * eps_cu * d)
        c = (-B_q + np.sqrt(B_q**2 - 4*A_q*C_q)) / (2*A_q)
        
        # Recalc stress
        eps_s = eps_cu * (d - c) / c
        fs = eps_s * Es
        
    a = k1 * c
    Mr = As * fs * (d - a/2) * 1e-6 # kNm
    return Mr, c, eps_s, status, fs

def check_bar_fit(b, cover, As_total):
    """
    Checks if bars fit in width b. 
    Assumes approx bar size (phi 20) for spacing check.
    """
    # Approx: Area of one 20mm bar is 314mm2
    num_bars = np.ceil(As_total / 314)
    phi_est = 20 
    stirrup_est = 10
    
    # Width required = 2*cover + 2*stirrup + n*phi + (n-1)*spacing
    # Min spacing = 20mm or phi
    req_spacing = max(20, phi_est)
    
    width_req = (2 * cover) + (2 * stirrup_est) + (num_bars * phi_est) + ((num_bars - 1) * req_spacing)
    
    if width_req > b:
        return False, f"⚠️ Bars may not fit! Est. Width {width_req:.0f}mm > {b}mm"
    return True, "✅ Bars fit comfortably."

# ==========================================
# 2. PLOTTING ENGINE
# ==========================================
def draw_analysis_diagram(b, h, d, c, As):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3))
    fig.patch.set_alpha(0); ax1.patch.set_alpha(0); ax2.patch.set_alpha(0)
    
    for ax in [ax1, ax2]:
        ax.set_ylim(-h*0.1, h*1.1)
        ax.axis('off')
        # Beam outline
        ax.plot([0, 0], [0, h], 'k', lw=1)
    
    # 1. Strain Profile
    ax1.set_title("Strain Profile")
    y_na = h - c
    ax1.plot([-1, 0], [h, h], 'b') # Top strain
    ax1.plot([-1, 1.5], [h, h-d], 'b-o') # Strain line
    ax1.plot([-2, 2], [y_na, y_na], 'r--', lw=1) # Neutral Axis
    ax1.text(0.1, y_na, f"NA (c={c:.1f})", color='red', fontsize=9)
    ax1.text(-1, h+10, "0.003", ha='center')
    
    # 2. Stress Block
    ax2.set_title("Internal Forces")
    k1 = 0.85 # approx for drawing
    a = k1 * c
    # Comp Block
    ax2.add_patch(patches.Rectangle((-0.5, h-a), 0.5, a, facecolor='#ffcccc', edgecolor='red'))
    ax2.text(-0.25, h-a/2, "C", color='red', ha='center', fontweight='bold')
    
    # Tension Arrow
    ax2.arrow(0, h-d, 0.5, 0, head_width=20, color='blue')
    ax2.text(0.6, h-d, "T", color='blue', ha='center', fontweight='bold')
    
    return fig

# ==========================================
# 3. WIZARD UI
# ==========================================
def app():
    st.title("TS 500 Flexure Solver")

    # --- STEP 1: CONTEXT ---
    col_setup, col_goal = st.columns(2)
    with col_setup:
        section_type = st.radio("Section Type", ["Singly Reinforced", "Doubly Reinforced"])
    
    with col_goal:
        if section_type == "Singly Reinforced":
            goal = st.selectbox("Professor's Question:", [
                "Find Capacity (Mr) & Neutral Axis (c)",
                "Design Steel Area (As)",
                "Find Concrete Class (fck)"
            ])
        else:
            goal = st.selectbox("Professor's Question:", ["Find Capacity (Mr)"])

    st.markdown("---")

    # --- STEP 2: DYNAMIC INPUTS ---
    data = {}
    
    # System Properties Row
    st.subheader("System Properties")
    c1, c2, c3, c4 = st.columns(4)
    data['b'] = c1.number_input("Width (b)", 300.0)
    data['h'] = c2.number_input("Height (h)", 500.0)
    data['cover'] = c3.number_input("Cover", 30.0)
    data['d'] = data['h'] - data['cover']
    
    fck = c4.selectbox("Concrete (C)", [20, 25, 30, 35, 40, 50], index=2)
    fyk = st.sidebar.selectbox("Steel (S)", [420, 500], index=0) # Sidebar for less freq items
    
    # Specific Inputs
    st.markdown(f"#### Variables for: {goal}")
    
    if section_type == "Singly Reinforced":
        if "Capacity" in goal:
            data['As'] = st.number_input("Provided Steel (As) [mm²]", value=1500.0)
        elif "Design" in goal:
            data['Md_target'] = st.number_input("Design Moment (Md) [kNm]", value=250.0)
        elif "Concrete" in goal:
            data['Md_target'] = st.number_input("Target Moment (Md) [kNm]", value=300.0)
            data['As'] = st.number_input("Provided Steel (As) [mm²]", value=2000.0)

    # --- STEP 3: SOLVE ---
    if st.button("Solve Problem", type="primary"):
        st.divider()
        
        # Prepare Math
        fcd, fyd, fctd, Es, eps_cu = get_ts500_properties(fck, fyk)
        k1 = get_k1(fck)
        
        # === LOGIC FOR SINGLY REINFORCED ===
        if section_type == "Singly Reinforced":
            
            # CASE A: FIND CAPACITY (Mr, c, epsilon)
            if "Capacity" in goal:
                Mr, c, eps_s, status, fs = solve_singly_capacity(data['b'], data['d'], data['As'], fcd, fyd, Es, eps_cu, k1)
                
                # Cracking Moment Check
                Ig = (data['b'] * data['h']**3) / 12
                yt = data['h'] / 2
                Mcr = (fctd * Ig / yt) * 1e-6
                
                # Bar Fit Check
                fits, msg = check_bar_fit(data['b'], data['cover'], data['As'])
                
                # RESULTS
                c1, c2 = st.columns([1, 1.5])
                with c1:
                    st.success(f"**Capacity Mr = {Mr:.1f} kNm**")
                    st.write(f"**Cracking Moment:** $M_{{cr}} = {Mcr:.1f}$ kNm")
                    
                    st.markdown("### Professor's Variables")
                    st.latex(fr"c = {c:.1f} \text{{ mm}}")
                    st.latex(fr"\epsilon_s = {eps_s:.5f}")
                    st.caption(f"Status: {status}")
                    
                    if fits: st.success(msg)
                    else: st.error(msg)
                    
                with c2:
                    st.pyplot(draw_analysis_diagram(data['b'], data['h'], data['d'], c, data['As']))

            # CASE B: DESIGN STEEL (As)
            elif "Design" in goal:
                # Iterative design
                Md_Nmm = data['Md_target'] * 1e6
                As_req = Md_Nmm / (fyd * 0.9 * data['d']) # Initial guess
                for _ in range(10): # Quick converge
                    a = (As_req * fyd) / (0.85 * fcd * data['b'])
                    As_req = Md_Nmm / (fyd * (data['d'] - a/2))
                
                st.success(f"**Required Steel As = {As_req:.0f} mm²**")
                
                # Suggest Bars
                n20 = int(np.ceil(As_req / 314))
                st.info(f"Suggestion: {n20} $\phi$ 20 bars ({n20*314} mm²)")
                
                # Check Min/Max
                rho = As_req / (data['b'] * data['d'])
                st.write(f"Steel Ratio $\\rho = {rho:.4f}$")
                if rho < 0.002: st.warning("⚠️ Below Minimum Steel!")
                if rho > 0.02: st.warning("⚠️ High Steel Ratio (Check spacing)")

            # CASE C: FIND CONCRETE
            elif "Concrete" in goal:
                # Simple loop to find fck
                found = False
                for try_fck in [20, 25, 30, 35, 40, 50]:
                    t_fcd = try_fck / 1.5
                    t_k1 = get_k1(try_fck)
                    Mr, _, _, _, _ = solve_singly_capacity(data['b'], data['d'], data['As'], t_fcd, fyd, Es, eps_cu, t_k1)
                    if Mr >= data['Md_target']:
                        st.success(f"**Required Concrete: C{try_fck}**")
                        st.write(f"Capacity with C{try_fck} is {Mr:.1f} kNm")
                        found = True
                        break
                if not found:
                    st.error("Even C50 is not enough. Increase Section Dimensions.")

if __name__ == "__main__":
    app()
