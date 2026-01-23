import streamlit as st
import numpy as np

def app():
    st.markdown("---")
    st.subheader("💧 Flow of Water & Permeability")
    
    # Create Tabs for different note sections
    tab1, tab2, tab3 = st.tabs(["🧪 Permeability (Lab Tests)", "🕸️ Flow Nets (2D Flow)", "⚠️ Quick Condition (Boiling)"])

    # ==========================================
    # TAB 1: PERMEABILITY TESTS (Pages 35-36)
    # ==========================================
    with tab1:
        st.markdown("Calculate **Coefficient of Permeability ($k$)** from Lab Data.")
        
        test_type = st.radio("Select Test Type:", ["Constant Head Test (Coarse Soil)", "Falling Head Test (Fine Soil)"])
        
        if "Constant" in test_type:
            st.latex(r"k = \frac{Q \cdot L}{A \cdot \Delta H \cdot t}")
            
            c1, c2 = st.columns(2)
            Q = c1.number_input("Volume of Water Collected (Q) [cm³]", 0.0, step=10.0)
            L = c2.number_input("Length of Soil Sample (L) [cm]", 0.0, step=1.0)
            A = c1.number_input("Area of Soil Sample (A) [cm²]", 0.0, step=1.0)
            dH = c2.number_input("Head Difference (ΔH) [cm]", 0.0, step=1.0)
            t = c1.number_input("Time Elapsed (t) [sec]", 0.0, step=1.0)
            
            if st.button("Calculate k (Constant Head)"):
                if A * dH * t > 0:
                    k = (Q * L) / (A * dH * t)
                    st.success(f"✅ Coefficient of Permeability, k = **{k:.4e} cm/sec**")
                else:
                    st.error("Please fill all fields (A, ΔH, t cannot be zero).")

        else: # Falling Head
            st.latex(r"k = \frac{a \cdot L}{A \cdot \Delta t} \ln\left(\frac{h_1}{h_2}\right)")
            
            c1, c2 = st.columns(2)
            a_tube = c1.number_input("Area of Standpipe (a) [cm²]", 0.0, step=0.1, format="%.4f")
            A_soil = c2.number_input("Area of Soil Sample (A) [cm²]", 0.0, step=1.0)
            L = c1.number_input("Length of Soil Sample (L) [cm]", 0.0, step=1.0)
            t = c2.number_input("Time Elapsed (Δt) [sec]", 0.0, step=1.0)
            h1 = c1.number_input("Initial Head (h1) [cm]", 0.0, step=1.0)
            h2 = c2.number_input("Final Head (h2) [cm]", 0.0, step=1.0)
            
            if st.button("Calculate k (Falling Head)"):
                if A_soil * t > 0 and h1 > h2 and h2 > 0:
                    # Logic: ln(h1/h2)
                    k = ((a_tube * L) / (A_soil * t)) * np.log(h1 / h2)
                    st.success(f"✅ Coefficient of Permeability, k = **{k:.4e} cm/sec**")
                else:
                    st.error("Check inputs: h1 must be > h2, and values cannot be zero.")

    # ==========================================
    # TAB 2: FLOW NETS (Page 44)
    # ==========================================
    with tab2:
        st.markdown("Calculate Seepage Rate ($q$) under a Dam/Sheet Pile.")
        st.latex(r"q = k \cdot H \cdot \frac{N_f}{N_d}")
        
        col1, col2 = st.columns(2)
        k_val = col1.number_input("Permeability (k) [m/day or similar]", 0.0, format="%.5f")
        H_loss = col2.number_input("Total Head Loss (H) [m]", 0.0, step=0.5)
        
        c1, c2 = st.columns(2)
        Nf = c1.number_input("Number of Flow Channels (Nf)", 0.0, step=1.0)
        Nd = c2.number_input("Number of Equipotential Drops (Nd)", 0.0, step=1.0)
        
        if st.button("Calculate Seepage (q)"):
            if Nd > 0:
                q = k_val * H_loss * (Nf / Nd)
                st.metric("Total Seepage (q)", f"{q:.4f} units³/time")
                st.info("Note: This is per unit length of the structure.")
            else:
                st.error("Nd (Drops) cannot be zero.")

    # ==========================================
    # TAB 3: QUICK CONDITION (Page 38)
    # ==========================================
    with tab3:
        st.markdown("Check for **Boiling / Quick Sand** Condition (Upward Flow).")
        st.caption("Boiling occurs when Effective Stress = 0")
        
        st.latex(r"i_{cr} = \frac{\gamma'}{\gamma_w} = \frac{G_s - 1}{1+e}")
        
        c1, c2 = st.columns(2)
        Gs = c1.number_input("Specific Gravity (Gs)", 2.65, step=0.01)
        e = c2.number_input("Void Ratio (e)", 0.60, step=0.01)
        
        if st.button("Calculate Critical Gradient"):
            icr = (Gs - 1) / (1 + e)
            st.metric("Critical Hydraulic Gradient (i_cr)", f"{icr:.3f}")
            
            st.markdown("---")
            st.write("**Check Safety:**")
            i_actual = st.number_input("Actual Hydraulic Gradient (i) on site", 0.0, step=0.1)
            
            if i_actual > 0:
                FS = icr / i_actual
                st.latex(rf"FS = \frac{{i_{{cr}}}}{{i_{{actual}}}} = {FS:.2f}")
                
                if FS < 1.0:
                    st.error("❌ DANGER: Boiling / Quick Sand will occur!")
                else:
                    st.success("✅ Stable Condition.")
