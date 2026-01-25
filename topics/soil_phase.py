import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def app():
    st.markdown("---")
    
    # 1. SELECT MODE
    mode = st.radio("Select Solver Mode:", ["Numeric Calculation", "Symbolic / Formula Finder"], horizontal=True)

    # ==========================================
    # MODE A: NUMERIC CALCULATION (Calculator)
    # ==========================================
    if "Numeric" in mode:
        st.caption("Enter parameters. The INPUT diagram (top) updates live. The RESULT diagram (bottom) appears after solving.")
        
        # --- CLASS DEFINITION (Numeric Logic) ---
        class SoilState:
            def __init__(self):
                self.params = {
                    'w': None, 'Gs': None, 'e': None, 'n': None, 'Sr': None,
                    'rho_bulk': None, 'rho_dry': None, 
                    'gamma_bulk': None, 'gamma_dry': None, 'gamma_sat': None,
                    'gamma_sub': None, 'na': None
                }
                self.rho_w = 1.0
                self.gamma_w = 9.81
                self.log = [] 
                self.inputs = [] # Track what user typed

                self.latex_map = {
                    'w': 'w', 'Gs': 'G_s', 'e': 'e', 'n': 'n', 'Sr': 'S_r',
                    'rho_bulk': r'\rho_{bulk}', 'rho_dry': r'\rho_{dry}',
                    'gamma_bulk': r'\gamma_{bulk}', 'gamma_dry': r'\gamma_{dry}', 
                    'gamma_sat': r'\gamma_{sat}', 'gamma_sub': r'\gamma^\prime', 'na': r'n_a'
                }

            def set_param(self, key, value):
                if value is not None and value >= 0: 
                    self.params[key] = float(value)
                    self.inputs.append(key)

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
                    
                    # 1. Basic n <-> e
                    if known('n') and not known('e'):
                        p['e'] = p['n'] / (1 - p['n'])
                        sub = r'\frac{' + f"{p['n']:.3f}" + r'}{1 - ' + f"{p['n']:.3f}" + r'}'
                        self.add_log('e', r'\frac{n}{1 - n}', sub, p['e'])
                        changed = True
                    if known('e') and not known('n'):
                        p['n'] = p['e'] / (1 + p['e'])
                        sub = r'\frac{' + f"{p['e']:.3f}" + r'}{1 + ' + f"{p['e']:.3f}" + r'}'
                        self.add_log('n', r'\frac{e}{1 + e}', sub, p['n'])
                        changed = True

                    # 2. Se = wGs
                    if known('w') and known('Gs') and known('e') and not known('Sr'):
                        p['Sr'] = (p['w'] * p['Gs']) / p['e']
                        sub = r'\frac{' + f"{p['w']:.3f} \cdot {p['Gs']:.2f}" + r'}{' + f"{p['e']:.3f}" + r'}'
                        self.add_log('Sr', r'\frac{w G_s}{e}', sub, p['Sr'])
                        changed = True
                    if known('w') and known('Gs') and known('Sr') and not known('e') and p['Sr'] != 0:
                        p['e'] = (p['w'] * p['Gs']) / p['Sr']
                        sub = r'\frac{' + f"{p['w']:.3f} \cdot {p['Gs']:.2f}" + r'}{' + f"{p['Sr']:.3f}" + r'}'
                        self.add_log('e', r'\frac{w G_s}{S_r}', sub, p['e'])
                        changed = True
                    if known('Sr') and known('e') and known('Gs') and not known('w'):
                        p['w'] = (p['Sr'] * p['e']) / p['Gs']
                        sub = r'\frac{' + f"{p['Sr']:.3f} \cdot {p['e']:.3f}" + r'}{' + f"{p['Gs']:.2f}" + r'}'
                        self.add_log('w', r'\frac{S_r e}{G_s}', sub, p['w'])
                        changed = True
                    if known('Sr') and known('e') and known('w') and not known('Gs') and p['w'] != 0:
                        p['Gs'] = (p['Sr'] * p['e']) / p['w']
                        sub = r'\frac{' + f"{p['Sr']:.3f} \cdot {p['e']:.3f}" + r'}{' + f"{p['w']:.3f}" + r'}'
                        self.add_log('Gs', r'\frac{S_r e}{w}', sub, p['Gs'])
                        changed = True

                    # 3. Unit Weights
                    if known('Gs') and known('e') and not known('gamma_dry'):
                        p['gamma_dry'] = (p['Gs'] * self.gamma_w) / (1 + p['e'])
                        sub = r'\frac{' + f"{p['Gs']:.2f} \cdot 9.81" + r'}{1 + ' + f"{p['e']:.3f}" + r'}'
                        self.add_log('gamma_dry', r'\frac{G_s \gamma_w}{1 + e}', sub, p['gamma_dry'])
                        changed = True
                    if known('Gs') and known('e') and known('w') and not known('gamma_bulk'):
                        p['gamma_bulk'] = (p['Gs'] * self.gamma_w * (1 + p['w'])) / (1 + p['e'])
                        sub = r'\frac{' + f"{p['Gs']:.2f} \cdot 9.81 (1 + {p['w']:.3f})" + r'}{1 + ' + f"{p['e']:.3f}" + r'}'
                        self.add_log('gamma_bulk', r'\frac{G_s \gamma_w (1+w)}{1+e}', sub, p['gamma_bulk'])
                        changed = True

                    # 4. Reverse Calcs
                    if known('gamma_bulk') and known('Gs') and known('w') and not known('e'):
                        val = (p['Gs'] * (1 + p['w']) * self.gamma_w) / p['gamma_bulk']
                        p['e'] = val - 1
                        sub = r'\frac{' + f"{p['Gs']:.2f}(1+{p['w']:.3f})9.81" + r'}{' + f"{p['gamma_bulk']:.2f}" + r'} - 1'
                        self.add_log('e', r'\frac{G_s(1+w)\gamma_w}{\gamma_{bulk}} - 1', sub, p['e'])
                        changed = True
                    if known('gamma_dry') and known('Gs') and not known('e'):
                        val = (p['Gs'] * self.gamma_w) / p['gamma_dry']
                        p['e'] = val - 1
                        sub = r'\frac{' + f"{p['Gs']:.2f} \cdot 9.81" + r'}{' + f"{p['gamma_dry']:.2f}" + r'} - 1'
                        self.add_log('e', r'\frac{G_s \gamma_w}{\gamma_{dry}} - 1', sub, p['e'])
                        changed = True

                    # 5. Saturation
                    if known('gamma_bulk') and p['Sr'] == 1.0 and not known('gamma_sub'):
                        p['gamma_sub'] = p['gamma_bulk'] - self.gamma_w
                        sub = f"{p['gamma_bulk']:.2f} - 9.81"
                        self.add_log('gamma_sub', r'\gamma_{sat} - \gamma_w', sub, p['gamma_sub'])
                        changed = True
                    if known('n') and known('Sr') and not known('na'):
                        p['na'] = p['n'] * (1 - p['Sr'])
                        sub = f"{p['n']:.3f}(1 - {p['Sr']:.3f})"
                        self.add_log('na', r'n(1-S_r)', sub, p['na'])
                        changed = True

                    iterations += 1

        # --- DRAWING FUNCTION ---
        def draw_phase_diagram(params, inputs_list, is_result_mode=False):
            raw_e = params.get('e')
            raw_Sr = params.get('Sr')
            raw_w = params.get('w')
            raw_Gs = params.get('Gs')

            if is_result_mode:
                e = raw_e if raw_e is not None else 0.5
                Sr = raw_Sr if raw_Sr is not None else 0.5
                Gs = raw_Gs if raw_Gs is not None else 2.7
                w = raw_w if raw_w is not None else 0.1
            else:
                e = raw_e if raw_e is not None else 0.7 
                Sr = raw_Sr if raw_Sr is not None else 0.5
                Gs = raw_Gs if raw_Gs is not None else 2.7
                w = raw_w if raw_w is not None else 0.2

            Vs = 1.0
            Vv = e
            Vw = Sr * e
            Va = Vv - Vw
            
            Ms = Gs 
            Mw = w * Ms if w is not None else Vw * 1.0 

            fig, ax = plt.subplots(figsize=(5, 3.5))
            ax.set_xlim(-1.5, 2.5) 
            ax.set_ylim(0, max(1.5, 1 + e + 0.3)) 
            ax.axis('off')

            def get_color(key):
                if key in inputs_list: return 'green' 
                if is_result_mode: return 'red'       
                return 'red'                          

            def get_label(key, val, fmt="{:.3f}"):
                if key in inputs_list: return fmt.format(val) 
                if is_result_mode and val is not None: return fmt.format(val)
                return "?" 

            # Rectangles
            ax.add_patch(patches.Rectangle((0, 0), 1, Vs, linewidth=2, edgecolor='black', facecolor='#D2B48C'))
            ax.text(0.5, Vs/2, 'S', ha='center', va='center', fontsize=10, fontweight='bold')

            if Vw > 0.001:
                ax.add_patch(patches.Rectangle((0, Vs), 1, Vw, linewidth=2, edgecolor='black', facecolor='#87CEEB'))
                if Vw > 0.15: ax.text(0.5, Vs + Vw/2, 'W', ha='center', va='center', fontsize=10, fontweight='bold')

            if Va > 0.001:
                ax.add_patch(patches.Rectangle((0, Vs + Vw), 1, Va, linewidth=2, edgecolor='black', facecolor='#F0F8FF'))
                if Va > 0.15: ax.text(0.5, Vs + Vw + Va/2, 'A', ha='center', va='center', fontsize=10, fontweight='bold')

            # Labels
            ax.text(-0.8, 1+e+0.1, r'$Vol$', ha='center', fontsize=10, fontweight='bold')
            ax.text(-0.1, Vs/2, f'$V_s=1$', ha='right', va='center', fontsize=9)
            
            if Vv > 0:
                brace_x = -0.6
                ax.plot([brace_x, brace_x], [Vs, Vs+Vv], color='black
