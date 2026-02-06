import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.optimize import brentq 

# ======================================
# 1. HELPER: TS 500 PARAMETERS & LOGIC
# ======================================
def get_k1_ts500(fck):
    """Returns k1 factor per TS 500."""
    if fck <= 25: return 0.85
    elif fck == 30: return 0.82
    elif fck == 35: return 0.79
    elif fck == 40: return 0.76
    elif fck == 45: return 0.73
    elif fck >= 50: return 0.70
    return 0.85

def get_material_properties(fck, fyk):
    fcd = fck / 1.5
    fyd = fyk / 1.15
    Es = 200000.0
    epsilon_cu = 0.003
    epsilon_sy = fyd / Es
    return fcd, fyd, Es, epsilon_cu, epsilon_sy

# --- CORE SOLVER: SINGLY REINFORCED ANALYSIS ---
def analyze_singly(b, d, As, fcd, fyd, Es, epsilon_cu, k1, epsilon_sy):
    """
    Standard Analysis: Returns (Mr, c, status, rho)
    """
    # 1. Force Equilibrium (Assume Yield)
    # 0.85 * fcd * b * k1 * c = As * fyd
    c_calc = (As * fyd) / (0.85 * fcd * b * k1)
    
    # 2. Check Strain
    eps_s = epsilon_cu * (d - c_calc) / c_calc
    
    status = "Yielded (Under-reinforced)"
    fs = fyd
    
    if eps_s < epsilon_sy:
        status = "Not Yielded (Over-reinforced)"
        # Quadratic Solve
        # A*c^2 + B*c + C = 0
        A_q = 0.85 * fcd * b * k1
        B_q = As * Es * epsilon_cu
        C_q = - (As * Es * epsilon_cu * d)
        
        delta = B_q**2 - 4 * A_q * C_q
        c_calc = (-B_q + np.sqrt(delta)) / (2 * A_q)
        
        # Recalc stress
        eps_s = epsilon_cu * (d - c_calc) / c_calc
        fs = eps_s * Es
        
    a = k1 * c_calc
    Mr = As * fs * (d - a/2) * 1e-6 # kNm
    return Mr, c_calc, eps_s, status

# --- SOLVER: DESIGN STEEL (As) ---
def design_singly_As(Md_target, b, d, fcd, fyd, k1):
    """
    Finds required As for a given Moment Md (kNm).
    Approximation using lever arm z ~ 0.9d then refining.
    """
    Md_Nmm = Md_target * 1e6
    
    # Initial Guess: z = 0.9d
    # As = M / (fyd * 0.9d)
    As_try = Md_Nmm / (fyd * 0.9 * d)
    
    # Iterate 5 times to converge lever arm
    for _ in range(10):
        a = (As_try * fyd) / (0.85 * fcd * b) # Force equilibrium
        z = d - a/2
        As_new = Md_Nmm / (fyd * z)
        if abs(As_new - As_try) < 1.0: break
        As_try = As_new
        
    return As_try

# --- SOLVER: REVERSE CONCRETE (fck) ---
def find_required_fck(Md_target, b, d, As, fyk):
    """
    Finds minimum fck required to support Md with given geometry/steel.
    Uses Bisection method.
    """
    def capacity_gap(fck_try):
        # Calc properties for this fck
        k1 = get_k1_ts500(fck_try)
        fcd = fck_try / 1.5
        fyd = fyk / 1.15
        Es = 200000.0
        eps_cu = 0.003
        eps_sy = fyd/Es
        
        Mr, _, _, _ = analyze_singly(b, d, As, fcd, fyd, Es, eps_cu, k1, eps_sy)
        return Mr - Md_target

    # Search range C10 to C100
    try:
        fck_sol = brentq(capacity_gap, 10, 150)
        return fck_sol
    except:
        return None # No solution in reasonable range

# --- SOLVER: DOUBLY REINFORCED (Quadratic) ---
def solve_doubly_quadratic(b, As, As_prime, d, d_prime, fcd, fyd, Es, epsilon_cu, k1):
    A_quad = 0.85 * fcd * b * k1
    B_quad = (As_prime * Es * epsilon_cu) - (As * fyd)
    C_quad = - (As_prime * Es * epsilon_cu * d_prime)
    
    delta = B_quad**2 - 4 * A_quad * C_quad
    if delta < 0: return d/2 
    c = (-B_quad + np.sqrt(delta)) / (2 * A_quad)
    return c

