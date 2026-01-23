import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def app():
    st.markdown("---")
    st.subheader("💧 Flow of Water & Seepage Analysis")

    # TABS FOR DIFFERENT PROBLEM TYPES
    tab1, tab2, tab3 = st.tabs(["1️⃣ 1D Seepage (Effective Stress)", "2️⃣ Permeability Tests", "3️⃣ Flow Nets & Piping"])

    # =================================================================
    # TAB 1: 1D SEEPAGE (The "Diagram" Problem)
    # =================================================================
    with tab1:
        st.caption("Determine Effective Stress under Upward or Downward Flow conditions.")
        
        col_setup, col_plot = st.columns([1, 1])
        
        with col_setup:
            st.markdown("### 1. Define Problem from Diagram")
            
            # Flow Direction
            flow_dir = st.radio("Flow Direction:", ["Downward Flow ⬇️", "Upward Flow ⬆️"], horizontal=True)
            
            # Geometric Inputs
            H_water = st.number_input("Height of Water above Soil (H1) [m]", 0.0, step=0.5, value=1.0)
            H_soil = st.number_input("Height of Soil Specimen (H2) [m]", 0.1, step=0.5, value=2.0)
            
            # Head Loss Input
            h_diff = st.number_input("Head Difference / Head Loss (h) [m]", 0.0, step=0.1, value=1.0, 
                                   help="Difference in water level between top and bottom piezometers.")
            
            # Soil Property
            gamma_sat = st.number_input("Saturated Unit Weight (γ_sat) [kN/m³]", 18.0, step=0.1)
            gamma_w = 9.81
            
            # Point of Interest
