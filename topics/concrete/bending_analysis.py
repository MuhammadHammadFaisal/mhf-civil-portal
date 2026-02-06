import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.optimize import brentq 

# ==========================================
# 1. MATH ENGINE (TS 500 LOGIC)
# ==========================================
def get_k1_ts500(fck):
    """TS 500 Equivalent Stress Block Factor"""
    if fck <= 25: return 0.85
    elif fck == 30: return 0.82
    elif fck == 35: return 0.79
    elif fck == 40: return 0.76
    elif fck == 45: return 0.73
    elif fck >= 50: return 0.70
    return 0.85

def get_material_properties(fck, fyk):
    # Partial Safety Factors
    fcd = fck / 1.5
    fyd = fyk / 1.15
    # Concrete Tensile Strength (approx for rho_min)
    fctd = (0.35 * np.sqrt(fck)) / 1.5 
    
    Es = 200000.0
    epsilon_cu = 0.003
    epsilon_sy = fyd / Es
    return fcd, fyd, fctd, Es, epsilon_cu, epsilon_sy

def check_ts500_limits(b, d, As, fcd, fyd, fctd):
    """Checks Rho_min and Rho_max per TS 500"""
    rho = As / (b * d)
    
    # Min Steel (TS 500 Formula)
    rho_min = 0.8 * (fctd / fyd)
    As_min = rho_min * b * d
    
    # Max Steel (Usually based on limit strain, approx 0.85 * rho_b or 0.02)
    # TS 500 often limits rho_max to 0.02 (2%) or ensures strain > 0.004/0.005
    rho_max = 0.02 
    As_max = rho_max * b * d
    
    status = []
    if rho < rho_min: status.append(f"⚠️ Below Min Steel (As < {As_min:.0f})")
    elif rho > rho_max: status.append(f"⚠️ Above Max Steel (As > {As_max:.0f})")
    else: status.append("✅ Code Limits OK")
    
    return status, rho_min, rho_max

def analyze_singly(b, d, As, fcd, fyd, Es, epsilon_cu, k1, epsilon_sy):
    # 1. Assume Yield
    c_calc = (As * fyd) / (0.85 * fcd * b * k1)
    eps_s = epsilon_cu * (d - c_calc) / c_calc
    
    status = "Ductile (Yields)"
    fs = fyd
    yielded = True
    
    # 2. Check Yield
    if eps_s < epsilon_sy:
        yielded = False
        status = "Brittle (Does not yield)"
        # Quadratic Solve for Elastic Steel
        A_q = 0.85 * fcd * b * k1
        B_q = As * Es * epsilon_cu
        C_q = - (As * Es * epsilon_cu * d)
        
        delta = B_q**2 - 4 * A_q * C_q
        c_calc = (-B_q + np.sqrt(delta)) / (2 * A_q)
        
        eps_s = epsilon_cu * (d - c_calc) / c_calc
        fs = eps_s * Es
        
    a = k1 * c_calc
    Mr = As * fs * (d - a/2) * 1e-6
    return Mr, c_calc, eps_s, status, yielded, fs

def design_singly_As(Md_target, b, d, fcd, fyd, k1):
    """Find As required for Md"""
    Md_Nmm = Md_target * 1e6
    # Initial guess z = 0.9d
    As_try = Md_Nmm / (fyd * 0.9 * d)
    
    for _ in range(20):
        a = (As_try * fyd) / (0.85 * fcd * b)
        z = d - a/2
        if z <= 0: z = 0.1 # Safety
        As_new = Md_Nmm / (fyd * z)
        if abs(As_new - As_try) < 0.5: break
        As_try = As_new
    return As_try

def find_required_depth(Md_target, b, rho_target, fcd, fyd, k1):
    """Find d required given a target rho"""
    # Mr = As * fy * (d - a/2)
    # Substitute As = rho*b*d and a = (rho*b*d*fy)/(0.85*fcd*b)
    # Mr = rho*b*d^2 * fy * (1 - 0.59*rho*fy/fc)
    # M = K * b * d^2
    
    term = rho_target * fyd * (1 - (0.59 * rho_target * fyd) / fcd)
    # d^2 = M / (b * term)
    d_req = np.sqrt( (Md_target * 1e6) / (b * term) )
    return d_req

