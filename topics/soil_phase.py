import streamlit as st
import pandas as pd

def app():
    st.markdown("---")
    
    # 1. SELECT MODE
    mode = st.radio("Select Solver Mode:", ["🔢 Numeric Calculation", "abc Symbolic / Formula Finder"], horizontal=True)

    # ==========================
    # MODE A: NUMERIC
    # ==========================
    if "Numeric" in mode:
        st.caption("Enter what you know. I will calculate the rest.")
        
        # --- LOGIC ENGINE ---
        class SoilState:
            def __init__(self):
                self.params = {
                    'w': None, 'Gs': None, 'e': None, 'n': None, 'S': None,
                    'rho_bulk': None, 'rho_dry': None, 
                    'gamma_bulk': None, 'gamma_dry': None, 'gamma_sat': None
                }
                self.rho_w = 1.0
                self.gamma_w = 9.81
                self.log = [] 

                # Dictionary to make variables look like Math Symbols
                self.latex_map = {
                    'w': 'w (Water Content)', 
                    'Gs': 'G_s (Specific Gravity)', 
                    'e': 'e (Void Ratio)', 
                    'n': 'n (Porosity)', 
                    'S': 'S (Saturation)',
                    'rho_bulk': r'\rho_{bulk} (Bulk Density)', 
                    'rho_dry': r'\rho_{dry} (Dry Density)',
                    'gamma_bulk': r'\gamma_{bulk} (Bulk Unit Wt)', 
                    'gamma_dry': r'\gamma_{dry} (Dry Unit Wt)', 
                    'gamma_sat': r'\gamma_{sat} (Sat Unit Wt)'
                }

            def set_param(self, key, value):
                if value is not None and value != 0: 
                    self.params[key] = float(value)

            def add_log(self, target_key, formula_latex, sub_latex, result):
                # Convert the target variable key to symbol
                # We split the map to get just the symbol part for the log
                full_label = self.latex_map.get(target_key, target_key)
                symbol = full_label.split(' ')[0] 
                
                self.log.append({
                    "Variable": symbol,
                    "Formula": formula_latex,
                    "Substitution": sub_latex,
                    "Result": result
                })

            def solve(self):
                changed = True
                iterations = 0
                p = self.params
                
                while changed and iterations < 10:
                    changed = False
                    
                    # 1. Gamma -> Rho
                    if p['gamma_bulk'] and not p['rho_bulk']:
                        p['rho_bulk'] = p['gamma_bulk'] / self.gamma_w
                        self.add_log('rho_bulk', r'\frac{\gamma_{bulk}}{\gamma_w}', r'\frac{' + f"{p['gamma_bulk']}" + r'}{9.81}', p['rho_bulk'])
                        changed = True
                    if p['gamma_dry'] and not p['rho_dry']:
                        p['rho_dry'] = p['gamma_dry'] / self.gamma_w
                        self.add_log('rho_dry', r'\frac{\gamma_{dry}}{\gamma_w}', r'\frac{' + f"{p['gamma_dry']}" + r'}{9.81}', p['rho_dry'])
                        changed = True

                    # 2. n <-> e
                    if p['n'] and not p['e']:
                        p['e'] = p['n'] / (1 - p['n'])
                        self.add_log('e', r'\frac{n}{1 - n}', r'\frac{' + f"{p['n']:.3f}" + r'}{1 - ' + f"{p['n']:.3f}" + r'}', p['e'])
                        changed = True
                    if p['e'] and not p['n']:
                        p['n'] = p['e'] / (1 + p['e'])
                        self.add_log('n', r'\frac{e}{1 + e}', r'\frac{' + f"{p['e']:.3f}" + r'}{1 + ' + f"{p['e']:.3f}" + r'}', p['n'])
                        changed = True

                    # 3. Se = wGs
                    if p['w'] and p['Gs'] and p['e'] and p['S'] is None:
                        p['S'] = (p['w'] * p['Gs']) / p['e']
                        self.add_log('S', r'\frac{w \cdot G_s}{e}', r'\frac{' + f"{p['w']:.3f} \cdot {p['Gs']:.2f}" + r'}{' + f"{p['e']:.3f}" + r'}', p['S'])
                        changed = True
                    if p['w'] and p['Gs'] and p['S'] and p['e'] is None and p['S'] != 0:
                        p['e'] = (p['w'] * p['Gs']) / p['S']
                        self.add_log('e', r'\frac{w \cdot G_s}{S}', r'\frac{' + f"{p['w']:.3f} \cdot {p['Gs']:.2f}" + r'}{' + f"{p['S']:.3f}" + r'}', p['e'])
                        changed = True
                    if p['S'] and p['e'] and p['Gs'] and p['w'] is None:
                        p['w'] = (p['S'] * p['e']) / p['Gs']
                        self.add_log('w', r'\frac{S \cdot e}{G_s}', r'\frac{' + f"{p['S']:.3f} \cdot {p['e']:.3f}" + r'}{' + f"{p['Gs']:.2f}" + r'}', p['w'])
                        changed = True
                    
                    # 4. Rho relationships
                    if p['rho_bulk'] and p['w'] and not p['rho_dry']:
                        p['rho_dry'] = p['rho_bulk'] / (1 + p['w'])
                        self.add_log('rho_dry', r'\frac{\rho_{bulk}}{1 + w}', r'\frac{' + f"{p['rho_bulk']:.3f}" + r'}{1 + ' + f"{p['w']:.3f}" + r'}', p['rho_dry'])
                        changed = True 
                    if p['rho_dry'] and p['w'] and not p['rho_bulk']:
                        p['rho_bulk'] = p['rho_dry'] * (1 + p['w'])
                        self.add_log('rho_bulk', r'\rho_{dry}(1 + w)', f"{p['rho_dry']:.3f}(1 + {p['w']:.3f})", p['rho_bulk'])
                        changed = True
                    
                    # 5. Fundamental Rho Dry
                    if p['Gs'] and p['e'] and not p['rho_dry']:
                        p['rho_dry'] = (p['Gs'] * self.rho_w) / (1 + p['e'])
                        self.add_log('rho_dry', r'\frac{G_s \rho_w}{1 + e}', r'\frac{' + f"{p['Gs']:.2f} \cdot 1" + r'}{1 + ' + f"{p['e']:.3f}" + r'}', p['rho_dry'])
                        changed = True
                        
                    iterations += 1

        # --- UI INPUTS ---
        col_state, col_blank = st.columns([1, 2])
        with col_state:
            condition = st.radio("Soil State:", ["Partially Saturated", "Fully Saturated (S=1)", "Dry (S=0)"])
        
        solver = SoilState()
        if condition == "Fully Saturated (S=1)": solver.set_param('S', 1.0)
        if condition == "Dry (S=0)": solver.set_param('S', 0.0)

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
        
        if st.button("🚀 Solve Numeric Problem", type="primary"):
            solver.solve()
            st.success("Calculation Complete!")
            
            if solver.log:
                with st.expander("📝 View Step-by-Step Solution", expanded=True):
                    for step in solver.log:
                        # Professional LaTeX Formatting
                        st.markdown(f"**Found ${step['Variable']}$:**")
                        st.latex(f"{step['Variable']} = {step['Formula']} = {step['Substitution']} = \\mathbf{{{step['Result']:.3f}}}")
            else:
                st.error("Not enough info to solve.")
                
            st.caption("Final Results Summary")
            
            # --- THE FIX: RENAME VARIABLES FOR THE TABLE ---
            clean_results = {}
            for k, v in solver.params.items():
                if v is not None:
                    # Get the fancy name (e.g., "ρ_bulk (Bulk Density)")
                    # We strip the LaTeX code slightly to make it readable in a simple table if needed,
                    # but Streamlit dataframes render LaTeX if you use st.data_editor or similar.
                    # For a simple view, let's just use the Key + Description.
                    label = solver.latex_map.get(k, k)
                    # Remove the $ signs if they were there (our map has raw latex r'\rho')
                    # We can format the value nicely too
                    clean_results[label] = f"{v:.4f}"

            # Create DataFrame with Index as "Property" and Value as "Result"
            df = pd.DataFrame.from_dict(clean_results, orient='index', columns=['Value'])
            st.dataframe(df, use_container_width=True)

    # ==========================
    # MODE B: SYMBOLIC
    # ==========================
    else:
        st.caption("Select variables to find the correct formula without numbers.")
        col1, col2 = st.columns(2)
        with col1:
            target = st.selectbox("Find Variable:", ["Void Ratio (e)", "Porosity (n)", "Dry Unit Wt (γ_dry)", "Degree of Saturation (S)", "Bulk Unit Wt (γ_bulk)"])
        with col2:
            knowns = st.multiselect("Given / Known Variables:", ["w", "Gs", "e", "n", "S", "γ_bulk", "γ_dry"])

        if st.button("🔎 Find Formula"):
            k = [x.split(" ")[0] for x in knowns] 
            found = False
            
            if "Void" in target:
                if "n" in k:
                    st.latex(r"e = \frac{n}{1 - n}")
                    found = True
                elif "w" in k and "Gs" in k and "S" in k:
                    st.latex(r"e = \frac{w G_s}{S}")
                    found = True
            elif "Porosity" in target:
                if "e" in k:
                    st.latex(r"n = \frac{e}{1 + e}")
                    found = True
            
            if not found:
                st.warning("No direct formula found. Try adding more known variables.")
