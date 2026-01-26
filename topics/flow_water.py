import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- GLOBAL HELPER FUNCTIONS ---
def format_scientific(val):
    if val == 0: return "0"
    exponent = int(np.floor(np.log10(abs(val))))
    mantissa = val / (10**exponent)
    if -3 < exponent < 4: return f"{val:.4f}"
    else: return f"{mantissa:.2f} \\times 10^{{{exponent}}}"

def solve_flow_net_at_point(x, y, struct_type, dim_val, H_up, H_down):
    z = x + 1j * y
    if struct_type == "Concrete Dam":
        c = dim_val / 2.0
        if y == 0 and abs(x) < c: return None, None, None, None
        try:
            w = np.arccosh(z / c)
            phi = np.real(w)
            phi_up = np.real(np.arccosh((-20 + 0j) / c))
            phi_down = np.real(np.arccosh((20 + 0j) / c))
        except: return None, None, None, None
    else: # Sheet Pile
        try:
            w = np.sqrt(z + 1j * dim_val)
            phi = np.real(w)
            phi_up, phi_down = -10.0, 10.0
            if x < 0: phi = -abs(phi)
            else: phi = abs(phi)
        except: return None, None, None, None

    if phi_down == phi_up: fraction = 0.5
    else: fraction = (phi - phi_up) / (phi_down - phi_up)
    fraction = max(0.0, min(1.0, fraction))
    
    total_head = H_up - (fraction * (H_up - H_down))
    elevation_head = y
    pressure_head = total_head - elevation_head
    pore_pressure = pressure_head * 9.81 
    
    return total_head, elevation_head, pressure_head, pore_pressure

# --- TAB RENDERERS ---
def render_tab1_seepage():
    st.caption("Determine Effective Stress at Point A.")
    col_setup, col_plot = st.columns([1, 1.2])
    with col_setup:
        val_z = st.number_input("Soil Specimen Height (z)", 0.1, step=0.5, value=4.0, key="t1_z")
        val_y = st.number_input("Water Height above Soil (y)", 0.0, step=0.5, value=2.0, key="t1_y")
        val_x = st.number_input("Piezometer Head (x)", 0.0, step=0.5, value=7.5, key="t1_x")
        gamma_sat = st.number_input("Sat. Unit Weight", 18.0, step=0.1, key="t1_g")
        val_A = st.slider("Height of Point A", 0.0, val_z, val_z/2, key="t1_a")

        if st.button("Calculate Effective Stress", type="primary", key="t1_btn"):
            H_top, H_bot = val_z + val_y, val_x
            h_loss = H_top - H_bot
            if h_loss > 0: msg = "Downward Flow (+Stress)"
            elif h_loss < 0: msg = "Upward Flow (-Stress)"
            else: msg = "Hydrostatic"
            
            sigma = (val_y * 9.81) + ((val_z - val_A) * gamma_sat)
            H_A = H_bot + (val_A / val_z) * (H_top - H_bot)
            u = (H_A - val_A) * 9.81
            st.success(f"Condition: {msg}")
            st.metric("Total Stress", f"{sigma:.2f} kPa")
            st.metric("Pore Pressure", f"{u:.2f} kPa")
            st.metric("Effective Stress", f"{sigma - u:.2f} kPa")

    with col_plot:
        fig, ax = plt.subplots(figsize=(7, 8))
        datum_y, soil_w, soil_x = 0.0, 2.5, 3.5
        wl_top = val_z + val_y
        wl_bot = val_x
        
        ax.add_patch(patches.Rectangle((soil_x, datum_y), soil_w, val_z, facecolor='#E3C195', hatch='.'))
        tank_base = max(datum_y + val_z, wl_top - 0.5)
        tank_x = soil_x + (soil_w - 2.0)/2
        ax.add_patch(patches.Rectangle((tank_x, tank_base), 2.0, wl_top - tank_base, facecolor='#D6EAF8', edgecolor='black'))
        
        # Simple Tube representation for robustness
        ax.plot([soil_x, soil_x], [0, val_z], 'k-', lw=2)
        ax.plot([soil_x+soil_w, soil_x+soil_w], [0, val_z], 'k-', lw=2)
        
        # Water Levels
        ax.plot([tank_x, tank_x+2.0], [wl_top, wl_top], 'b-', lw=2)
        
        # Left Tank Level visualization (simplified)
        ax.annotate(f"Head: {wl_bot}m", xy=(soil_x, 0), xytext=(1, wl_bot), arrowprops=dict(arrowstyle='->', color='blue'))
        ax.plot([0.5, 2.5], [wl_bot, wl_bot], 'b--', lw=1)

        ax.scatter(soil_x + soil_w/2, val_A, c='red', s=80, zorder=10)
        ax.set_ylim(-2, max(wl_top, wl_bot)+2); ax.set_xlim(0, 9); ax.axis('off')
        st.pyplot(fig)

