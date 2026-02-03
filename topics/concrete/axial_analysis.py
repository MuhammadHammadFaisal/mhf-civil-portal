import streamlit as st
import numpy as np

def app():
    st.header("🏗️ Analysis of Axial Load Capacity")
    st.markdown("---")

    # --- 1. SIDEBAR CONFIGURATION ---
    st.sidebar.header("⚙️ Design Parameters")
    
    design_code = st.sidebar.selectbox(
        "Select Design Code:",
        ["ACI 318-19 (USA/Gulf)", "Eurocode 2 (Turkey/EU)"]
    )

    shape = st.sidebar.selectbox(
        "Select Column Shape:",
        ["Rectangular", "Square", "Circular"]
    )

    # --- 2. INPUT SECTION ---
    st.subheader("1. Input Data")
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Material Properties**")
        fc = st.number_input("Concrete Strength (f'c / fck) [MPa]", min_value=10.0, value=30.0, step=5.0)
        fy = st.number_input("Steel Yield Strength (fy / fyk) [MPa]", min_value=200.0, value=420.0, step=10.0)

    with col2:
        st.markdown("**Geometry**")
        if shape == "Rectangular":
            width = st.number_input("Width (b) [mm]", min_value=100.0, value=300.0, step=50.0)
            depth = st.number_input("Depth (h) [mm]", min_value=100.0, value=500.0, step=50.0)
            Ag = width * depth
        elif shape == "Square":
            side = st.number_input("Side Dimension (a) [mm]", min_value=100.0, value=400.0, step=50.0)
            Ag = side * side
        else: # Circular
            diameter = st.number_input("Diameter (D) [mm]", min_value=100.0, value=400.0, step=50.0)
            Ag = (np.pi * diameter**2) / 4

    with col3:
        st.markdown("**Reinforcement**")
        bar_dia = st.number_input("Bar Diameter [mm]", min_value=8.0, value=20.0, step=2.0)
        num_bars = st.number_input("Number of Bars", min_value=4, value=6, step=2)
        
        # Calculate Steel Area
        Ast = num_bars * (np.pi * (bar_dia/2)**2)
        
        # Reinforcement Ratio Check
        rho = Ast / Ag
        rho_percent = rho * 100

    # Display Calculated Areas immediately for verification
    st.info(f"GROSS AREA ($A_g$): **{Ag:,.0f} mm²** | STEEL AREA ($A_{{st}}$): **{Ast:,.0f} mm²** | RATIO ($\rho$): **{rho_percent:.2f}%**")

    # --- 3. CALCULATION LOGIC ---
    
    st.subheader("2. Detailed Calculation")

    if st.button("Calculate Capacity", type="primary"):
        
        st.markdown("### Step-by-Step Report")

        # ==========================================
        # LOGIC FOR ACI 318-19
        # ==========================================
        if "ACI 318" in design_code:
            st.success("Selected Standard: **ACI 318-19**")

            # Determine Factors based on Shape (Ties vs Spirals)
            if shape == "Circular":
                confinement_type = "Spiral"
                phi = 0.75
                alpha = 0.85
            else:
                confinement_type = "Tied"
                phi = 0.65
                alpha = 0.80

            # 1. Nominal Strength (Pn)
            # Pn = 0.85 * f'c * (Ag - Ast) + fy * Ast
            Pn_concrete_part = 0.85 * fc * (Ag - Ast)
            Pn_steel_part = fy * Ast
            Pn_newton = Pn_concrete_part + Pn_steel_part
            Pn_kN = Pn_newton / 1000

            # 2. Design Strength (phi Pn)
            # phi Pn(max) = alpha * phi * Pn
            PhiPn_kN = alpha * phi * Pn_kN

            # --- DISPLAY ACI RESULTS ---
            
            with st.expander("ℹ️ Understanding ACI Factors (Click to learn)"):
                st.write(f"""
                * **Confinement Type:** {confinement_type} (Determined by shape)
                * **Phi ($\phi$):** {phi} (Strength Reduction Factor). ACI uses 0.65 for tied columns (rectangular) and 0.75 for spirals because spirals are more ductile.
                * **Alpha ($\\alpha$):** {alpha} (Eccentricity Factor). This accounts for accidental moments.
                """)

            st.markdown("**Step A: Calculate Nominal Axial Strength ($P_n$)**")
            st.latex(r"P_n = 0.85 f'_c (A_g - A_{st}) + f_y A_{st}")
            st.write(f"Substitution:")
            st.latex(fr"P_n = 0.85 ({fc}) ({Ag:.0f} - {Ast:.0f}) + {fy} ({Ast:.0f})")
            st.write(f"Calculated $P_n$ = **{Pn_kN:,.2f} kN**")

            st.markdown("---")

            st.markdown("**Step B: Apply Safety Factors ($\phi$ and $\\alpha$)**")
            st.latex(r"\phi P_{n(max)} = \alpha \cdot \phi \cdot P_n")
            st.write(f"For {confinement_type} columns: $\\alpha$ = {alpha}, $\phi$ = {phi}")
            st.latex(fr"\phi P_{n(max)} = {alpha} \cdot {phi} \cdot {Pn_kN:.2f}")
            
            st.markdown(f"### ✅ Design Axial Capacity: **{PhiPn_kN:,.2f} kN**")

        # ==========================================
        # LOGIC FOR EUROCODE 2
        # ==========================================
        else:
            st.success("Selected Standard: **Eurocode 2**")
            
            # Partial Safety Factors
            gamma_c = 1.5  # Concrete
            gamma_s = 1.15 # Steel
            alpha_cc = 0.85 # Long term effects (standard value, sometimes 1.0 depending on National Annex)

            # Design Strengths
            fcd = (alpha_cc * fc) / gamma_c
            fyd = fy / gamma_s

            # N_Rd Formula
            # NRd = fcd * Ac + fyd * As
            # Ac = Ag - Ast (Net concrete area)
            Ac = Ag - Ast
            
            Nrd_concrete = fcd * Ac
            Nrd_steel = fyd * Ast
            Nrd_total_N = Nrd_concrete + Nrd_steel
            Nrd_kN = Nrd_total_N / 1000

            # --- DISPLAY EUROCODE RESULTS ---
            
            with st.expander("ℹ️ Understanding Eurocode Factors (Click to learn)"):
                st.write(f"""
                * **$\gamma_c$ (Gamma C):** {gamma_c} (Safety factor for concrete)
                * **$\gamma_s$ (Gamma S):** {gamma_s} (Safety factor for steel)
                * **$\\alpha_{{cc}}$:** {alpha_cc} (Coefficient for long-term effects and load duration)
                """)

            st.markdown("**Step A: Calculate Design Material Strengths**")
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.latex(r"f_{cd} = \frac{\alpha_{cc} f_{ck}}{\gamma_c}")
                st.write(f"$f_{{cd}} = ({alpha_cc} \\cdot {fc}) / {gamma_c} = $ **{fcd:.2f} MPa**")
            with col_res2:
                st.latex(r"f_{yd} = \frac{f_{yk}}{\gamma_s}")
                st.write(f"$f_{{yd}} = {fy} / {gamma_s} = $ **{fyd:.2f} MPa**")

            st.markdown("---")

            st.markdown("**Step B: Calculate Design Axial Resistance ($N_{Rd}$)**")
            st.latex(r"N_{Rd} = f_{cd} A_c + f_{yd} A_s")
            st.caption(f"*Note: $A_c$ is net concrete area ($A_g - A_s$)*")
            st.latex(fr"N_{{Rd}} = {fcd:.2f}({Ac:.0f}) + {fyd:.2f}({Ast:.0f})")
            
            st.markdown(f"### ✅ Design Axial Capacity ($N_{{Rd}}$): **{Nrd_kN:,.2f} kN**")