# --- SOLVER: MULTI-LAYER (Iterative) ---
def solve_multilayer_iterative(layers, b, h, fcd, fyd, Es, epsilon_cu, k1):
    def sum_forces(c_try):
        if c_try <= 0.1: return 1e9
        a = k1 * c_try
        if a > h: a = h
        Fc = 0.85 * fcd * b * a
        F_net = Fc 
        for layer in layers:
            d_i = layer['d']
            As_i = layer['As']
            eps = epsilon_cu * (d_i - c_try) / c_try
            sigma = min(max(eps * Es, -fyd), fyd)
            F_layer = As_i * sigma
            F_net -= F_layer 
        return F_net

    c_min, c_max = 1.0, h * 1.5
    for _ in range(100): 
        c_mid = (c_min + c_max) / 2
        f_mid = sum_forces(c_mid)
        if abs(f_mid) < 10: return c_mid
        if f_mid > 0: c_max = c_mid
        else: c_min = c_mid
    return (c_min + c_max) / 2

# ======================================
# 2. HELPER: DRAWING FUNCTIONS
# ======================================
def draw_stress_strain_general(c, h, layers, epsilon_cu, fcd, k1, Es, fyd):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))
    fig.patch.set_alpha(0); ax1.patch.set_alpha(0); ax2.patch.set_alpha(0)
    
    for ax in [ax1, ax2]:
        ax.axhline(y=h, color='k', lw=1); ax.axhline(y=0, color='k', lw=1)
        ax.axvline(x=0, color='gray', alpha=0.5, lw=0.5)
        ax.axis('off'); ax.set_ylim(-0.1*h, 1.1*h)

    # 1. Strain
    ax1.set_title("Strain Profile", color="white")
    y_na = h - c
    ax1.axhline(y=y_na, color='red', linestyle=':')
    ax1.text(0.1, y_na, f"c={c:.1f}", color='red', fontsize=8)
    
    d_max = max([l['d'] for l in layers])
    eps_bot = epsilon_cu * (d_max - c) / c
    scale = 0.8 / max(epsilon_cu, abs(eps_bot) + 0.0001)
    
    ax1.plot([-epsilon_cu*scale, eps_bot*scale], [h, h-d_max], 'b-o', linewidth=2)
    ax1.text(-epsilon_cu*scale, h+10, f"{epsilon_cu}", color='white', ha='center', fontsize=8)

    # 2. Forces
    ax2.set_title("Internal Forces", color="white")
    a = k1 * c
    Fc_rect = patches.Rectangle((-0.5, h-a), 0.5, a, facecolor='#ffcccc', edgecolor='red')
    ax2.add_patch(Fc_rect)
    ax2.arrow(-0.25, h-a/2, 0.25, 0, color='red', head_width=15, length_includes_head=True)
    ax2.text(-0.6, h-a/2, "Fc", color='red', va='center')
    
    max_force = 0
    for l in layers:
        eps = epsilon_cu * (l['d'] - c) / c
        sigma = min(max(eps*Es, -fyd), fyd)
        force = abs(l['As'] * sigma)
        if force > max_force: max_force = force
        
    for i, layer in enumerate(layers):
        y_pos = h - layer['d']
        eps = epsilon_cu * (layer['d'] - c) / c
        sigma = min(max(eps*Es, -fyd), fyd)
        col = 'blue' if sigma > 0 else 'orange'
        direction = 1 if sigma > 0 else -1
        arrow_len = 0.4 * (abs(layer['As']*sigma) / (max_force+1)) + 0.1
        ax2.arrow(0, y_pos, direction*arrow_len, 0, color=col, head_width=15, width=2, length_includes_head=True)

    return fig