def render_tab2_permeability():
    st.caption("Calculate Permeability (k).")
    c1, c2 = st.columns([1, 1.2])
    with c1:
        type_t = st.radio("Test", ["Constant Head", "Falling Head"], key="t2_type")
        if type_t == "Constant Head":
            Q = st.number_input("Q [cm³]", 500.0, key="t2_q")
            L = st.number_input("L [cm]", 15.0, key="t2_l")
            h = st.number_input("h [cm]", 40.0, key="t2_h")
            A = st.number_input("A [cm²]", 40.0, key="t2_a")
            t = st.number_input("t [sec]", 60.0, key="t2_t")
            if st.button("Calc k", key="t2_b"):
                k = (Q*L)/(A*h*t)
                st.markdown(f"<h3 style='color:green'>k = {format_scientific(k)} cm/s</h3>", unsafe_allow_html=True)
        else:
            a = st.number_input("a [cm²]", 0.5, key="t2_aa")
            A = st.number_input("A [cm²]", 40.0, key="t2_aa2")
            L = st.number_input("L [cm]", 15.0, key="t2_ll")
            h1, h2 = st.number_input("h1", 50.0, key="t2_h1"), st.number_input("h2", 30.0, key="t2_h2")
            t = st.number_input("t [sec]", 300.0, key="t2_tt")
            if st.button("Calc k", key="t2_bb"):
                k = (2.303*a*L)/(A*t)*np.log10(h1/h2)
                st.markdown(f"<h3 style='color:green'>k = {format_scientific(k)} cm/s</h3>", unsafe_allow_html=True)
    with c2:
        fig, ax = plt.subplots(figsize=(6,6))
        ax.add_patch(patches.Rectangle((2,2), 4, 4, facecolor='#E3C195', hatch='X'))
        ax.text(4,4,"SOIL", ha='center', fontweight='bold')
        ax.axis('off')
        st.pyplot(fig)

def render_tab3_flownet():
    st.markdown("### 2D Flow Net Analysis")
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st_type = st.radio("Structure", ["Sheet Pile", "Concrete Dam"], key="t3_st")
        dim = st.number_input("Dimension (Width/Depth)", 5.0, key="t3_dim")
        h_up, h_dw = st.number_input("Upstream H", 10.0, key="t3_hu"), st.number_input("Downstream H", 2.0, key="t3_hd")
        
        st.markdown("---")
        px = st.number_input("Point X", 2.0, key="t3_px")
        py = st.number_input("Point Y", -4.0, max_value=0.0, key="t3_py")
        
        rh, rz, rp, ru = solve_flow_net_at_point(px, py, st_type, dim, h_up, h_dw)
        if rh:
            st.info(f"At ({px}, {py}):\nTotal Head: {rh:.2f}m\nPore Pressure: {ru:.2f} kPa")
        
        st.markdown("---")
        k = st.number_input("k [m/day]", 0.0864, key="t3_k")
        nf, nd = st.number_input("Nf", 4, key="t3_nf"), st.number_input("Nd", 12, key="t3_nd")
        if st.button("Calc Flow", key="t3_bq"):
            q = k * (h_up - h_dw) * (nf/nd)
            st.success(f"q = {q:.4f} m³/day/m")

    with c2:
        fig, ax = plt.subplots(figsize=(8,6))
        gx, gy = np.linspace(-15, 15, 100), np.linspace(-15, 0, 100)
        X, Y = np.meshgrid(gx, gy); Z = X + 1j*Y
        
        if st_type == "Concrete Dam":
            C = dim/2.0
            ax.add_patch(patches.Rectangle((-C, 0), 2*C, h_up+1, facecolor='gray'))
            with np.errstate(all='ignore'): W = np.arccosh(Z/C)
        else:
            D = dim
            ax.add_patch(patches.Rectangle((-0.2, -D), 0.4, D+h_up, facecolor='gray'))
            with np.errstate(all='ignore'): W = -1j*np.sqrt(Z+1j*D)
            
        ax.contour(X, Y, np.imag(W), 10, colors='blue', alpha=0.5)
        ax.contour(X, Y, np.real(W), 15, colors='red', alpha=0.5)
        
        ax.add_patch(patches.Rectangle((-15, 0), 15, h_up, facecolor='#D6EAF8', alpha=0.5))
        ax.add_patch(patches.Rectangle((0, 0), 15, h_dw, facecolor='#D6EAF8', alpha=0.5))
        ax.plot([-15, 15], [0, 0], 'k-')
        
        if rh: ax.scatter(px, py, c='red', marker='x', s=100, zorder=10)
        ax.set_ylim(-12, max(h_up, h_dw)+1); ax.set_xlim(-12, 12); ax.axis('off')
        st.pyplot(fig)

# --- MAIN APP FUNCTION ---
def app():
    # This is what gets called by 06_Soil_Mechanics.py
    t1, t2, t3 = st.tabs(["1D Seepage", "Permeability", "2D Flow Net"])
    with t1: render_tab1_seepage()
    with t2: render_tab2_permeability()
    with t3: render_tab3_flownet()
