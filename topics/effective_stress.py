import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def app():
    st.markdown("---")
    st.subheader("⬇️ Effective Stress Calculator")
    st.markdown(r"**Principle:** $\sigma' = \sigma_{total} - u$")

    # --- 1. SETUP SOIL PROFILE ---
    st.write("### 1. Soil Profile Setup")
    
    col1, col2 = st.columns(2)
    with col1:
        water_depth = st.number_input("Depth of Water Table (m)", min_value=0.0, step=0.5, value=2.0)
    with col2:
        surcharge = st.number_input("Surcharge Load (q) [kPa]", min_value=0.0, step=1.0, value=0.0)

    st.info("Define your soil layers from Top to Bottom:")
    
    # We create a simple input table for 3 layers
    layers = []
    
    # Layer 1
    with st.expander("Layer 1 (Top Layer)", expanded=True):
        c1, c2 = st.columns(2)
        h1 = c1.number_input("Thickness (H1) [m]", 0.0, step=0.1, key="h1")
        g1 = c2.number_input("Unit Weight (γ1) [kN/m³]", 0.0, step=0.1, key="g1")
        if h1 > 0: layers.append({"id": 1, "H": h1, "gamma": g1})

    # Layer 2
    with st.expander("Layer 2 (Middle Layer)"):
        c1, c2 = st.columns(2)
        h2 = c1.number_input("Thickness (H2) [m]", 0.0, step=0.1, key="h2")
        g2 = c2.number_input("Unit Weight (γ2) [kN/m³]", 0.0, step=0.1, key="g2")
        if h2 > 0: layers.append({"id": 2, "H": h2, "gamma": g2})

    # Layer 3
    with st.expander("Layer 3 (Bottom Layer)"):
        c1, c2 = st.columns(2)
        h3 = c1.number_input("Thickness (H3) [m]", 0.0, step=0.1, key="h3")
        g3 = c2.number_input("Unit Weight (γ3) [kN/m³]", 0.0, step=0.1, key="g3")
        if h3 > 0: layers.append({"id": 3, "H": h3, "gamma": g3})

    # --- 2. CALCULATION ENGINE ---
    if st.button("🚀 Calculate Stress Profile", type="primary"):
        if not layers:
            st.error("Please add at least one soil layer.")
            return

        # Initialize results list
        # Start at surface (z=0)
        results = [{'z': 0.0, 'sigma': surcharge, 'u': 0.0, 'sigma_p': surcharge}]
        
        current_depth = 0.0
        current_sigma = surcharge
        gamma_w = 9.81

        st.markdown("### 📝 Step-by-Step Calculation")

        for layer in layers:
            H = layer['H']
            gamma = layer['gamma']
            
            # Move to bottom of this layer
            current_depth += H
            
            # 1. Calculate Total Stress increment (Sigma = Sigma_prev + gamma * H)
            delta_sigma = gamma * H
            current_sigma += delta_sigma
            
            # 2. Calculate Pore Water Pressure (u)
            # u = (Depth - Water_Depth) * 9.81
            if current_depth > water_depth:
                # Calculate height of water column above this point
                h_w = current_depth - water_depth
                u = h_w * gamma_w
            else:
                u = 0.0
            
            # 3. Effective Stress
            sigma_p = current_sigma - u
            
            # Store result
            results.append({
                'z': current_depth,
                'sigma': current_sigma,
                'u': u,
                'sigma_p': sigma_p
            })

            # Display Step for this layer
            st.markdown(f"**At Depth z = {current_depth:.2f} m (Bottom of Layer {layer['id']}):**")
            
            # Math display
            st.latex(rf"\sigma = {results[-2]['sigma']:.2f} + ({gamma:.1f} \times {H:.1f}) = {current_sigma:.2f} \, \text{{kPa}}")
            
            if u > 0:
                st.latex(rf"u = ({current_depth:.2f} - {water_depth:.2f}) \times 9.81 = {u:.2f} \, \text{{kPa}}")
            else:
                st.latex(r"u = 0 \, \text{kPa (Above Water Table)}")
                
            st.latex(rf"\sigma' = {current_sigma:.2f} - {u:.2f} = \mathbf{{{sigma_p:.2f}}} \, \text{{kPa}}")
            st.divider()

        # --- 3. FINAL SUMMARY TABLE ---
        st.subheader("📊 Stress Distribution Table")
        df = pd.DataFrame(results)
        df.columns = ["Depth (z)", "Total Stress (σ)", "Pore Pressure (u)", "Effective Stress (σ')"]
        st.dataframe(df.style.format("{:.2f}"))

        # --- 4. PLOTTING (OPTIONAL BUT COOL) ---
        with st.expander("📈 View Stress Diagrams"):
            fig, ax = plt.subplots()
            # Plot Total
            ax.plot(df["Total Stress (σ)"], df["Depth (z)"], label="Total Stress (σ)", marker='o')
            # Plot Pore
            ax.plot(df["Pore Pressure (u)"], df["Depth (z)"], label="Pore Water (u)", linestyle='--', marker='x')
            # Plot Effective
            ax.plot(df["Effective Stress (σ')"], df["Depth (z)"], label="Effective Stress (σ')", linewidth=3, color='black')
            
            ax.set_ylim(max(df["Depth (z)"]), 0) # Invert Y axis so 0 is at top
            ax.set_xlabel("Stress (kPa)")
            ax.set_ylabel("Depth (m)")
            ax.legend()
            ax.grid(True)
            st.pyplot(fig)
