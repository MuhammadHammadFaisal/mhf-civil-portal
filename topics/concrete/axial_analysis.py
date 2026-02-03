# ... (Keep imports and helper functions as they are) ...

def app():
    st.header("🏗️ Analysis of Axial Load Capacity")
    st.markdown("---")

    col_input, col_viz = st.columns([1.2, 1])

    with col_input:
        st.subheader("1. Design Inputs")
        
        # ... (Inputs section remains exactly the same) ...
        # (I am summarizing here to save space, keep your existing Input code)
        with st.expander("⚙️ General Settings", expanded=True):
            design_code = st.selectbox("Design Code", ["ACI 318-19 (USA/Gulf)", "Eurocode 2 (EU/Turkey)"])
            shape = st.selectbox("Column Shape", ["Rectangular", "Square", "Circular"])
            
            if shape == "Circular":
                trans_type = st.radio("Transverse Reinforcement", ["Circular Ties", "Spiral"])
                st.caption(r"Spirals provide higher ductility ($\phi=0.75$) than Ties ($\phi=0.65$).") # FIXED: Added 'r'
            else:
                trans_type = "Ties"
                st.caption("Rectangular/Square columns use Ties.")

        st.markdown("**Material Properties**")
        c1, c2 = st.columns(2)
        with c1: fc = st.number_input("Concrete (f'c) [MPa]", value=30.0, step=5.0)
        with c2: fy = st.number_input("Steel (fy) [MPa]", value=420.0, step=10.0)

        st.markdown("**Geometry**")
        if shape == "Rectangular":
            cc1, cc2 = st.columns(2)
            with cc1: b = st.number_input("Width (b) [mm]", value=300.0, step=50.0)
            with cc2: h = st.number_input("Depth (h) [mm]", value=500.0, step=50.0)
            Ag = b * h
            dims = (b, h)
            viz_width = b 
        elif shape == "Square":
            a = st.number_input("Side (a) [mm]", value=400.0, step=50.0)
            Ag = a * a
            dims = (a,)
            viz_width = a
        else:
            D = st.number_input("Diameter (D) [mm]", value=400.0, step=50.0)
            Ag = np.pi * D**2 / 4
            dims = (D,)
            viz_width = D

        st.markdown("**Reinforcement**")
        rc1, rc2 = st.columns(2)
        with rc1:
            bar_dia = st.number_input("Bar Dia [mm]", value=20.0, step=2.0)
            num_bars = st.number_input("Total Bars", value=6, min_value=4, step=1)
        with rc2:
            tie_spacing = st.number_input(f"{trans_type} Spacing [mm]", value=150, step=25)

        Ast = num_bars * np.pi * (bar_dia / 2) ** 2
        rho = (Ast / Ag) * 100
        
        if rho < 1.0: st.warning(f"⚠️ Low Reinforcement: {rho:.2f}% (Min 1%)")
        elif rho > 8.0: st.warning(f"⚠️ High Reinforcement: {rho:.2f}% (Max 8%)")
        else: st.info(f"✅ Ratio: **{rho:.2f}%** ($A_s={Ast:,.0f}$ mm²)")

    with col_viz:
        st.subheader("2. Visualization")
        tab1, tab2 = st.tabs(["Cross-Section", "Elevation"])
        with tab1:
            fig1 = draw_cross_section(shape, dims, num_bars, bar_dia, trans_type)
            st.pyplot(fig1)
            plt.close(fig1) # FIXED: Explicitly close figure
            st.caption(f"Configuration: {shape} with {trans_type}")
        with tab2:
            fig2 = draw_side_view(viz_width, num_bars, tie_spacing, trans_type)
            st.pyplot(fig2)
            plt.close(fig2) # FIXED: Explicitly close figure

    st.markdown("---")

    st.subheader("3. Calculation Report")
    
    if st.button("Calculate Capacity", type="primary"):
        
        if "ACI 318" in design_code:
            st.success(f"Selected: **ACI 318-19** ({trans_type} Column)")

            if trans_type == "Spiral":
                phi = 0.75
                alpha = 0.85
                acc_ecc_msg = "Spirals = 0.85"
            else:
                phi = 0.65
                alpha = 0.80
                acc_ecc_msg = "Ties = 0.80"

            Pn_conc = 0.85 * fc * (Ag - Ast)
            Pn_steel = fy * Ast
            Pn_newton = Pn_conc + Pn_steel
            Pn_kN = Pn_newton / 1000 
            
            PhiPn_kN = alpha * phi * Pn_kN

            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown(r"### Peak 1: Theoretical Limit ($P_0$)") # FIXED: Added 'r'
                st.caption("Nominal Strength at zero eccentricity (The 'Pure' Peak)")
                st.latex(r"P_0 = 0.85 f'_c (A_g - A_{st}) + f_y A_{st}")
                st.write(f"This is the maximum load if the column is **perfectly** straight.")
                st.metric(label="Nominal Capacity (Pn)", value=f"{Pn_kN:,.0f} kN")
            
            with c2:
                st.markdown(r"### Peak 2: Design Limit ($\phi P_{n(max)}$)") # FIXED: Added 'r'
                st.caption("Practical limit considering safety & accidental eccentricity")
                st.latex(r"\phi P_{n(max)} = \alpha \cdot \phi \cdot P_0")
                
                # FIXED: Used double backslashes \\alpha and \\phi inside f-string
                st.write(f"**Factors Used:**")
                st.write(f"- $\\alpha = {alpha}$ ({acc_ecc_msg})")
                st.write(f"- $\\phi = {phi}$ ({trans_type})")
                
                st.latex(fr"\phi P_{{n(max)}} = {alpha} \cdot {phi} \cdot {Pn_kN:.0f}")
                
                st.metric(label="Design Capacity", value=f"{PhiPn_kN:,.0f} kN", delta="Final Value")

        else:
            st.success("Selected Standard: **Eurocode 2**")
            
            gamma_c, gamma_s = 1.5, 1.15
            alpha_cc = 0.85 
            
            fcd = (alpha_cc * fc) / gamma_c
            fyd = fy / gamma_s
            
            Ac = Ag - Ast
            Nrd_kN = (fcd * Ac + fyd * Ast) / 1000
            
            st.markdown(f"### Design Capacity ($N_{{Rd}}$): **{Nrd_kN:,.2f} kN**")
            st.caption("Eurocode applies safety factors to materials, not the final load.")
            st.latex(r"N_{Rd} = f_{cd} A_c + f_{yd} A_s")
