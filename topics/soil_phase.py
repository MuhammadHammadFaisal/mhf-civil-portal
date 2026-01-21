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
                        p['Sr'] = (p['w'] * p['Gs']) / p['e
