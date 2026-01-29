import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# =========================================================
# CONSTANTS
# =========================================================
GAMMA_W = 9.81

def app():
    st.title("Lateral Earth Pressure Calculator 🧱")
    st.markdown("---")
    
    tab_rankine, tab_coulomb = st.tabs(
        ["1. Rankine's Theory (Wall Profile)", "2. Coulomb's Wedge Theory"]
    )

    # =========================================================================
    # TAB 1: RANKINE
    # =========================================================================
    with tab_rankine:
        st.header("Rankine Analysis: Retaining Wall Profile")

        c1, c2 = st.columns(2)
        wall_height = c1.number_input("Wall Height (m)", 1.0, 30.0, 9.0)
        excavation_depth = c2.number_input("Excavation Depth (m)", 0.0, wall_height, 4.5)

        col_L, col_R = st.columns(2)

        def render_layers(prefix, defaults):
            layers = []
            z = 0.0
            n = st.number_input(f"Layers ({prefix})", 1, 5, len(defaults), key=f"{prefix}_n")
            for i in range(int(n)):
                with st.expander(f"Layer {i+1}", True):
                    h = st.number_input("H (m)", 0.1, 20.0, defaults[i]["H"], key=f"{prefix}_h{i}")
                    g = st.number_input("γ (kN/m³)", 10.0, 25.0, defaults[i]["g"], key=f"{prefix}_g{i}")
                    p = st.number_input("ϕ' (deg)", 0.0, 45.0, defaults[i]["p"], key=f"{prefix}_p{i}")
                    c = st.number_input("c' (kPa)", 0.0, 50.0, defaults[i]["c"], key=f"{prefix}_c{i}")

                    layers.append({
                        "id": i+1, "H": h, "gamma": g,
                        "phi": p, "c": c,
                        "top": z, "bottom": z + h
                    })
                    z += h
            return layers

        with col_L:
            st.subheader("⬅ Passive Side")
            left_wt = st.number_input("WT Depth (m)", 0.0, 20.0, 1.5)
            left_layers = render_layers("L", [
                {"H":1.5,"g":18,"p":38,"c":0},
                {"H":3.0,"g":20,"p":28,"c":10}
            ])

        with col_R:
            st.subheader("➡ Active Side")
            right_q = st.number_input("Surcharge q (kPa)", 0.0, 100.0, 50.0)
            right_wt = st.number_input("WT Depth (m)", 0.0, 20.0, 6.0)
            right_layers = render_layers("R", [
                {"H":6.0,"g":18,"p":38,"c":0},
                {"H":3.0,"g":20,"p":28,"c":10}
            ])

        # =====================================================
        # CORE CALCULATION (FIXED)
        # =====================================================
        def calculate_stress(z, layers, wt, surcharge, mode):
            sig_v = surcharge
            active = layers[-1]

            for l in layers:
                if z <= l["bottom"]:
                    sig_v += (z - l["top"]) * l["gamma"]
                    active = l
                    break
                sig_v += l["H"] * l["gamma"]

            u = max(0.0, (z - wt) * GAMMA_W)
            sig_eff = sig_v - u

            phi = np.radians(active["phi"])
            c = active["c"]

            if mode == "Active":
                K = (1 - np.sin(phi)) / (1 + np.sin(phi))
                sig_lat_eff = sig_eff * K - 2 * c * np.sqrt(K)
            else:
                K = (1 + np.sin(phi)) / (1 - np.sin(phi))
                sig_lat_eff = sig_eff * K + 2 * c * np.sqrt(K)

            sig_lat_eff = max(0.0, sig_lat_eff)
            return sig_lat_eff + u, K, active["id"]

        # =====================================================
        # PLOT
        # =====================================================
        fig, ax = plt.subplots(figsize=(10, 8))
        w = 0.8

        ax.add_patch(patches.Rectangle((-w/2, 0), w, wall_height,
                                       facecolor="lightgrey", edgecolor="black"))

        YT = wall_height
        YE = wall_height - excavation_depth
        scale = 0.05

        y = np.linspace(0, wall_height, 60)
        pr = [calculate_stress(d, right_layers, right_wt, right_q, "Active")[0] for d in y]
        ax.fill_betweenx(YT - y, w/2, w/2 + np.array(pr)*scale, color="red", alpha=0.3)

        yl = np.linspace(0, wall_height - excavation_depth, 60)
        pl = [calculate_stress(d, left_layers, left_wt, 0, "Passive")[0] for d in yl]
        ax.fill_betweenx(YE - yl, -w/2, -w/2 - np.array(pl)*scale, color="green", alpha=0.3)

        ax.set_xlim(-7, 7)
        ax.set_ylim(-1, wall_height + 1)
        ax.axis("off")
        st.pyplot(fig)

    # =========================================================================
    # TAB 2: COULOMB (SAFE)
    # =========================================================================
    with tab_coulomb:
        st.header("Coulomb's Wedge Theory")

        phi = np.radians(st.number_input("ϕ (deg)", 20.0, 45.0, 30.0))
        delta = np.radians(st.number_input("δ (deg)", 0.0, 30.0, 15.0))
        H = st.number_input("Wall Height (m)", 1.0, 20.0, 5.0)
        gamma = st.number_input("γ (kN/m³)", 10.0, 25.0, 18.0)

        denom = max(1e-6, np.cos(delta))
        Ka = (np.cos(phi - delta)**2) / denom
        Pa = 0.5 * gamma * H**2 * Ka

        st.metric("Ka", f"{Ka:.3f}")
        st.metric("Pa", f"{Pa:.2f} kN/m")

if __name__ == "__main__":
    app()
