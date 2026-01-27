import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

def app():
    st.header("🏗️ Consolidation: Field Settlement")
    st.markdown("""
    Calculate the ultimate primary consolidation settlement and time-rate settlement for clay layers.
    The interactive graph below visualizes the soil state relative to the preconsolidation pressure.
    """)
    
    st.divider()

    # =================================================================
    # INPUT SECTION
    # =================================================================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("##### 1. Soil Properties")
        H_field = st.number_input("Layer Thickness (H) [m]", value=5.0)
        e0 = st.number_input("Initial Void Ratio ($e_0$)", value=0.85, format="%.3f")
        Cc = st.number_input("Compression Index ($C_c$)", value=0.32, format="%.3f")
        Cr = st.number_input("Recompression Index ($C_r$)", value=0.05, format="%.3f")
        
    with col2:
        st.markdown("##### 2. Stress State")
        sigma_v0 = st.number_input("Initial Effective Stress ($\sigma'_0$) [kPa]", value=100.0)
        sigma_p = st.number_input("Preconsolidation Pressure ($\sigma'_p$) [kPa]", value=120.0)
        delta_sigma = st.number_input("Stress Increase ($\Delta\sigma$) [kPa]", value=50.0)

    with col3:
        st.markdown("##### 3. Drainage & Time")
        cv_field = st.number_input("Coeff. of Consolidation ($c_v$) [$m^2/year$]", value=2.0)
        drainage_type = st.selectbox("Drainage Condition", ["Double (Top & Bottom)", "Single (Top or Bottom)"])
        
        # Calculate Drainage Path
        if "Double" in drainage_type:
            Hdr = H_field / 2
            st.caption(f"Drainage path $d = H/2 = {Hdr:.2f}$ m")
        else:
            Hdr = H_field
            st.caption(f"Drainage path $d = H = {Hdr:.2f}$ m")

    st.divider()

    # =================================================================
    # CALCULATION LOGIC
    # =================================================================
    sigma_final = sigma_v0 + delta_sigma
    settlement = 0.0
    case_type = ""
    status_msg = ""
    
    # Logic Tree based on Lecture Notes [cite: 230-237]
    if sigma_v0 >= sigma_p:
        # Case: Normally Consolidated (NC)
        # Note: Ideally sigma_v0 can't be > sigma_p, but we treat it as NC if they are close or user input varies.
        case_type = "Normally Consolidated (NC)"
        status_msg = "Current stress is on the Virgin Compression Line."
        
        settlement = (Cc * H_field / (1 + e0)) * np.log10(sigma_final / sigma_v0)
        
        # For plotting: path is just straight down Cc line
        path_sigma = [sigma_v0, sigma_final]
        path_e = [e0, e0 - Cc * np.log10(sigma_final/sigma_v0)]
        
    else:
        # Case: Over Consolidated (OC)
        if sigma_final <= sigma_p:
            # Case 1: Recompression Only
            case_type = "OC Case 1: Recompression Only"
            status_msg = "Final stress is still below Preconsolidation Pressure."
            
            settlement = (Cr * H_field / (1 + e0)) * np.log10(sigma_final / sigma_v0)
            
            # For plotting: path is straight down Cr line
            path_sigma = [sigma_v0, sigma_final]
            path_e = [e0, e0 - Cr * np.log10(sigma_final/sigma_v0)]
            
        else:
            # Case 2: Recompression + Compression
            case_type = "OC Case 2: Recompression + Virgin Compression"
            status_msg = "Stress exceeds Preconsolidation Pressure; moving to Virgin Compression Line."
            
            term1 = (Cr * H_field / (1 + e0)) * np.log10(sigma_p / sigma_v0)
            term2 = (Cc * H_field / (1 + e0)) * np.log10(sigma_final / sigma_p)
            settlement = term1 + term2
            
            # For plotting: Two segments
            # Segment 1: sigma_v0 to sigma_p (slope Cr)
            e_p = e0 - Cr * np.log10(sigma_p/sigma_v0)
            # Segment 2: sigma_p to sigma_final (slope Cc)
            e_final = e_p - Cc * np.log10(sigma_final/sigma_p)
            
            path_sigma = [sigma_v0, sigma_p, sigma_final]
            path_e = [e0, e_p, e_final]

    # =================================================================
    # OUTPUT & VISUALIZATION
    # =================================================================
    col_res, col_plot = st.columns([1, 1.5])

    with col_res:
        st.subheader("Results")
        st.info(f"**State:** {case_type}")
        st.write(f"_{status_msg}_")
        
        st.metric(
            label="Total Primary Settlement ($S_c$)", 
            value=f"{settlement*1000:.2f} mm",
            help=f"Calculated value: {settlement:.4f} m"
        )
        
        # Time Rate Quick Calc
        st.markdown("#### ⏳ Time Rate")
        t_years = st.number_input("Years elapsed:", value=1.0, step=0.5)
        
        if cv_field > 0:
            Tv = (cv_field * t_years) / (Hdr**2)
            
            # Inverse Tv approximation
            if Tv < 0.283:
                U = np.sqrt((4 * Tv) / np.pi)
            else:
                U = 1 - (10 ** ((Tv + 0.085) / -0.933))
            
            if U > 1.0: U = 1.0
            
            st.metric(f"Settlement at {t_years} years", f"{(settlement * U)*1000:.2f} mm")
            st.caption(f"Degree of Consolidation $U = {U*100:.1f}\%$")
        else:
            st.warning("Enter $c_v > 0$ for time calculations.")

    with col_plot:
        st.subheader("Dynamic $e-\log \sigma'$ Curve")
        
        fig, ax = plt.subplots(figsize=(6, 4))
        
        # 1. Plot the "Background" Lines (Theoretical)
        # Create a range of stress for visualization
        x_range = np.logspace(np.log10(min(10, sigma_v0/2)), np.log10(max(1000, sigma_final*2)), 100)
        
        # Plot Virgin Compression Line (extending from sigma_p)
        # We need a reference point. If NC, ref is (sigma_v0, e0). If OC, ref is (sigma_p, e_p calculated).
        if sigma_v0 >= sigma_p:
            ref_sig, ref_e = sigma_v0, e0
        else:
            # Calculate e_p first
            ref_sig = sigma_p
            ref_e = e0 - Cr * np.log10(sigma_p/sigma_v0)
            
            # Plot Recompression Line (backward from sigma_p)
            # e = e_p + Cr * log(sigma_p / sigma) -> slope is negative in plot
            y_recomp = ref_e + Cr * np.log10(ref_sig / x_range)
            ax.plot(x_range, y_recomp, '--', color='green', alpha=0.3, label="Recompression Slope ($C_r$)")

        # Virgin Line equation: e = ref_e - Cc * log(sigma / ref_sig)
        y_virgin = ref_e - Cc * np.log10(x_range / ref_sig)
        ax.plot(x_range, y_virgin, '--', color='red', alpha=0.3, label="Virgin Slope ($C_c$)")
        
        # 2. Plot the Actual Stress Path (The "Dynamic" part)
        ax.plot(path_sigma, path_e, 'o-', color='blue', linewidth=2, markersize=8, label="Stress Path")
        
        # Annotate points
        ax.annotate('Start ($\sigma\'_0$)', xy=(path_sigma[0], path_e[0]), xytext=(5, 5), textcoords='offset points')
        ax.annotate('Final ($\sigma\'_f$)', xy=(path_sigma[-1], path_e[-1]), xytext=(5, -15), textcoords='offset points')
        
        if len(path_sigma) == 3: # If we have the break point at sigma_p
             ax.annotate('$\sigma\'_p$', xy=(path_sigma[1], path_e[1]), xytext=(5, 5), textcoords='offset points')

        # Formatting
        ax.set_xscale('log')
        ax.set_xlabel("Effective Stress $\sigma'$ (kPa) [Log Scale]")
        ax.set_ylabel("Void Ratio ($e$)")
        ax.grid(True, which="both", ls="-", alpha=0.2)
        ax.legend(loc='upper right', fontsize='small')
        
        st.pyplot(fig)

if __name__ == "__main__":
    app()
