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
        
        class SoilState:
            def __init__(self):
                self.params = {
                    'w': None, 'Gs': None, 'e': None, 'n': None, 'Sr': None,
                    'rho_bulk': None, 'rho_dry': None, 
                    'gamma_bulk': None, 'gamma_dry': None, 'gamma_sat': None,
                    'gamma_sub': None, 'na': None  # Added Air Content & Submerged
                }
                self.rho_w = 1.0
                self.gamma_w = 9.81
                self.log = [] 

                self.latex_map = {
                    'w': 'w', 'Gs': 'G_s', 'e': 'e', 'n': 'n', 'Sr': 'S_r',
                    'rho_bulk': r'\rho_{bulk}', 'rho_dry': r'\rho_{dry}',
                    'gamma_bulk': r'\gamma_{bulk}', 'gamma_dry': r'\gamma_{dry}', 
                    'gamma_sat': r'\gamma_{sat}',
                    'gamma_sub': r'\gamma^\prime (Submerged)', # New
                    'na': r'n_a (Air Content)' # New
                }

            def set_param(self, key, value):
                if value is not None: self.params[key] = float(value)

            def add_log(self, target_key, formula_latex, sub_latex, result):
                symbol = self.latex_map.get(target_key, target_key)
                self.log.append({
                    "Variable": symbol, "Formula": formula_latex, "Substitution": sub_latex, "Result": result
                })

            def solve(self):
                changed = True
                iterations = 0
                p = self.params
                def known(k): return p[k] is not None

                while changed and iterations < 15:
                    changed = False
                    
                    # --- CORE RELATIONSHIPS ---
                    # Gamma <-> Rho
                    if known('gamma_bulk') and not known('rho_bulk'):
                        p['rho_bulk'] = p['gamma_bulk'] / self.gamma_w
                        self.add_log('rho_bulk', r'\frac{\gamma_{bulk}}{\gamma_w}', r'\frac{' + f"{p['gamma_bulk']}" + r'}{9.81}', p['rho_bulk'])
                        changed = True

                    # n <-> e
                    if known('n') and not known('e'):
                        p['e'] = p['n'] / (1 - p['n'])
                        self.add_log('e', r'\frac{n}{1 - n}', r'\frac{' + f"{p['n']:.3f}" + r'}{1 - ' + f"{p['n']:.3f}" + r'}', p['e'])
                        changed = True
                    if known('e') and not known('n'):
                        p['n'] = p['e'] / (1 + p['e'])
                        self.add_log('n', r'\frac{e}{1 + e}', r'\frac{' + f"{p['e']:.3f}" + r'}{1 + ' + f"{p['e']:.3f}" + r'}', p['n'])
                        changed = True

                    # Se = wGs
                    if known('w') and known('Gs') and known('e') and not known('Sr'):
                        p['Sr'] = (p['w'] * p['Gs']) / p['e']
                        self.add_log('Sr', r'\frac{w \cdot G_s}{e}', r'\frac{' + f"{p['w']:.3f} \cdot {p['Gs']:.2f}" + r'}{' + f"{p['e']:.3f}" + r'}', p['Sr'])
                        changed = True
                    if known('w') and known('Gs') and known('Sr') and not known('e') and p['Sr'] != 0:
                        p['e'] = (p['w'] * p['Gs']) / p['Sr']
                        self.add_log('e', r'\frac{w \cdot G_s}{S_r}', r'\frac{' + f"{p['w']:.3f} \cdot {p['Gs']:.2f}" + r'}{' + f"{p['Sr']:.3f}" + r'}', p['e'])
                        changed = True
                    if known('Sr') and known('e') and known('Gs') and not known('w'):
                        p['w'] = (p['Sr'] * p['e']) / p['Gs']
                        self.add_log('w', r'\frac{S_r \cdot e}{G_s}', r'\frac{' + f"{p['Sr']:.3f} \cdot {p['e']:.3f}" + r'}{' + f"{p['Gs']:.2f}" + r'}', p['w'])
                        changed = True
                    
                    # Gamma Dry from Gs
                    if known('Gs') and known('e') and not known('gamma_dry'):
                        p['gamma_dry'] = (p['Gs'] * self.gamma_w) / (1 + p['e'])
                        self.add_log('gamma_dry', r'\frac{G_s \gamma_w}{1 + e}', r'\frac{' + f"{p['Gs']:.2f} \cdot 9.81" + r'}{1 + ' + f"{p['e']:.3f}" + r'}', p['gamma_dry'])
                        changed = True

                    # Gamma Bulk from Gs
                    if known('Gs') and known('e') and known('Sr') and not known('gamma_bulk'):
                        p['gamma_bulk'] = ((p['Gs'] + (p['Sr']*p['e'])) * self.gamma_w) / (1 + p['e'])
                        self.add_log('gamma_bulk', r'\frac{(G_s + S_r e)\gamma_w}{1+e}', r'Calc...', p['gamma_bulk'])
                        changed = True

                    # --- NEW: MISSING CONCEPTS FROM NOTES ---
                    
                    # 1. Submerged Unit Weight (Gamma Prime)
                    # If we know Gamma Bulk and it is Saturated (Sr=1), then Gamma Bulk IS Gamma Sat
                    if known('gamma_bulk') and p['Sr'] == 1.0 and not known('gamma_sub'):
                        p['gamma_sub'] = p['gamma_bulk'] - self.gamma_w
                        self.add_log('gamma_sub', r'\gamma_{sat} - \gamma_w', f"{p['gamma_bulk']:.2f} - 9.81", p['gamma_sub'])
                        changed = True
                    
                    # 2. Air Content (na)
                    if known('n') and known('Sr') and not known('na'):
                        p['na'] = p['n'] * (1 - p['Sr'])
                        self.add_log('na', r'n(1 - S_r)', f"{p['n']:.3f}(1 - {p['Sr']:.3f})", p['na'])
                        changed = True

                    iterations += 1

        # --- UI INPUTS ---
        col_state, col_blank = st.columns([1, 2])
        with col_state:
            condition = st.radio("Soil State:", ["Partially Saturated (Input Sr)", "Fully Saturated (Sr=1)", "Dry (Sr=0)"])
        
        solver = SoilState()
        if "Fully" in condition: solver.set_param('Sr', 1.0)
        elif "Dry" in condition: solver.set_param('Sr', 0.0)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Basic Properties**")
            w_in = st.number_input("Water Content (w)", 0.0, step=0.01, format="%.3f")
            Gs_in = st.number_input("Specific Gravity (Gs)", 0.0, step=0.01, format="%.2f")
            e_in = st.number_input("Void Ratio (e)", 0.0, step=0.01)
            n_in = st.number_input("Porosity (n)", 0.0, step=0.01)
            Sr_in = st.number_input("Degree of Saturation (Sr)", 0.0, 1.0, step=0.01)

        with col2:
            st.markdown("**Unit Weights**")
            gamma_bulk_in = st.number_input("Bulk Unit Wt (kN/m³)", 0.0, step=0.1)
            gamma_dry_in = st.number_input("Dry Unit Wt (kN/m³)", 0.0, step=0.1)

        # Load inputs
        if w_in > 0: solver.set_param('w', w_in)
        if Gs_in > 0: solver.set_param('Gs', Gs_in)
        if e_in > 0: solver.set_param('e', e_in)
        if n_in > 0: solver.set_param('n', n_in)
        if "Partially" in condition and Sr_in > 0: solver.set_param('Sr', Sr_in)
        if gamma_bulk_in > 0: solver.set_param('gamma_bulk', gamma_bulk_in)
        if gamma_dry_in > 0: solver.set_param('gamma_dry', gamma_dry_in)
        
        if st.button("🚀 Solve Numeric Problem", type="primary"):
            solver.solve()
            st.success("Calculation Complete!")
            
            # 1. Standard Results
            if solver.log:
                with st.expander("📝 View Step-by-Step Solution", expanded=True):
                    for step in solver.log:
                        st.markdown(f"**Found ${step['Variable']}$:**")
                        st.latex(f"{step['Variable']} = {step['Formula']} = {step['Substitution']} = \\mathbf{{{step['Result']:.4f}}}")
            else:
                st.error("Not enough info to solve.")

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
                # NEW: Air Content
                if get_val('na') is not None: st.latex(f"n_a = {get_val('na'):.4f}")
            
            with res_col2:
                st.markdown("**Unit Weights**")
                if get_val('gamma_bulk') is not None: st.latex(r"\gamma_{bulk} = " + f"{get_val('gamma_bulk'):.2f}")
                if get_val('gamma_dry') is not None: st.latex(r"\gamma_{dry} = " + f"{get_val('gamma_dry'):.2f}")
                # NEW: Submerged Unit Weight
                if get_val('gamma_sub') is not None: st.latex(r"\gamma' = " + f"{get_val('gamma_sub'):.2f}")

        # --- NEW SECTION: RELATIVE DENSITY (Dr) ---
        st.markdown("---")
        st.subheader("🥪 Relative Density (Dr)")
        st.caption("Calculate density state based on e_max and e_min.")
        
        c1, c2, c3 = st.columns(3)
        with c1: e_curr = st.number_input("Current Void Ratio (e)", 0.0, step=0.01, key="dr_e")
        with c2: e_max = st.number_input("Max Void Ratio (e_max)", 0.0, step=0.01, key="dr_emax")
        with c3: e_min = st.number_input("Min Void Ratio (e_min)", 0.0, step=0.01, key="dr_emin")
        
        if st.button("Calculate Relative Density"):
            if e_max > e_min and e_max > 0:
                Dr = (e_max - e_curr) / (e_max - e_min)
                st.latex(r"D_r = \frac{e_{max} - e}{e_{max} - e_{min}} = " + f"{Dr*100:.1f}\\%")
                
                if Dr < 0.15: st.info("State: Very Loose")
                elif Dr < 0.35: st.info("State: Loose")
                elif Dr < 0.65: st.info("State: Medium Dense")
                elif Dr < 0.85: st.info("State: Dense")
                else: st.info("State: Very Dense")
            else:
                st.error("Check your inputs. e_max must be greater than e_min.")

    # ==========================
