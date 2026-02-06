import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.optimize import brentq 

# ======================================
# 1. HELPER: TS 500 & MATH
# ======================================
def get_k1_ts500(fck):
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

def analyze_singly(b, d, As, fcd, fyd, Es, epsilon_cu, k1, epsilon_sy):
    c_calc = (As * fyd) / (0.85 * fcd * b * k1)
    eps_s = epsilon_cu * (d - c_calc) / c_calc
    status = "Yielded"
    fs = fyd
    
    if eps_s < epsilon_sy:
        status = "Not Yielded"
        A_q = 0.85 * fcd * b * k1
        B_q = As * Es * epsilon_cu
        C_q = - (As * Es * epsilon_cu * d)
        delta = B_q**2 - 4 * A_q * C_q
        c_calc = (-B_q + np.sqrt(delta)) / (2 * A_q)
        eps_s = epsilon_cu * (d - c_calc) / c_calc
        fs = eps_s * Es
        
    a = k1 * c_calc
    Mr = As * fs * (d - a/2) * 1e-6
    return Mr, c_calc, eps_s, status

def design_singly_As(Md_target, b, d, fcd, fyd, k1):
    Md_Nmm = Md_target * 1e6
    As_try = Md_Nmm / (fyd * 0.9 * d)
    for _ in range(10):
        a = (As_try * fyd) / (0.85 * fcd * b)
        z = d - a/2
        As_new = Md_Nmm / (fyd * z)
        if abs(As_new - As_try) < 1.0: break
        As_try = As_new
    return As_try

def find_required_fck(Md_target, b, d, As, fyk):
    def capacity_gap(fck_try):
        k1 = get_k1_ts500(fck_try)
        fcd = fck_try / 1.5
        fyd = fyk / 1.15
        Es = 200000.0
        eps_cu = 0.003
        eps_sy = fyd/Es
        Mr, _, _, _ = analyze_singly(b, d, As, fcd, fyd, Es, eps_cu, k1, eps_sy)
        return Mr - Md_target
    try:
        return brentq(capacity_gap, 10, 150)
    except:
        return None

def solve_doubly_quadratic(b, As, As_prime, d, d_prime, fcd, fyd, Es, epsilon_cu, k1):
    A_quad = 0.85 * fcd * b * k1
    B_quad = (As_prime * Es * epsilon_cu) - (As * fyd)
    C_quad = - (As_prime * Es * epsilon_cu * d_prime)
    delta = B_quad**2 - 4 * A_quad * C_quad
    if delta < 0: return d/2 
    return (-B_quad + np.sqrt(delta)) / (2 * A_quad)

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
            F_net -= As_i * sigma 
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
# 2. DRAWING FUNCTIONS
# ======================================
def draw_live_section(b, h, layers_to_draw, cover):
    """
    Draws just the physical section geometry for live preview.
    layers_to_draw: list of dict {'d': depth, 'As': area, 'label': text}
    """
    fig, ax = plt.subplots(figsize=(4, 4))
    fig.patch.set_alpha(0); ax.patch.set_alpha(0)
    
    # 1. Concrete Box
    ax.add_patch(patches.Rectangle((0, 0), b, h, fill=True, facecolor='#e0e0e0', edgecolor='black', linewidth=2))
    
    # 2. Reinforcement
    # Visualize area roughly by circle size (scaled)
    max_area = max([l['As'] for l in layers_to_draw]) if layers_to_draw else 500
    
    for layer in layers_to_draw:
        y_pos = h - layer['d']
        area = layer['As']
        
        # Scale radius for visual relative to max, but keep min visible
        radius = 5 + 15 * (area / (max_area + 1)) 
        
        # Draw "Bars" (Just one circle to represent layer centroid)
        ax.add_patch(patches.Circle((b/2, y_pos), radius, color="#d32f2f", zorder=10))
        
        # Label Line
        ax.annotate(f"{layer['label']}\nAs={area:.0f}", 
                    xy=(b/2 + radius, y_pos), 
                    xytext=(b + 30, y_pos),
                    arrowprops=dict(arrowstyle='-', color='red', linewidth=1),
                    fontsize=9, color='red', va='center')

    # Dimensions
    ax.annotate(f"b={b:.0f}", xy=(b/2, h+10), ha='center', fontsize=10)
    ax.annotate(f"h={h:.0f}", xy=(-10, h/2), rotation=90, va='center', fontsize=10)
    
    # Axis settings
    margin = 80
    ax.set_xlim(-50, b + margin)
    ax.set_ylim(-50, h + 50)
    ax.set_aspect('equal')
    ax.axis('off')
    return fig

