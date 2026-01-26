import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- 1. HELPER FUNCTIONS ---
def format_scientific(val):
    if val == 0: return "0"
    exponent = int(np.floor(np.log10(abs(val))))
    mantissa = val / (10**exponent)
    if -3 < exponent < 4: return f"{val:.4f}"
    else: return f"{mantissa:.2f} \\times 10^{{{exponent}}}"

def solve_flow_net_at_point(x, y, struct_type, dim_val, H_up, H_down):
    """Calculates Head and Pressure at (x,y) using Conformal Mapping."""
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

    # Interpolate Head
    if phi_down == phi_up: fraction = 0.5
    else: fraction = (phi - phi_up) / (phi_down - phi_up)
    
    fraction = max(0.0, min(1.0, fraction))
    total_head = H_up - (fraction * (H_up - H_down))
    
    elevation_head = y
    pressure_head = total_head - elevation_head
    pore_pressure = pressure_head * 9.81 
    
    return total_head, elevation_head, pressure_head, pore_pressure

# --- 2. TAB RENDERERS (ISOLATED LOGIC) ---

def render_seepage():
    st.subheader("1D Seepage & Effective Stress")
    c1, c2 = st.columns([1, 1.2])
    
    with c1:
        val_z = st.number_input("Soil Height (z) [m]", 0.1, step=0.5, value=4.0)
        val_y = st.number_input("Water Above (y) [m]", 0.0, step=0.5, value=2.0)
        val_x = st.number_input("Piezometer Head (x) [m]", 0.0, step=0.5, value=7.5)
        gamma = st.number_input("Sat. Unit Weight [kN/m³]", 18.0, step=0.1)
        val_A = st.slider("Height of Point A [m]", 0.0, val_z, val_z/2)

        if st.button("Calculate Stress", type="primary"):
            sigma = (val_y * 9.81) + ((val_z - val_A) * gamma)
            H_A = val_x + (val_A / val_z) * ((val_z + val_y) - val_x)
            u = (H_A - val_A) * 9.81
            
            st.metric("Total Stress (σ)", f"{sigma:.2f} kPa")
            st.metric("Pore Pressure (u)", f"{u:.2f} kPa")
            st.metric("Effective Stress (σ')", f"{sigma - u:.2f} kPa")

    with c2:
        fig, ax = plt.subplots(figsize=(6, 8))
        wl_top = val_z + val_y
        wl_bot = val_x
        
        # Soil
        ax.add_patch(patches.Rectangle((3.5, 0), 2.5, val_z, facecolor='#E3C195', hatch='.'))
        # Top Tank
        tank_base = max(val_z, wl_top - 0.5)
        ax.add_patch(patches.Rectangle((3.75, tank_base), 2.0, max(0.5, wl_top-tank_base), facecolor='#D6EAF8', edgecolor='black'))
        
        # Walls
        ax.plot([3.5, 3.5], [0, val_z], 'k-', lw=2)
        ax.plot([6, 6], [0, val_z], 'k-', lw=2)
        
        # Water Levels
        ax.plot([3.75, 5.75], [wl_top, wl_top], 'b-', lw=2)
        
        # Piezometer Level (Dynamic Arrow)
        ax.annotate(f"Head: {wl_bot}m", xy=(3.5, 0), xytext=(1, wl_bot), arrowprops=dict(arrowstyle='->', color='blue'))
        ax.plot([1, 3.5], [wl_bot, wl_bot], 'b--', lw=1)
        
        # Point A
        ax.scatter(4.75, val_A, c='red', s=80, zorder=5)
        ax.text(5, val_A, "A", fontweight='bold')
        
        # FIX: Dynamic Y-Limit to prevent cut-off
        max_y = max(wl_top, wl_bot) + 2
        ax.set_ylim(-2, max_y)
        ax.set_xlim(0, 9)
        ax.axis('off')
        st.pyplot(fig)
        plt.close(fig) # FIX: Prevents memory leak

def render_permeability():
    st.subheader("Permeability Lab Tests")
    c1, c2 = st.columns([1, 1.2])
    
    with c1:
        method = st.radio("Method", ["Constant Head", "Falling Head"])
        if method == "Constant Head":
            Q = st.number_input("Q [cm³]", 500.0)
            L = st.number_input("L [cm]", 15.0)
            h = st.number_input("h [cm]", 40.0)
            A = st.number_input("A [cm²]", 40.0)
            t = st.number_input("t [sec]", 60.0)
            if st.button("Calculate k"):
                if A*h*t > 0:
                    k = (Q*L)/(A*h*t)
                    st.success(f"k = {format_scientific(k)} cm/s")
                else: st.error("Invalid inputs")
        else:
            a = st.number_input("a [cm²]", 0.5)
            A = st.number_input("A [cm²]", 40.0)
            L = st.number_input("L [cm]", 15.0)
            h1, h2 = st.number_input("h1", 50.0), st.number_input("h2", 30.0)
            t = st.number_input("t", 300.0)
            if st.button("Calculate k"):
                if A*t > 0:
                    k = (2.303*a*L)/(A*t)*np.log10(h1/h2)
                    st.success(f"k = {format_scientific(k)} cm/s")
                else: st.error("Invalid inputs")

    with c2:
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.add_patch(patches.Rectangle((3,3), 4, 4, facecolor='#E3C195', hatch='X', edgecolor='black'))
        ax.text(5,5,"SOIL SAMPLE", ha='center', fontweight='bold')
        ax.axis('off')
        st.pyplot(fig)
        plt.close(fig) # FIX: Prevents memory leak

def render_flownet():
    st.subheader("2D Flow Net Analysis")
    c1, c2 = st.columns([1, 1.5])
    
    with c1:
        st_type = st.radio("Structure", ["Concrete Dam", "Sheet Pile"])
        dim = st.number_input("Dimension (Width/Depth)", 5.0)
        h_up, h_dw = st.number_input("Upstream H", 10.0), st.number_input("Downstream H", 2.0)
        
        st.markdown("---")
        st.write("**Point Calculator**")
        px = st.number_input("X", 2.0)
        py = st.number_input("Y", -4.0, max_value=0.0)
        
        rh, rz, rp, ru = solve_flow_net_at_point(px, py, st_type, dim, h_up, h_dw)
        if rh:
            st.info(f"Point ({px}, {py}):\nu = {ru:.2f} kPa")
        else:
            st.warning("Invalid Point (Inside Structure)")
            
        st.markdown("---")
        k = st.number_input("k [m/day]", 0.0864)
        nf, nd = st.number_input("Nf", 4), st.number_input("Nd", 12)
        if st.button("Calc Flow"):
            q = k * (h_up - h_dw) * (nf/nd)
            st.success(f"q = {q:.4f} m³/day/m")

    with c2:
        fig, ax = plt.subplots(figsize=(8, 6))
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
        ax.plot([-15, 15], [0, 0], 'k-')
        if rh: ax.scatter(px, py, c='red', marker='x', s=100, zorder=10)
        
        ax.set_ylim(-12, max(h_up, h_dw)+1); ax.set_xlim(-12, 12); ax.axis('off')
        st.pyplot(fig)
        plt.close(fig) # FIX: Prevents memory leak

# --- 3. MAIN APP (CALLED BY ROUTER) ---
def app():
    t1, t2, t3 = st.tabs(["1D Seepage", "Permeability", "2D Flow Net"])
    with t1: render_seepage()
    with t2: render_permeability()
    with t3: render_flownet()
