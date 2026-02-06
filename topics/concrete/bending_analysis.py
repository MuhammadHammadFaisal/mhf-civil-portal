import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. INPUT MANAGER (The "Smart" Part)
# ==========================================
def render_inputs(section_type, goal):
    """
    Dynamically renders inputs based on user selection.
    Returns a dictionary 'data' containing all user inputs.
    """
    data = {}
    
    st.markdown("### 2. System Properties")
    
    # --- COMMON INPUTS (Materials & Geometry) ---
    # These are needed for ALMOST every case, so we keep them standard
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Geometry**")
        data['b'] = st.number_input("Width (b) [mm]", value=300.0, step=50.0)
        data['h'] = st.number_input("Height (h) [mm]", value=500.0, step=50.0)
        data['cover'] = st.number_input("Cover [mm]", value=40.0)
        data['d'] = data['h'] - data['cover']
        
    with col2:
        st.markdown("**Materials**")
        data['fck'] = st.selectbox("Concrete (C)", [20, 25, 30, 35, 40, 45, 50], index=2)
        data['fyk'] = st.selectbox("Steel (S)", [220, 420, 500], index=1)

    st.markdown("---")
    st.markdown(f"### 3. {section_type} Specifics")

    # --- SPECIFIC INPUTS (Conditionals) ---
    
    # CASE A: SINGLY REINFORCED
    if section_type == "Singly Reinforced":
        if goal == "Calculate Capacity (Mr)":
            data['As'] = st.number_input("Tension Steel Area (As) [mm²]", value=1257.0)
        elif goal == "Design Steel (As)":
            data['Md'] = st.number_input("Design Moment (Md) [kNm]", value=200.0)
        elif goal == "Find Concrete (fck)":
            data['Md'] = st.number_input("Target Moment (Md) [kNm]", value=300.0)
            data['As'] = st.number_input("Provided Steel (As) [mm²]", value=2000.0)

    # CASE B: DOUBLY REINFORCED
    elif section_type == "Doubly Reinforced":
        # Always need compression steel for this analysis
        data['As_comp'] = st.number_input("Compression Steel (As') [mm²]", value=400.0)
        
        if goal == "Calculate Capacity (Mr)":
            data['As'] = st.number_input("Tension Steel (As) [mm²]", value=2000.0)
        elif goal == "Design Tension Steel (As)":
            data['Md'] = st.number_input("Design Moment (Md) [kNm]", value=400.0)

    # CASE C: MULTI-LAYER
    elif section_type == "Multi-Layer / Irregular":
        # Dynamic layer adder
        n_layers = st.number_input("Number of Layers", 1, 10, 3)
        layers = []
        for i in range(int(n_layers)):
            c1, c2 = st.columns(2)
            d_def = data['cover'] + (data['d']-data['cover'])*(i/(n_layers-1)) if n_layers>1 else data['d']
            ld = c1.number_input(f"Depth Layer {i+1}", value=float(d_def))
            las = c2.number_input(f"Area Layer {i+1}", value=500.0)
            layers.append({'d': ld, 'As': las})
        data['layers'] = layers

    return data

# ==========================================
# 2. MAIN APP FLOW
# ==========================================
def app():
    st.title("TS 500 Flexure Analysis")
    st.markdown("Step-by-step solver.")

    # STEP 1: SELECT TYPE
    st.markdown("### 1. Analysis Scope")
    col_type, col_goal = st.columns(2)
    
    with col_type:
        section_type = st.radio(
            "Section Type", 
            ["Singly Reinforced", "Doubly Reinforced", "Multi-Layer / Irregular"]
        )
    
    with col_goal:
        # Options change based on type
        if section_type == "Singly Reinforced":
            goal_opts = ["Calculate Capacity (Mr)", "Design Steel (As)", "Find Concrete (fck)", "Find Depth (d)"]
        elif section_type == "Doubly Reinforced":
            goal_opts = ["Calculate Capacity (Mr)", "Design Tension Steel (As)"]
        else:
            goal_opts = ["Calculate Capacity (Mr)"]
            
        goal = st.selectbox("Calculation Goal", goal_opts)

    # STEP 2: RENDER INPUTS (Based on Step 1)
    inputs = render_inputs(section_type, goal)

    # STEP 3: ACTION & OUTPUT
    if st.button("Run Analysis", type="primary"):
        st.write("---")
        st.header("Results")
        
        # Placeholder for where we will connect the logic engines next
        st.info(f"Running Logic for: **{section_type}** -> **{goal}**")
        st.write("Inputs collected:", inputs)
        
        # Here we will call:
        # 1. Math Function (returns c, Mr, etc.)
        # 2. Report Generator (Text)
        # 3. Diagram Generator (Plot)

if __name__ == "__main__":
    app()