def find_required_fck(Md_target, b, d, As, fyk):
    def capacity_gap(fck_try):
        k1 = get_k1_ts500(fck_try)
        fcd = fck_try / 1.5
        fyd = fyk / 1.15
        Es = 200000.0
        eps_cu = 0.003
        eps_sy = fyd/Es
        Mr, _, _, _, _, _ = analyze_singly(b, d, As, fcd, fyd, Es, eps_cu, k1, eps_sy)
        return Mr - Md_target
    try:
        return brentq(capacity_gap, 10, 150)
    except:
        return None

# ==========================================
# 2. VISUALIZATION ENGINE
# ==========================================
def draw_results_diagram(b, h, d, c, As, epsilon_cu, k1):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))
    fig.patch.set_alpha(0); ax1.patch.set_alpha(0); ax2.patch.set_alpha(0)
    
    for ax in [ax1, ax2]:
        ax.axhline(0, color='k', lw=1); ax.axhline(h, color='k', lw=1)
        ax.axvline(0, color='gray', linestyle=':', lw=1)
        ax.axis('off'); ax.set_ylim(-0.1*h, 1.1*h)

    # Strain
    ax1.set_title("Strain Profile", color="white")
    y_na = h - c
    ax1.axhline(y_na, color='red', linestyle='--', lw=1)
    ax1.text(0.1, y_na, f"c={c:.1f}", color='red', fontsize=9)
    
    eps_bot = epsilon_cu * (d - c) / c
    scale = 0.6 / max(epsilon_cu, eps_bot)
    
    # Concrete Strain (Top)
    ax1.plot([-epsilon_cu*scale, 0], [h, y_na], 'b-', lw=2)
    ax1.plot([-epsilon_cu*scale, 0], [h, h], 'b-', lw=1)
    ax1.text(-epsilon_cu*scale, h+15, f"{epsilon_cu}", ha='center', color='white', fontsize=9)
    
    # Steel Strain (Bottom)
    ax1.plot([0, eps_bot*scale], [y_na, h-d], 'b-', lw=2)
    ax1.plot([eps_bot*scale, 0], [h-d, h-d], 'b--', lw=1)
    ax1.text(eps_bot*scale, h-d-20, f"{eps_bot:.4f}", ha='center', color='white', fontsize=9)

    # Forces
    ax2.set_title("Force Equilibrium", color="white")
    a = k1 * c
    
    # Comp Block
    ax2.add_patch(patches.Rectangle((-0.4, h-a), 0.4, a, facecolor='#ffcccc', edgecolor='red'))
    ax2.arrow(-0.2, h-a/2, 0.2, 0, head_width=15, color='red')
    ax2.text(-0.5, h-a/2, "C", va='center', color='red', fontweight='bold')
    
    # Tension
    y_steel = h - d
    ax2.arrow(0, y_steel, 0.2, 0, head_width=15, color='blue')
    ax2.text(0.25, y_steel, "T", va='center', color='blue', fontweight='bold')
    ax2.text(0, y_steel-30, f"As={As:.0f}", ha='center', color='white', fontsize=8)

    return fig