# ======================================
# 3. MAIN APP
# ======================================
def app():
    st.markdown("## TS 500: Flexural Analysis")
    st.caption("Calculate Capacity, Design Steel, or Find required Concrete Strength.")

    # --- SIDEBAR INPUTS ---
    with st.sidebar:
        st.header("Section Parameters")
        bw = st.number_input("Width (b) [mm]", 300.0)
        h = st.number_input("Height (h) [mm]", 500.0)
        cover = st.number_input("Cover [mm]", 40.0)
        d = h - cover

    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["1. Singly Reinforced", "2. Doubly Reinforced", "3. Multi-Layer"])

    # === TAB 1: SINGLY REINFORCED ===
    with tab1:
        st.subheader("Singly Reinforced Section")
        
        # Calculation Goal Selector
        calc_mode = st.radio(
            "What do you want to calculate?",
            ["Moment Capacity ($M_r$)", "Steel Requirement ($A_s$)", "Concrete Strength ($f_{ck}$)", "Section Depth ($d$)"],
            horizontal=True
        )

        st.markdown("---")
        
        # DYNAMIC INPUTS BASED ON SELECTION
        col_in1, col_in2 = st.columns(2)
        
        # Default placeholders
        As_input = 0.0
        Md_input = 0.0
        fck_input = 30
        fyk_input = 420
        d_input = d

        with col_in1:
            if calc_mode == "Concrete Strength ($f_{ck}$)":
                 st.info("Finding required Concrete Class")
            else:
                fck_input = st.selectbox("Concrete Class (C)", [20, 25, 30, 35, 40, 45, 50], index=2, key="s_fck")
            
            fyk_input = st.selectbox("Steel Grade (S)", [220, 420, 500], index=1, key="s_fyk")

        with col_in2:
            if calc_mode == "Moment Capacity ($M_r$)":
                As_input = st.number_input("Steel Area ($A_s$) [mm²]", value=1500.0)
            elif calc_mode == "Steel Requirement ($A_s$)":
                Md_input = st.number_input("Design Moment ($M_d$) [kNm]", value=250.0)
            elif calc_mode == "Concrete Strength ($f_{ck}$)":
                Md_input = st.number_input("Target Moment ($M_d$) [kNm]", value=300.0)
                As_input = st.number_input("Steel Area ($A_s$) [mm²]", value=2000.0)
            elif calc_mode == "Section Depth ($d$)":
                Md_input = st.number_input("Target Moment ($M_d$) [kNm]", value=250.0)
                rho_target = st.slider("Target Steel Ratio ($\\rho$)", 0.005, 0.02, 0.01)

        # --- EXECUTE CALCULATION ---
        if st.button("Calculate", type="primary"):
            
            # Common Material props
            fcd, fyd, Es, epsilon_cu, epsilon_sy = get_material_properties(fck_input, fyk_input)
            k1 = get_k1_ts500(fck_input)

            # MODE 1: MOMENT CAPACITY
            if calc_mode == "Moment Capacity ($M_r$)":
                Mr, c, eps, status = analyze_singly(bw, d, As_input, fcd, fyd, Es, epsilon_cu, k1, epsilon_sy)
                
                st.metric("Moment Capacity ($M_r$)", f"{Mr:.1f} kNm")
                st.caption(f"Neutral Axis c = {c:.1f} mm | {status}")
                
                # Plot
                fig = draw_stress_strain_general(c, h, [{'As':As_input, 'd':d}], epsilon_cu, fcd, k1, Es, fyd)
                st.pyplot(fig)

            # MODE 2: STEEL REQUIREMENT
            elif calc_mode == "Steel Requirement ($A_s$)":
                As_req = design_singly_As(Md_input, bw, d, fcd, fyd, k1)
                
                # Check if this As creates valid section
                Mr, c, eps, status = analyze_singly(bw, d, As_req, fcd, fyd, Es, epsilon_cu, k1, epsilon_sy)
                
                st.success(f"**Required Steel ($A_s$): {As_req:.0f} mm²**")
                
                col_r1, col_r2 = st.columns(2)
                col_r1.metric("Provided Capacity", f"{Mr:.1f} kNm")
                col_r1.caption(f"Target: {Md_input:.1f} kNm")
                col_r2.metric("Steel Ratio", f"{(As_req/(bw*d))*100:.2f}%")
                
                # Suggest Bars
                n_20 = np.ceil(As_req / 314)
                col_r2.info(f"Try: {int(n_20)} $\phi$ 20")

            # MODE 3: CONCRETE STRENGTH
            elif calc_mode == "Concrete Strength ($f_{ck}$)":
                req_fck = find_required_fck(Md_input, bw, d, As_input, fyk_input)
                
                if req_fck:
                    st.success(f"**Required Concrete Strength ($f_{{ck}}$): {req_fck:.1f} MPa**")
                    st.info(f"Select standard grade higher than C{int(np.ceil(req_fck))}")
                else:
                    st.error("Cannot achieve this moment with the given steel/geometry even with very high strength concrete. Increase dimensions or steel.")

            # MODE 4: SECTION DEPTH
            elif calc_mode == "Section Depth ($d$)":
                # K = bd^2 / M
                # Approximate design using K tables or simple formula: As = rho * b * d
                # Mr = rho * b * d * fy * (d - 0.59 * rho * d * fy/fc)
                # Mr = b * d^2 * [rho * fy * (1 - 0.59 rho fy/fc)]
                
                term = (rho_target * fyd * (1 - 0.59 * rho_target * fyd / fcd))
                # Md = b * d^2 * term
                d_req = np.sqrt( (Md_input * 1e6) / (bw * term) )
                
                st.success(f"**Required Effective Depth ($d$): {d_req:.1f} mm**")
                st.metric("Total Height ($h$)", f"{d_req + cover:.0f} mm")
                st.caption(f"Assuming $\\rho = {rho_target:.1%}$")

    # === TAB 2: DOUBLY REINFORCED ===
    with tab2:
        st.subheader("Doubly Reinforced Section")
        d_mode = st.radio("Goal", ["Analyze Capacity ($M_r$)", "Find Tension Steel ($A_s$)"], horizontal=True, key="d_mode")
        
        fck_d = st.selectbox("Concrete (C)", [20, 25, 30, 35, 40], index=2, key="d_fck")
        fyk_d = st.selectbox("Steel (S)", [420, 500], index=0, key="d_fyk")
        fcd, fyd, Es, epsilon_cu, epsilon_sy = get_material_properties(fck_d, fyk_d)
        k1 = get_k1_ts500(fck_d)

        col_d1, col_d2 = st.columns(2)
        with col_d1: As_comp = st.number_input("Compression Steel ($A_s'$) [mm²]", value=400.0)
        d_comp = cover
        d_tens = d
        
        if d_mode == "Analyze Capacity ($M_r$)":
            with col_d2: As_tens = st.number_input("Tension Steel ($A_s$) [mm²]", value=1800.0, key="d_as_tens")
            
            if st.button("Analyze Doubly", type="primary"):
                # Analysis Logic
                c_assume = ((As_tens - As_comp) * fyd) / (0.85 * fcd * bw * k1)
                eps_comp = epsilon_cu * (c_assume - d_comp) / c_assume
                
                c_final = c_assume
                fs_prime = fyd
                if eps_comp < epsilon_sy:
                    c_final = solve_doubly_quadratic(bw, As_tens, As_comp, d_tens, d_comp, fcd, fyd, Es, epsilon_cu, k1)
                    eps_comp = epsilon_cu * (c_final - d_comp) / c_final
                    fs_prime = eps_comp * Es
                
                a = k1 * c_final
                Cc = 0.85 * fcd * bw * a
                Cs = As_comp * fs_prime
                Mr = (Cc * (d_tens - a/2) + Cs * (d_tens - d_comp)) * 1e-6
                
                st.metric("Moment Capacity", f"{Mr:.1f} kNm")
                st.caption(f"c={c_final:.1f}mm")
                fig = draw_stress_strain_general(c_final, h, [{'As':As_tens, 'd':d_tens}, {'As':As_comp, 'd':d_comp}], epsilon_cu, fcd, k1, Es, fyd)
                st.pyplot(fig)

        else: # Find Tension Steel
            with col_d2: Md_target = st.number_input("Target Moment ($M_d$) [kNm]", value=400.0)
            
            if st.button("Design Tension Steel", type="primary"):
                # Approximate Design
                # M_total = M_singly + M_couple
                # M_couple = As' * fyd * (d - d') (Assume comp steel yields)
                M_couple = (As_comp * fyd * (d_tens - d_comp)) * 1e-6
                
                M_remain = Md_target - M_couple
                
                # Design remaining as singly reinforced
                As_singly = design_singly_As(M_remain, bw, d_tens, fcd, fyd, k1)
                As_total = As_singly + As_comp
                
                st.success(f"**Required Tension Steel ($A_s$): {As_total:.0f} mm²**")
                st.write(f"This assumes compression steel yields. The simplified breakdown is:")
                st.write(f"- Couple ($A_s'$): {M_couple:.1f} kNm")
                st.write(f"- Singly Part: {M_remain:.1f} kNm")


    # === TAB 3: MULTI-LAYER ===
    with tab3:
        st.subheader("Multi-Layer Analysis")
        n_layers = st.number_input("Layers", 1, 10, 3)
        layers = []
        for i in range(int(n_layers)):
            c1, c2 = st.columns([1, 2])
            with c1: l_d = st.number_input(f"Depth L{i+1}", value=float(cover + (d-cover)*(i/(n_layers-1) if n_layers>1 else 1)), key=f"md_{i}")
            with c2: l_as = st.number_input(f"Area L{i+1}", value=500.0 if i==n_layers-1 else 0.0, key=f"mas_{i}")
            layers.append({'As': l_as, 'd': l_d})

        if st.button("Analyze Multi-Layer", type="primary"):
            fcd_m, fyd_m, Es_m, eps_cu_m, _ = get_material_properties(30, 420) # Default mat for multi
            k1_m = get_k1_ts500(30)
            c_iter = solve_multilayer_iterative(layers, bw, h, fcd_m, fyd_m, Es_m, eps_cu_m, k1_m)
            
            # Moment Sum about Geometric Center (h/2)
            a = k1_m * c_iter
            if a > h: a = h
            Fc = 0.85 * fcd_m * bw * a
            M_total = Fc * (h/2 - a/2) 
            
            for l in layers:
                eps = eps_cu_m * (l['d'] - c_iter) / c_iter
                sigma = min(max(eps * Es_m, -fyd_m), fyd_m)
                M_total += l['As'] * sigma * (l['d'] - h/2)
            
            st.metric("Moment Capacity", f"{M_total/1e6:.1f} kNm")
            st.caption(f"c = {c_iter:.1f} mm")
            fig = draw_stress_strain_general(c_iter, h, layers, eps_cu_m, fcd_m, k1_m, Es_m, fyd_m)
            st.pyplot(fig)

if __name__ == "__main__":
    app()