def draw_stress_strain_result(c, h, layers, epsilon_cu, fcd, k1, Es, fyd):
    # (Same result drawing function as before)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 4))
    fig.patch.set_alpha(0); ax1.patch.set_alpha(0); ax2.patch.set_alpha(0)
    for ax in [ax1, ax2]:
        ax.axhline(y=h, color='k', lw=1); ax.axhline(y=0, color='k', lw=1)
        ax.axvline(x=0, color='gray', alpha=0.5, lw=0.5)
        ax.axis('off'); ax.set_ylim(-0.1*h, 1.1*h)

    ax1.set_title("Strain", color="white")
    y_na = h - c
    ax1.axhline(y=y_na, color='red', linestyle=':')
    ax1.text(0.1, y_na, f"c={c:.1f}", color='red', fontsize=8)
    
    d_max = max([l['d'] for l in layers])
    eps_bot = epsilon_cu * (d_max - c) / c
    scale = 0.8 / max(epsilon_cu, abs(eps_bot) + 0.0001)
    ax1.plot([-epsilon_cu*scale, eps_bot*scale], [h, h-d_max], 'b-o', linewidth=2)
    ax1.text(-epsilon_cu*scale, h+10, f"{epsilon_cu}", color='white', ha='center', fontsize=8)

    ax2.set_title("Forces", color="white")
    a = k1 * c
    Fc_rect = patches.Rectangle((-0.5, h-a), 0.5, a, facecolor='#ffcccc', edgecolor='red')
    ax2.add_patch(Fc_rect)
    ax2.arrow(-0.25, h-a/2, 0.25, 0, color='red', head_width=15, length_includes_head=True)
    
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
    st.markdown("## TS 500: Flexure (Live Preview)")
    
    # 1. Global Section Properties (Sidebar)
    with st.sidebar:
        st.header("Global Dimensions")
        bw = st.number_input("Width (b) [mm]", 300.0, step=50.0)
        h = st.number_input("Height (h) [mm]", 500.0, step=50.0)
        cover = st.number_input("Cover [mm]", 40.0, step=5.0)
        d = h - cover
        
        st.header("Materials")
        fck = st.selectbox("Concrete (C)", [20, 25, 30, 35, 40, 45, 50], index=2)
        fyk = st.selectbox("Steel (S)", [220, 420, 500], index=1)

    # 2. Main Tabs
    tab1, tab2, tab3 = st.tabs(["Singly Reinforced", "Doubly Reinforced", "Multi-Layer"])

    # --- TAB 1: SINGLY REINFORCED ---
    with tab1:
        col_in, col_viz = st.columns([1, 1])
        with col_in:
            st.subheader("1. Inputs")
            mode = st.radio("Mode", ["Capacity ($M_r$)", "Design ($A_s$)", "Find $f_{ck}$"], horizontal=True)
            
            # Default Layer List for Visualization
            layers_viz = []
            
            if mode == "Capacity ($M_r$)":
                As_in = st.number_input("Steel Area ($A_s$)", value=1500.0)
                layers_viz = [{'d': d, 'As': As_in, 'label': 'As'}]
                
                if st.button("Calculate", key="b1"):
                    fcd, fyd, Es, eps_cu, eps_sy = get_material_properties(fck, fyk)
                    k1 = get_k1_ts500(fck)
                    Mr, c, _, status = analyze_singly(bw, d, As_in, fcd, fyd, Es, eps_cu, k1, eps_sy)
                    st.success(f"**Mr = {Mr:.1f} kNm**")
                    st.caption(f"c={c:.1f}mm | {status}")
                    
            elif mode == "Design ($A_s$)":
                Md_in = st.number_input("Design Moment ($M_d$)", value=250.0)
                # For viz, we show calculated As after button press, or placeholder
                if st.button("Calculate", key="b2"):
                    fcd, fyd, _, _, _ = get_material_properties(fck, fyk)
                    k1 = get_k1_ts500(fck)
                    As_req = design_singly_As(Md_in, bw, d, fcd, fyd, k1)
                    st.success(f"**Required As = {As_req:.0f} mm²**")
                    layers_viz = [{'d': d, 'As': As_req, 'label': 'Req As'}]
            
            elif mode == "Find $f_{ck}$":
                Md_in = st.number_input("Target Moment ($M_d$)", value=300.0)
                As_in = st.number_input("Steel Area ($A_s$)", value=2000.0)
                layers_viz = [{'d': d, 'As': As_in, 'label': 'As'}]
                if st.button("Calculate", key="b3"):
                    req_fck = find_required_fck(Md_in, bw, d, As_in, fyk)
                    if req_fck: st.success(f"**Required fck = {req_fck:.1f} MPa**")
                    else: st.error("Impossible with this section.")

        with col_viz:
            st.markdown("#### Section Preview")
            if layers_viz:
                fig = draw_live_section(bw, h, layers_viz, cover)
                st.pyplot(fig)
            else:
                st.info("Define inputs to see section.")

    # --- TAB 2: DOUBLY REINFORCED ---
    with tab2:
        col_in, col_viz = st.columns([1, 1])
        with col_in:
            st.subheader("1. Reinforcement")
            As_tens = st.number_input("Tension ($A_s$)", value=1800.0)
            As_comp = st.number_input("Compression ($A_s'$)", value=400.0)
            
            # Prepare Live Data
            layers_viz = [
                {'d': d, 'As': As_tens, 'label': 'As (Tens)'},
                {'d': cover, 'As': As_comp, 'label': "As' (Comp)"}
            ]
            
            if st.button("Calculate Capacity", key="b_double"):
                fcd, fyd, Es, eps_cu, eps_sy = get_material_properties(fck, fyk)
                k1 = get_k1_ts500(fck)
                
                # Check Comp Yield
                c_assume = ((As_tens - As_comp)*fyd)/(0.85*fcd*bw*k1)
                eps_comp = eps_cu*(c_assume - cover)/c_assume
                
                if eps_comp < eps_sy:
                    st.warning("Comp. steel Elastic")
                    c_final = solve_doubly_quadratic(bw, As_tens, As_comp, d, cover, fcd, fyd, Es, eps_cu, k1)
                    eps_comp = eps_cu*(c_final - cover)/c_final
                    fs_prime = eps_comp * Es
                else:
                    c_final = c_assume
                    fs_prime = fyd
                    
                a = k1*c_final
                Cc = 0.85*fcd*bw*a
                Cs = As_comp*fs_prime
                Mr = (Cc*(d - a/2) + Cs*(d - cover))*1e-6
                
                st.metric("Capacity ($M_r$)", f"{Mr:.1f} kNm")
                
                # Show Result Graph below input
                fig_res = draw_stress_strain_result(c_final, h, layers_viz, eps_cu, fcd, k1, Es, fyd)
                st.pyplot(fig_res)

        with col_viz:
            st.markdown("#### Section Preview")
            fig = draw_live_section(bw, h, layers_viz, cover)
            st.pyplot(fig)

    # --- TAB 3: MULTI-LAYER ---
    with tab3:
        col_in, col_viz = st.columns([1, 1])
        layers_data = []
        
        with col_in:
            st.subheader("1. Define Layers")
            n_layers = st.number_input("Num Layers", 1, 10, 3)
            
            # Input Loop
            for i in range(int(n_layers)):
                c1, c2 = st.columns([1, 1])
                # Smart defaults
                def_d = cover + (d-cover)*(i/(n_layers-1)) if n_layers>1 else d
                with c1: ld = st.number_input(f"d{i+1}", value=float(def_d), key=f"md{i}")
                with c2: las = st.number_input(f"As{i+1}", value=400.0, key=f"mas{i}")
                layers_data.append({'d': ld, 'As': las, 'label': f'L{i+1}'})
            
            if st.button("Calculate", key="b_multi"):
                fcd, fyd, Es, eps_cu, _ = get_material_properties(fck, fyk)
                k1 = get_k1_ts500(fck)
                c_iter = solve_multilayer_iterative(layers_data, bw, h, fcd, fyd, Es, eps_cu, k1)
                
                # Calc Moment
                a = k1 * c_iter
                if a>h: a=h
                Fc = 0.85 * fcd * bw * a
                M_tot = Fc * (h/2 - a/2)
                for l in layers_data:
                    eps = eps_cu*(l['d'] - c_iter)/c_iter
                    sigma = min(max(eps*Es, -fyd), fyd)
                    M_tot += l['As']*sigma*(l['d'] - h/2)
                
                st.metric("Capacity ($M_r$)", f"{M_tot/1e6:.1f} kNm")
                
                fig_res = draw_stress_strain_result(c_iter, h, layers_data, eps_cu, fcd, k1, Es, fyd)
                st.pyplot(fig_res)

        with col_viz:
            st.markdown("#### Section Preview")
            # This graph updates AUTOMATICALLY as you change inputs in col_in loop
            fig = draw_live_section(bw, h, layers_data, cover)
            st.pyplot(fig)

if __name__ == "__main__":
    app()
