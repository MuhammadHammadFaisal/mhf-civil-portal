import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. INPUT MANAGER
# ==========================================
def render_inputs(section_type, goal):
    """
    Renders inputs dynamically based on the 'Professor's Question'.
    """
    data = {}
    
    # --- COMMON SYSTEM PROPERTIES (Always visible) ---
    st.markdown("### 2. System Properties")
    c1, c2 = st.columns(2)
    with c1:
        # If finding 'd', we don't ask for 'h' or 'd'
        if "Depth (d)" in goal:
            data['b'] = st.number_input("Width (b) [mm]", value=300.0)
            data['cover'] = st.number_input("Cover [mm]", value=30.0)
        else:
            data['b'] = st.number_input("Width (b) [mm]", value=300.0)
            data['h'] = st.number_input("Height (h) [mm]", value=500.0)
            data['cover'] = st.number_input("Cover [mm]", value=30.0)
            data['d'] = data['h'] - data['cover']
            
    with c2:
        # If finding Concrete Class, we don't ask for fck
        if "Concrete Class" in goal:
            data['fyk'] = st.selectbox("Steel Grade", [220, 420, 500], index=1)
        else:
            data['fck'] = st.selectbox("Concrete Class", [20, 25, 30, 35, 40, 50], index=2)
            data['fyk'] = st.selectbox("Steel Grade", [220, 420, 500], index=1)

    st.markdown("---")
    st.markdown(f"### 3. Problem Variables")

    # --- SPECIFIC VARIABLES ---
    
    # === SINGLY REINFORCED ===
    if section_type == "Singly Reinforced":
        
        if goal == "Find Moment Capacity (Mr)":
            st.info("Input the reinforcement to find the max moment.")
            data['As'] = st.number_input("Tension Steel (As) [mm²]", value=1257.0)
            
        elif goal == "Find Neutral Axis (c) & Strain":
            st.info("Calculate c, εs, and check ductility.")
            data['As'] = st.number_input("Tension Steel (As) [mm²]", value=1257.0)
            
        elif goal == "Design Steel Area (As)":
            st.info("Input the Load (Moment) to find required Steel.")
            data['Md'] = st.number_input("Design Moment (Md) [kNm]", value=250.0)
            
        elif goal == "Find Minimum Depth (d)":
            st.info("Input Load and Steel Ratio to find Beam Size.")
            data['Md'] = st.number_input("Design Moment (Md) [kNm]", value=250.0)
            data['rho'] = st.slider("Target Steel Ratio (ρ)", 0.005, 0.020, 0.010, format="%.3f")
            
        elif goal == "Find Concrete Class (fck)":
            st.info("What concrete grade is needed for this load?")
            data['Md'] = st.number_input("Target Moment (Md) [kNm]", value=300.0)
            data['As'] = st.number_input("Provided Steel (As) [mm²]", value=2000.0)

    # === DOUBLY REINFORCED ===
    elif section_type == "Doubly Reinforced":
        data['As_comp'] = st.number_input("Compression Steel (As') [mm²]", value=400.0)
        
        if "Capacity" in goal:
            data['As'] = st.number_input("Tension Steel (As) [mm²]", value=1800.0)
        elif "Tension Steel" in goal:
            data['Md'] = st.number_input("Design Moment (Md) [kNm]", value=450.0)

    return data

# ==========================================
# 2. MAIN APP
# ==========================================
def app():
    st.title("TS 500 Flexure Solver")
    st.markdown("Select the variable the professor is asking you to solve for.")

    # STEP 1: WIZARD SETUP
    col_type, col_goal = st.columns(2)
    
    with col_type:
        section_type = st.radio("Section Type", ["Singly Reinforced", "Doubly Reinforced", "Multi-Layer"])
    
    with col_goal:
        # These match the Professor's likely exam questions
        if section_type == "Singly Reinforced":
            options = [
                "Find Moment Capacity (Mr)",
                "Find Neutral Axis (c) & Strain",
                "Design Steel Area (As)",
                "Find Minimum Depth (d)",
                "Find Concrete Class (fck)"
            ]
        elif section_type == "Doubly Reinforced":
            options = [
                "Find Moment Capacity (Mr)",
                "Find Tension Steel (As)"
            ]
        else:
            options = ["Find Moment Capacity (Mr)"]
            
        goal = st.selectbox("What needs to be calculated?", options)

    # STEP 2: RENDER
    inputs = render_inputs(section_type, goal)

    # STEP 3: SOLVE
    if st.button("Solve", type="primary"):
        st.divider()
        st.subheader("Solution")
        
        # Placeholder for Logic Integration
        # We will connect the logic file here in the next step
        st.success(f"Solving for **{goal}**...")
        st.write("Parameters:", inputs)
        
        # Example of what the output will look like (Hardcoded for Demo)
        if "Neutral Axis" in goal:
            st.latex(r"c = \frac{A_s f_{yd}}{0.85 f_{cd} b} = \dots \text{ mm}")
            st.pyplot(plt.figure(figsize=(4,2))) # Placeholder graph

if __name__ == "__main__":
    app()
