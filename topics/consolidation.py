import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

def consolidation_page():
    st.header("⏱️ Consolidation & Settlement Analysis")
    st.markdown("""
    This module is divided into two parts:
    1.  **Lab Analysis:** Determine the Coefficient of Consolidation ($c_v$) using lab data.
    2.  **Field Settlement:** Calculate ultimate settlement and time-rate settlement using field parameters.
    """)
    
    st.divider()

    # =================================================================
    # PART 1: DETERMINATION OF Cv (Lab Data)
    # =================================================================
    st.subheader("1. Laboratory Determination of $c_v$")
    st.info("Select the graphical method used in your laboratory test to determine the Coefficient of Consolidation.")

    # User Selection: Method
    cv_method = st.radio(
        "Which method are you using?",
        ["Casagrande Method (Log-Time)", "Taylor Method (Square-Root-Time)"],
        horizontal=True
    )

    col_lab1, col_lab2 = st.columns(2)
    
    with col_lab1:
        # Lab Sample Inputs
        d_lab_mm = st.number_input("Sample Thickness at 50% consolidation (H_lab) [mm]", value=20.0, step=0.1)
        drainage_lab = st.selectbox("Lab Drainage Condition", ["Double Drainage (Top & Bottom)", "Single Drainage"])
        
        # Calculate drainage path 'd' or 'Hdr' for lab
        if drainage_lab == "Double Drainage (Top & Bottom)":
            Hdr_lab = (d_lab_mm / 2) / 1000 # convert to meters
            st.caption(f"Drainage path $d = H/2 = {Hdr_lab*1000:.2f}$ mm")
        else:
            Hdr_lab = d_lab_mm / 1000 # convert to meters
            st.caption(f"Drainage path $d = H = {Hdr_lab*1000:.2f}$ mm")

    with col_lab2:
        # Method Specific Inputs
        if "Casagrande" in cv_method:
            st.markdown("**Casagrande Method Inputs**")
            t_50 = st.number_input("Time for 50% consolidation ($t_{50}$) [min]", value=10.0, step=0.1)
            # Formula: Tv=0.196, Cv = (0.196 * d^2) / t50
            # Convert t50 to years for consistency with typical geotechnical units (m2/year) 
            # or keep in m2/min. Let's output both.
            if t_50 > 0:
                cv_val = (0.196 * (Hdr_lab**2)) / t_50 # m2/min
                method_cite = "Tv = 0.196 for 50% Consolidation"
            else:
                cv_val = 0
                
        else: # Taylor Method
            st.markdown("**Taylor Method Inputs**")
            t_90 = st.number_input("Time for 90% consolidation ($t_{90}$) [min]", value=25.0, step=0.1)
            # Formula: Tv=0.848, Cv = (0.848 * d^2) / t90
            if t_90 > 0:
                cv_val = (0.848 * (Hdr_lab**2)) / t_90 # m2/min
                method_cite = "Tv = 0.848 for 90% Consolidation"
            else:
                cv_val = 0

    # Display Cv Results
    if cv_val > 0:
        cv_year = cv_val * 60 * 24 * 365 # Convert m2/min to m2/year
        st.success(f"**Calculated Coefficient of Consolidation ($c_v$):**")
        st.latex(f"c_v = {cv_val:.6f} \, m^2/min = {cv_year:.4f} \, m^2/year")
        st.caption(f"Based on {method_cite}")
    
    st.divider()

    # =================================================================
    # PART 2: FIELD SETTLEMENT (Smart Logic)
    # =================================================================
    st.subheader("2. Field Settlement Analysis")
    st.write("Enter the soil profile parameters. The system will automatically identify the soil state (NC vs OC) and apply the correct settlement formula.")

    col_field1, col_field2, col_field3 = st.columns(3)

    with col_field1:
        st.markdown("##### Soil Properties")
        H_field = st.number_input("Field Layer Thickness (H) [m]", value=5.0)
        e0 = st.number_input("Initial Void Ratio ($e_0$)", value=0.85)
        Cc = st.number_input("Compression Index ($C_c$)", value=0.32)
        Cr = st.number_input("Recompression Index ($C_r$)", value=0.05)
        
    with col_field2:
        st.markdown("##### Stress State")
        sigma_v0 = st.number_input("Initial Effective Stress ($\sigma'_0$) [kPa]", value=118.0)
        sigma_p = st.number_input("Preconsolidation Pressure ($\sigma'_p$) [kPa]", value=118.0)
        delta_sigma = st.number_input("Stress Increase ($\Delta\sigma$) [kPa]", value=60.0)

    with col_field3:
        st.markdown("##### Time Rate Params")
        # Allow user to use calculated Cv or override
        use_calc_cv = st.checkbox("Use calculated $c_v$ from Part 1?", value=True)
        if use_calc_cv:
            cv_field = cv_year
            st.write(f"$c_v = {cv_field:.4f} \, m^2/year$")
        else:
            cv_field = st.number_input("Enter Field $c_v$ [$m^2/year$]", value=2.0)
            
        drainage_field = st.selectbox("Field Drainage", ["Double (Top & Bottom)", "Single (Top or Bottom)"])
        Hdr_field = H_field / 2 if "Double" in drainage_field else H_field

    # --- CRITICAL THINKING / LOGIC ---
    sigma_final = sigma_v0 + delta_sigma
    settlement = 0.0
    status_msg = ""
    formula_latex = ""

    # Logic Tree for Settlement Calculation
    if sigma_v0 >= sigma_p:
        # Case: Normally Consolidated (NC)
        # Even if sigma_v0 > sigma_p (which is technically impossible in nature without recent unloading, 
        # we treat it as NC if it's on the virgin curve).
        case_type = "Normally Consolidated (NC)"
        
        # Calculate NC Settlement
        settlement = (Cc * H_field / (1 + e0)) * np.log10(sigma_final / sigma_v0)
        
        status_msg = f"Since $\sigma'_0 ({sigma_v0}) \approx \sigma'_p ({sigma_p})$, the soil is **Normally Consolidated**."
        formula_latex = r"S_c = \frac{C_c H}{1+e_0} \log \left( \frac{\sigma'_0 + \Delta\sigma}{\sigma'_0} \right)"
        
    else:
        # Case: Over Consolidated (OC)
        if sigma_final <= sigma_p:
            # Case 1: Recompression Only
            case_type = "Over-Consolidated (Case 1: Recompression)"
            
            settlement = (Cr * H_field / (1 + e0)) * np.log10(sigma_final / sigma_v0)
            
            status_msg = f"Since $\sigma'_0 < \sigma'_p$ AND $\sigma'_{{final}} ({sigma_final}) < \sigma'_p ({sigma_p})$, the soil remains in the **recompression range**."
            formula_latex = r"S_c = \frac{C_r H}{1+e_0} \log \left( \frac{\sigma'_0 + \Delta\sigma}{\sigma'_0} \right)"
            
        else:
            # Case 2: Recompression + Compression
            case_type = "Over-Consolidated (Case 2: Preconsolidation Exceeded)"
            
            term1 = (Cr * H_field / (1 + e0)) * np.log10(sigma_p / sigma_v0)
            term2 = (Cc * H_field / (1 + e0)) * np.log10(sigma_final / sigma_p)
            settlement = term1 + term2
            
            status_msg = f"Since $\sigma'_0 < \sigma'_p$ BUT $\sigma'_{{final}} ({sigma_final}) > \sigma'_p ({sigma_p})$, the soil undergoes **both recompression and virgin compression**."
            formula_latex = r"S_c = \frac{C_r H}{1+e_0} \log \left( \frac{\sigma'_p}{\sigma'_0} \right) + \frac{C_c H}{1+e_0} \log \left( \frac{\sigma'_0 + \Delta\sigma}{\sigma'_p} \right)"

    # --- RESULTS DISPLAY ---
    st.markdown("#### 📊 Analysis Results")
    
    # 1. Classification Result
    st.info(f"**Identified State:** {case_type}")
    st.write(status_msg)
    
    # 2. Ultimate Settlement Result
    col_res1, col_res2 = st.columns(2)
    with col_res1:
        st.metric("Total Ultimate Settlement ($S_c$)", f"{settlement*1000:.2f} mm", help=f"{settlement:.4f} m")
    with col_res2:
        st.latex(formula_latex)

    # 3. Time Rate Calculation
    st.markdown("#### ⏳ Time-Rate Predictions")
    
    time_calc_mode = st.radio("Calculate:", ["Time required for X% Settlement", "Settlement amount after Y years"], horizontal=True)
    
    if time_calc_mode == "Time required for X% Settlement":
        U_target = st.slider("Target Consolidation Ratio (U%)", 10, 99, 90)
        U_decimal = U_target / 100.0
        
        # Calculate Tv based on U (Note formulas from slides)
        if U_decimal <= 0.60:
            Tv = (np.pi / 4) * (U_decimal ** 2)
        else:
            Tv = -0.933 * np.log10(1 - U_decimal) - 0.085
            
        # Calculate time: t = (Tv * d^2) / Cv
        if cv_field > 0:
            t_years = (Tv * (Hdr_field**2)) / cv_field
            st.metric(f"Time required for {U_target}% Consolidation", f"{t_years:.2f} years")
        else:
            st.error("Cv must be greater than 0")
            
    else:
        t_user = st.number_input("Time duration [years]", value=1.0)
        
        # Calculate Tv: Tv = Cv * t / d^2
        if Hdr_field > 0:
            Tv_calc = (cv_field * t_user) / (Hdr_field**2)
            
            # Inverse Tv to get U
            # Approximation for U from Tv is complex to inverse exactly for U>60%, 
            # but we can use the approximation equations:
            # If Tv < 0.286 (approx U=60%), U = sqrt(4Tv/pi)
            if Tv_calc < 0.283: # Using 0.283 boundary roughly
                U_calc = np.sqrt((4 * Tv_calc) / np.pi)
            else:
                # Inverse of: Tv = -0.933 log(1-U) - 0.085
                # (Tv + 0.085) / -0.933 = log10(1-U)
                # 10^ANS = 1-U  => U = 1 - 10^ANS
                exponent = (Tv_calc + 0.085) / -0.933
                U_calc = 1 - (10**exponent)
                
            # Cap U at 100%
            if U_calc > 1.0: U_calc = 1.0
            
            settlement_at_t = settlement * U_calc
            
            st.metric(f"Degree of Consolidation at {t_user} years", f"{U_calc*100:.1f} %")
            st.metric(f"Settlement at {t_user} years", f"{settlement_at_t*1000:.2f} mm")

if __name__ == "__main__":
    consolidation_page()
