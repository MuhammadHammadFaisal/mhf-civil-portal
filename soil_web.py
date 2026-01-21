import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# 🏠 PAGE 1: THE MHF HOME PAGE (Rebranded)
# ==========================================
def home_page():
    # Header Section
    st.title(" MHF Civil Portal")
    st.caption("Advanced Civil Engineering Question Solver | Developed by Muhammad Hammad Faisal")
    st.markdown("---")

    # Welcome Message
    st.markdown("""
    ### **Precision. Logic. Deterministic.**
    Welcome to the official digital workspace of **MHF Civil**. This platform solves complex Civil Engineering questions and give you correct answer every time.
    
    #### **Available Modules**
    """)

    # Course Cards (Using Columns for a professional look)
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**Soil Mechanics**\n\nActive module for phase relationships.")
    
    with col2:
        st.warning("**🏗️ Structural Analysis**\n\n*Coming Soon*\n\nModules for beam deflection and moment distribution.")

    st.markdown("---")
    
    # --- ABOUT THE DEVELOPER ---
    st.subheader("👨‍💻 About MHF Civil")
    
    dev_col1, dev_col2 = st.columns([1, 3])
    
    with dev_col1:
        # Placeholder professional icon (You can change this link later)
    st.image("https://github.com/MuhammadHammadFaisal/mhf-civil-portal/blob/main/profile.png?raw=true", width=100)
    
    with dev_col2:
        st.markdown("""
        **Muhammad Hammad Faisal** *Final Year Civil Engineering Student (METU) | Founder, MHF Civil*
        
        This portal was developed to assist students and junior engineers in verifying complex calculations.
        """)
        # Link to your LinkedIn or Email (Change the URL to your actual profile)
        st.link_button("🤝 Connect on LinkedIn", "https://www.linkedin.com/in/muhammad-hammad-20059a229/")
        # --- PROFESSIONAL FOOTER ---
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 12px;'>
        © 2026 MHF Civil Engineering Group. All rights reserved.<br>
        Version 1.0.2 | Ankara, Turkey
        </div>
        """, 
        unsafe_allow_html=True
    )
# ==========================================
# 🧠 LOGIC ENGINE (The Brain)
# ==========================================
class SoilState:
    def __init__(self):
        self.params = {
            'w': None, 'Gs': None, 'e': None, 'n': None, 'S': None,
            'rho_bulk': None, 'rho_dry': None, 
            'gamma_bulk': None, 'gamma_dry': None, 'gamma_sat': None,
            'm_total': None, 'm_solids': None, 'm_water': None,
            'V_total': None, 'V_solids': None, 'V_voids': None
        }
        self.rho_w = 1.0
        self.gamma_w = 9.81
        self.log = [] 

    def set_param(self, key, value):
        if value is not None and value != 0: 
            self.params[key] = float(value)

    def add_log(self, target, formula, sub, result):
        self.log.append({
            "Variable": target,
            "Formula": formula,
            "Substitution": sub,
            "Result": result
        })

    def solve(self):
        changed = True
        iterations = 0
        p = self.params
        
        while changed and iterations < 10:
            changed = False
            
            # Gamma -> Rho
            if p['gamma_bulk'] and not p['rho_bulk']:
                p['rho_bulk'] = p['gamma_bulk'] / self.gamma_w
                self.add_log('rho_bulk', 'gamma_bulk / 9.81', f"{p['gamma_bulk']} / 9.81", p['rho_bulk'])
                changed = True
            if p['gamma_dry'] and not p['rho_dry']:
                p['rho_dry'] = p['gamma_dry'] / self.gamma_w
                self.add_log('rho_dry', 'gamma_dry / 9.81', f"{p['gamma_dry']} / 9.81", p['rho_dry'])
                changed = True

            # n <-> e
            if p['n'] and not p['e']:
                p['e'] = p['n'] / (1 - p['n'])
                self.add_log('e', 'n / (1 - n)', f"{p['n']} / (1 - {p['n']})", p['e'])
                changed = True
            if p['e'] and not p['n']:
                p['n'] = p['e'] / (1 + p['e'])
                self.add_log('n', 'e / (1 + e)', f"{p['e']} / (1 + {p['e']})", p['n'])
                changed = True

            # Se = wGs
            if p['w'] and p['Gs'] and p['e'] and p['S'] is None:
                p['S'] = (p['w'] * p['Gs']) / p['e']
                self.add_log('S', 'w * Gs / e', f"({p['w']} * {p['Gs']}) / {p['e']}", p['S'])
                changed = True
            if p['w'] and p['Gs'] and p['S'] and p['e'] is None and p['S'] != 0:
                p['e'] = (p['w'] * p['Gs']) / p['S']
                self.add_log('e', 'w * Gs / S', f"({p['w']} * {p['Gs']}) / {p['S']}", p['e'])
                changed = True
            if p['S'] and p['e'] and p['Gs'] and p['w'] is None:
                p['w'] = (p['S'] * p['e']) / p['Gs']
                self.add_log('w', 'S * e / Gs', f"({p['S']} * {p['e']}) / {p['Gs']}", p['w'])
                changed = True
            
            # Rho relationships
            if p['rho_bulk'] and p['w'] and not p['rho_dry']:
                p['rho_dry'] = p['rho_bulk'] / (1 + p['w'])
                self.add_log('rho_dry', 'rho_bulk / (1+w)', f"{p['rho_bulk']} / (1+{p['w']})", p['rho_dry'])
                changed = True
            if p['rho_dry'] and p['w'] and not p['rho_bulk']:
                p['rho_bulk'] = p['rho_dry'] * (1 + p['w'])
                self.add_log('rho_bulk', 'rho_dry * (1+w)', f"{p['rho_dry']} * (1+{p['w']})", p['rho_bulk'])
                changed = True
            
            # Fundamental Rho Dry
            if p['Gs'] and p['e'] and not p['rho_dry']:
                p['rho_dry'] = (p['Gs'] * self.rho_w) / (1 + p['e'])
                self.add_log('rho_dry', 'Gs * rho_w / (1+e)', f"{p['Gs']} * 1 / (1+{p['e']:.3f})", p['rho_dry'])
                changed = True
            if p['Gs'] and p['rho_dry'] and not p['e']:
                p['e'] = ((p['Gs'] * self.rho_w) / p['rho_dry']) - 1
                self.add_log('e', '(Gs * rho_w / rho_dry) - 1', f"({p['Gs']} * 1 / {p['rho_dry']:.3f}) - 1", p['e'])
                changed = True

            # Fundamental Rho Bulk -> e (Direct)
            if p['rho_bulk'] and p['Gs'] and p['w'] and not p['e']:
                p['e'] = (p['Gs'] * (1 + p['w']) * self.rho_w / p['rho_bulk']) - 1
                self.add_log('e', '(Gs(1+w)/rho_bulk) - 1', f"({p['Gs']}*(1+{p['w']})/{p['rho_bulk']:.3f}) - 1", p['e'])
                changed = True
                
            iterations += 1

# ==========================================
# 📐 PAGE 2: SOIL MECHANICS COURSE
# ==========================================
def soil_mechanics_page():
    st.header("🪨 CE 363: Soil Mechanics")
    
    # --- SUB-TOPIC SELECTOR ---
    topic = st.selectbox("Select Topic:", ["1. Phase Relationships", "2. Stress Calculation", "3. Soil Classification"])
    
    if topic == "1. Phase Relationships":
        render_phase_solver()
    elif topic == "2. Stress Calculation":
        st.warning("🚧 Stress Calculation Module is under construction!")
    elif topic == "3. Soil Classification":
        st.warning("🚧 Classification Module is under construction!")

# ==========================================
# 🧮 THE SOLVER UI (Embedded inside Page 2)
# ==========================================
def render_phase_solver():
    st.markdown("---")
    st.subheader("Phase Relationship Solver")
    st.caption("Enter what you know. I will calculate the rest.")

    # 1. SETTINGS
    col_state, col_blank = st.columns([1, 2])
    with col_state:
        condition = st.radio("Soil State:", ["Partially Saturated", "Fully Saturated (S=1)", "Dry (S=0)"])
    
    solver = SoilState()
    if condition == "Fully Saturated (S=1)": solver.set_param('S', 1.0)
    if condition == "Dry (S=0)": solver.set_param('S', 0.0)

    # 2. INPUTS
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Basic Properties**")
        w = st.number_input("Water Content (w) [decimal]", 0.0, step=0.01, format="%.3f")
        Gs = st.number_input("Specific Gravity (Gs)", 0.0, step=0.01, format="%.2f")
        e = st.number_input("Void Ratio (e)", 0.0, step=0.01)
        n = st.number_input("Porosity (n)", 0.0, step=0.01)

    with col2:
        st.markdown("**Unit Weights**")
        gamma_bulk = st.number_input("Bulk Unit Wt (kN/m³)", 0.0, step=0.1)
        gamma_dry = st.number_input("Dry Unit Wt (kN/m³)", 0.0, step=0.1)
        rho_bulk = st.number_input("Bulk Density (g/cm³)", 0.0, step=0.01)
        rho_dry = st.number_input("Dry Density (g/cm³)", 0.0, step=0.01)

    # Load inputs
    if w > 0: solver.set_param('w', w)
    if Gs > 0: solver.set_param('Gs', Gs)
    if e > 0: solver.set_param('e', e)
    if n > 0: solver.set_param('n', n)
    if gamma_bulk > 0: solver.set_param('gamma_bulk', gamma_bulk)
    if gamma_dry > 0: solver.set_param('gamma_dry', gamma_dry)
    if rho_bulk > 0: solver.set_param('rho_bulk', rho_bulk)
    if rho_dry > 0: solver.set_param('rho_dry', rho_dry)
    
    # 3. SOLVE BUTTON
    if st.button("🚀 Solve Problem", type="primary"):
        solver.solve()
        
        st.success("Calculation Complete!")
        
        # LOGIC STEPS
        if solver.log:
            with st.expander("📝 View Step-by-Step Solution", expanded=True):
                for step in solver.log:
                    st.markdown(f"**Found `{step['Variable']}`:**")
                    st.latex(f"{step['Variable']} = {step['Formula']} = {step['Substitution']} = \\mathbf{{{step['Result']:.3f}}}")
        else:
            st.error("Not enough info to solve.")

        # FINAL TABLE
        st.caption("Final Results Summary")
        results = {k: v for k, v in solver.params.items() if v is not None}
        st.dataframe(pd.DataFrame.from_dict(results, orient='index', columns=['Value']))

# ==========================================
# 🧭 MAIN APP NAVIGATION
# ==========================================
def main():
    st.set_page_config(page_title="MHF Civil", page_icon="🏗️", layout="wide")
    
    # SIDEBAR MENU
    st.sidebar.title("🏗️ MHF Civil")
    page = st.sidebar.radio("Navigate to:", ["🏠 Home", "🪨 Soil Mechanics", "🏗️ Structures"])
    
    # PAGE ROUTING
    if page == "🏠 Home":
        home_page()
    elif page == "🪨 Soil Mechanics":
        soil_mechanics_page()
    elif page == "🏗️ Structures":
        st.title("🏗️ Structural Analysis")
        st.info("This course is not active yet.")

if __name__ == "__main__":
    main()