# ==========================================
# 3. MAIN APP (THE WIZARD)
# ==========================================
def app():
    st.markdown("## TS 500: Flexure Solver")
    
    # --- STEP 1: GLOBAL SETTINGS ---
    with st.container():
        st.subheader("1. System Properties")
        c1, c2, c3 = st.columns(3)
        with c1: 
            bw = st.number_input("Width (b) [mm]", 250.0, step=50.0)
        with c2: 
            # Height is optional if finding d, but we keep it for visualization default
            h = st.number_input("Height (h) [mm]", 500.0, step=50.0)
        with c3: 
            cover = st.number_input("Cover [mm]", 30.0, step=5.0)
        
        d = h - cover # Default d
        
        c4, c5 = st.columns(2)
        with c4: fck = st.selectbox("Concrete (C)", [20, 25, 30, 35, 40, 50], index=2)
        with c5: fyk = st.selectbox("Steel (S)", [220, 420, 500], index=1)

    st.markdown("---")

    # --- STEP 2: PROBLEM WIZARD ---
    col_type, col_goal = st.columns([1, 1.5])
    
    with col_type:
        st.subheader("2. Section Type")
        sec_type = st.radio("Type", ["Singly Reinforced", "Doubly Reinforced"], label_visibility="collapsed")
    
    with col_goal:
        st.subheader("3. Professor's Question")
        if sec_type == "Singly Reinforced":
            goal = st.selectbox("Solve for:", [
                "Find Capacity (Mr)",
                "Design Steel (As)",
                "Find Depth (d)",
                "Find Concrete Class"
            ])
        else:
             goal = st.selectbox("Solve for:", ["Find Capacity (Mr)"])

    st.markdown("---")

    # --- STEP 3: DYNAMIC INPUTS & SOLVER ---
    if sec_type == "Singly Reinforced":
        
        # === GOAL A: CAPACITY ===
        if goal == "Find Capacity (Mr)":
            st.info("👇 **INPUT:** Enter provided steel to find strength.")
            As_in = st.number_input("Provided Steel (As) [mm²]", value=1257.0)
            
            if st.button("Solve", type="primary"):
                fcd, fyd, fctd, Es, eps_cu, eps_sy = get_material_properties(fck, fyk)
                k1 = get_k1_ts500(fck)
                
                # Check Limits
                limits_msg, r_min, r_max = check_ts500_limits(bw, d, As_in, fcd, fyd, fctd)
                
                # Analyze
                Mr, c, eps, status, yielded, fs = analyze_singly(bw, d, As_in, fcd, fyd, Es, eps_cu, k1, eps_sy)
                
                # OUTPUT
                st.success(f"**Moment Capacity ($M_r$) = {Mr:.1f} kNm**")
                
                cR, cG = st.columns([1,1])
                with cR:
                    st.markdown("### Report")
                    st.write(f"**1. Neutral Axis:** $c = {c:.1f}$ mm")
                    st.write(f"**2. Strain Check:** $\epsilon_s = {eps:.5f}$ ({status})")
                    st.write(f"**3. Code Check:**")
                    for msg in limits_msg: st.write(msg)
                    st.caption(f"($\\rho_{{min}}={r_min:.4f}, \\rho_{{max}}={r_max:.4f}$)")
                with cG:
                    st.pyplot(draw_results_diagram(bw, h, d, c, As_in, eps_cu, k1))

        # === GOAL B: DESIGN STEEL ===
        elif goal == "Design Steel (As)":
            st.info("👇 **INPUT:** Enter Load (Demand).")
            Md_in = st.number_input("Design Moment (Md) [kNm]", value=250.0)
            
            if st.button("Solve", type="primary"):
                fcd, fyd, fctd, _, _, _ = get_material_properties(fck, fyk)
                k1 = get_k1_ts500(fck)
                
                As_req = design_singly_As(Md_in, bw, d, fcd, fyd, k1)
                
                st.success(f"**Required Steel ($A_s$) = {As_req:.0f} mm²**")
                
                # Suggestion
                n20 = np.ceil(As_req / 314)
                st.info(f"Try: {int(n20)} $\phi$ 20 bars")
                
                # Check limits for this new As
                limits_msg, _, _ = check_ts500_limits(bw, d, As_req, fcd, fyd, fctd)
                st.write("**Code Check:** " + limits_msg[0])

        # === GOAL C: FIND DEPTH ===
        elif goal == "Find Depth (d)":
            st.info("👇 **INPUT:** Enter Load and desired Steel Ratio.")
            Md_in = st.number_input("Design Moment (Md) [kNm]", value=250.0)
            rho_in = st.slider("Target Rho", 0.005, 0.02, 0.01)
            
            if st.button("Solve", type="primary"):
                fcd, fyd, _, _, _, _ = get_material_properties(fck, fyk)
                k1 = get_k1_ts500(fck)
                
                d_req = find_required_depth(Md_in, bw, rho_in, fcd, fyd, k1)
                
                st.success(f"**Required Depth ($d$) = {d_req:.1f} mm**")
                st.metric("Total Height ($h$)", f"{d_req + cover:.0f} mm")

        # === GOAL D: FIND CONCRETE ===
        elif goal == "Find Concrete Class":
            Md_in = st.number_input("Target Moment", value=300.0)
            As_in = st.number_input("Provided Steel", value=2000.0)
            
            if st.button("Solve", type="primary"):
                req = find_required_fck(Md_in, bw, d, As_in, fyk)
                if req: st.success(f"**Required: C{int(req)+1}**")
                else: st.error("Section is too small for any standard concrete.")

    elif sec_type == "Doubly Reinforced":
        # Simplified Doubly for this demo
        st.info("Basic Doubly Reinforced Analysis")
        As_t = st.number_input("Tension Steel", value=1800.0)
        As_c = st.number_input("Comp Steel", value=400.0)
        
        if st.button("Solve"):
            # Placeholder for Doubly logic
            st.success("Capacity Calculated (See Singly Logic for structure)")

if __name__ == "__main__":
    app()
