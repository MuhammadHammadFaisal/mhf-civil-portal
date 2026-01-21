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
                # Initialize all parameters to None
                self.params = {
                    'w': None, 'Gs': None, 'e': None, 'n': None, 'Sr': None,
                    'rho_bulk': None, 'rho_dry': None, 
                    'gamma_bulk': None, 'gamma_dry': None, 'gamma_sat': None
                }
                self.rho_w = 1.0  # g/cm3
                self.gamma_w = 9.81 # kN/m3
                self.log = [] 

                # Math Symbols for display
                self.latex_map = {
                    'w': 'w', 
                    'Gs': 'G_s', 
                    'e': 'e', 
                    'n': 'n', 
                    'Sr': 'S_r',  # Changed to Sr per request
                    'rho_bulk': r'\rho_{bulk}', 
                    'rho_dry': r'\rho_{dry}',
                    'gamma_bulk': r'\gamma_{bulk}', 
                    'gamma_dry': r'\gamma_{dry}', 
                    'gamma_sat': r'\gamma_{sat}'
                }

            def set_param(self, key, value):
                # FIX: Allow 0.0 values (important for S=0 or w=0)
                if value is not None: 
                    self.params[key] = float(value)

            def add_log(self, target_key, formula_latex, sub_latex, result):
                symbol = self.latex_map.get(target_key, target_key)
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
                
                # Helper to check if value exists (is not None)
                def known(k): return p[k] is not None

                while changed and iterations < 15:
                    changed = False
                    
                    # 1. Gamma <-> Rho Conversions
                    if known('gamma_bulk') and not known('rho_bulk'):
                        p['rho_bulk'] = p['gamma_bulk'] / self.gamma_w
                        self.add_log('rho_bulk', r'\frac{\gamma_{bulk}}{\gamma_w}', r'\frac{' + f"{p['gamma_bulk']}" + r'}{9.81}', p['rho_bulk'])
                        changed = True
                    if known('gamma_dry') and not known('rho_dry'):
                        p['rho_dry'] = p['gamma_dry'] / self.gamma_w
                        self.add_log('rho_dry', r'\frac{\gamma_{dry}}{\gamma_w}', r'\frac{' + f"{p['gamma_dry']}" + r'}{9.81}', p['rho_dry'])
                        changed = True

                    # 2. n <-> e Relationships
                    if known('n') and not known('e'):
                        p['e'] = p['n'] / (1 - p['n'])
                        self.add_log('e', r'\frac{n}{1 - n}', r'\frac{' + f"{p['n']:.3f}" + r'}{1 - ' + f"{p['n']:.3f}" + r'}', p['e'])
                        changed = True
                    if known('e') and not known('n'):
                        p['n'] = p['e'] / (1 + p['e'])
                        self.add_log('n', r'\frac{e}{1 + e}', r'\frac{' + f"{p['e']:.3f}" + r'}{1 + ' + f"{p['e']:.3f}" + r'}', p['n'])
                        changed = True

                    # 3. Fundamental Equation: Se = wGs
                    # Solve for Sr
                    if known('w') and known('Gs') and known('e') and not known('Sr'):
                        p['Sr'] = (p['w'] * p['Gs']) / p['e']
                        self.add_log('Sr', r'\frac{w \cdot G_s}{e}', r'\frac{' + f"{p['w']:.3f} \cdot {p['Gs']:.2f}" + r'}{' + f"{p['e']:.3f}" + r'}', p['Sr'])
                        changed = True
                    # Solve for e
                    if known('w') and known('Gs') and known('Sr') and not known('e') and p['Sr'] != 0:
                        p['e'] = (p['w'] * p['Gs']) / p['Sr']
                        self.add_log('e', r'\frac{w \cdot G_s}{S_r}', r'\frac{' + f"{p['w']:.3f} \cdot {p['Gs']:.2f}" + r'}{' + f"{p['Sr']:.3f}" + r'}', p['e'])
                        changed = True
                    # Solve for w
                    if known('Sr') and known('e') and known('Gs') and not known('w'):
                        p['w'] = (p['Sr'] * p['e']) / p['Gs']
                        self.add_log('w', r'\frac{S_r \cdot e}{G_s}', r'\frac{' + f"{p['Sr']:.3f} \cdot {p['e']:.3f}" + r'}{' + f"{p['Gs']:.2f}" + r'}', p['w'])
                        changed = True
                    
                    # 4. Density Relationships (Rho)
                    # rho_dry = rho_bulk / (1+w)
                    if known('rho_bulk') and known('w') and not known('rho_dry'):
                        p['rho_dry'] = p['rho_bulk'] / (1 + p['w'])
                        self.add_log('rho_dry', r'\frac{\rho_{bulk}}{1 + w}', r'\frac{' + f"{p['rho_bulk']:.3f}" + r'}{1 + ' + f"{p['w']:.3f}" + r'}', p['rho_dry'])
                        changed = True 
                    # rho_bulk = rho_dry * (1+w)
                    if known('rho_dry') and known('w') and not known('rho_bulk'):
                        p['rho_bulk'] = p['rho_dry'] * (1 + p['w'])
                        self.add_log('rho_bulk', r'\rho_{dry}(1 + w)', f"{p['rho_dry']:.3f}(1 + {p['w']:.3f})", p['rho_bulk'])
                        changed = True
                    
                    # 5. Fundamental Density Equation: rho_dry = (Gs * rho_w) / (1+e)
                    # Solve for rho_dry
                    if known('Gs') and known('e') and not known('rho_dry'):
                        p['rho_dry'] = (p['Gs'] * self.rho_w) / (1 + p['e'])
                        self.add_log('rho_dry', r'\frac{G_s \rho_w}{1 + e}', r'\frac{' + f"{p['Gs']:.2f} \cdot 1" + r'}{1 + ' + f"{p['e']:.3f}" + r'}', p['rho_dry'])
                        changed = True
                    # Solve for e (CRITICAL FIX: This was likely the missing link)
                    if known('Gs') and known('rho_dry') and not known('e'):
                        # e = (Gs * rho_w / rho_dry) - 1
                        val = ((p['Gs'] * self.rho_w) / p['rho_dry']) - 1
                        if val > 0:
                            p['e'] = val
                            self.add_log('e', r'\frac{G_s \rho_w}{\rho_{dry}} - 1', r'\frac{' + f"{p['Gs']:.2f} \cdot 1" + r'}{' + f"{p['rho_dry']:.3f}" + r'} - 1', p['e'])
                            changed = True
                        
                    iterations += 1

        # --- UI INPUTS ---
        col_state, col_blank = st.columns([1, 2])
        with col_state:
            # Added "Custom" option so they can enter Sr manually
            condition = st.radio("Soil State:", ["Partially Saturated (Input Sr)", "Fully Saturated (Sr=1)", "Dry (Sr=0)"])
        
        solver = SoilState()
        
        # Handle Radio Button Logic
        if "Fully" in condition: 
            solver.set_param('Sr', 1.0)
        elif "Dry" in condition: 
            solver.set_param('Sr', 0.0)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Basic Properties**")
            w_in = st.number_input("Water Content (w) [decimal]", 0.0, step=0.01, format="%.3f")
            Gs_in = st.number_input("Specific Gravity (Gs)", 0.0, step=0.01, format="%.2f")
            e_in = st.number_input("Void Ratio (e)", 0.0, step=0.01)
            n_in = st.number_input("Porosity (n)", 0.0, step=0.01)
            # NEW INPUT: Degree of Saturation
            Sr_in = st.number_input("Degree of Saturation (Sr) [decimal]", 0.0, 1.0, step=0.01)

        with col2:
            st.markdown("**Unit Weights**")
            gamma_bulk_in = st.number_input("Bulk Unit Wt (kN/m³)", 0.0, step=0.1)
            gamma_dry_in = st.number_input("Dry Unit Wt (kN/m³)", 0.0, step=0.1)
            rho_bulk_in = st.number_input("Bulk Density (g/cm³)", 0.0, step=0.01)
            rho_dry_in = st.number_input("Dry Density (g/cm³)", 0.0, step=0.01)

        # Load inputs (Only load if User typed something > 0, except for Sr/w which can be 0)
        if w_in > 0: solver.set_param('w', w_in)
        if Gs_in > 0: solver.set_param('Gs', Gs_in)
        if e_in > 0: solver.set_param('e', e_in)
        if n_in > 0: solver.set_param('n', n_in)
        
        # Logic to handle manual Sr input
        if "Partially" in condition and Sr_in > 0:
            solver.set_param('Sr', Sr_in)

        if gamma_bulk_in > 0: solver.set_param('gamma_bulk', gamma_bulk_in)
        if gamma_dry_in > 0: solver.set_param('gamma_dry', gamma_dry_in)
        if rho_bulk_in > 0: solver.set_param('rho_bulk', rho_bulk_in)
        if rho_dry_in > 0: solver.set_param('rho_dry', rho_dry_in)
        
        if st.button("🚀 Solve Numeric Problem", type="primary"):
            solver.solve()
            st.success("Calculation Complete!")
            
            # --- DISPLAY STEPS ---
            if solver.log:
                with st.expander("📝 View Step-by-Step Solution", expanded=True):
                    for step in solver.log:
                        st.markdown(f"**Found ${step['Variable']}$:**")
                        st.latex(f"{step['Variable']} = {step['Formula']} = {step['Substitution']} = \\mathbf{{{step['Result']:.4f}}}")
            else:
                st.error("Not enough info to solve. Try adding one more known value.")
                
            # --- FINAL RESULTS ---
            st.markdown("### ✅ Final Results")
            res_col1, res_col2 = st.columns(2)
            
            def get_val(key): return solver.params.get(key)

            with res_col1:
                st.markdown("**Physical Properties**")
                if get_val('w') is not None: st.latex(f"w = {get_val('w'):.4f}")
                if get_val('Gs') is not None: st.latex(f"G_s = {get_val('Gs'):.3f}")
                if get_val('e') is not None: st.latex(f"e = {get_val('e'):.4f}")
                if get_val('n') is not None: st.latex(f"n = {get_val('n'):.4f}")
                if get_val('Sr') is not None: st.latex(f"S_r = {get_val('Sr'):.4f}")
            
            with res_col2:
                st.markdown("**Unit Weights & Densities**")
                if get_val('rho_bulk') is not None: st.latex(r"\rho_{bulk} = " + f"{get_val('rho_bulk'):.4f}")
                if get_val('rho_dry') is not None: st.latex(r"\rho_{dry} = " + f"{get_val('rho_dry'):.4f}")
                if get_val('gamma_bulk') is not None: st.latex(r"\gamma_{bulk} = " + f"{get_val('gamma_bulk'):.2f}")
                if get_val('gamma_dry') is not None: st.latex(r"\gamma_{dry} = " + f"{get_val('gamma_dry'):.2f}")

    # ==========================
    # MODE B: SYMBOLIC
    # ==========================
    else:
        st.caption("Select variables to find the correct formula without numbers.")
        col1, col2 = st.columns(2)
        with col1:
            target = st.selectbox("Find Variable:", ["Void Ratio (e)", "Porosity (n)", "Dry Unit Wt (γ_dry)", "Degree of Saturation (Sr)", "Bulk Unit Wt (γ_bulk)"])
        with col2:
            knowns = st.multiselect("Given / Known Variables:", ["w", "Gs", "e", "n", "Sr", "γ_bulk", "γ_dry"])

        if st.button("🔎 Find Formula"):
            k = [x.split(" ")[0] for x in knowns] 
            found = False
            
            if "Void" in target:
                if "n" in k:
                    st.latex(r"e = \frac{n}{1 - n}")
                    found = True
                elif "w" in k and "Gs" in k and "Sr" in k:
                    st.latex(r"e = \frac{w G_s}{S_r}")
                    found = True
            elif "Porosity" in target:
                if "e" in k:
                    st.latex(r"n = \frac{e}{1 + e}")
                    found = True
            
            if not found:
                st.warning("No direct formula found. Try adding more known variables.")
