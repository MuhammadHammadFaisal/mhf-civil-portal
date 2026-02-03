import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def app():
    st.markdown("---")
    
    # 1. SELECT MODE
    mode = st.radio("Select Solver Mode:", ["Numeric Calculation", "Symbolic / Formula Finder"], horizontal=True)

    # ==========================================
    # MODE A: NUMERIC CALCULATION
    # ==========================================
    if "Numeric" in mode:
        st.caption("Enter parameters. The INPUT diagram updates live. The RESULT diagram appears after solving.")
        
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
                self.tol = 1e-6
                self.log = []
                self.inputs = []

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
                    
                    # 0. Density <-> Unit Weight Conversions
                    if known('rho_bulk') and not known('gamma_bulk'):
                        p['gamma_bulk'] = p['rho_bulk'] * self.gamma_w
                        self.add_log('gamma_bulk', r'\rho_{bulk} g', f"{p['rho_bulk']:.2f} \\cdot 9.81", p['gamma_bulk'])
                        changed = True
                    if known('gamma_bulk') and not known('rho_bulk'):
                        p['rho_bulk'] = p['gamma_bulk'] / self.gamma_w
                    
                    if known('rho_dry') and not known('gamma_dry'):
                        p['gamma_dry'] = p['rho_dry'] * self.gamma_w
                        self.add_log('gamma_dry', r'\rho_{dry} g', f"{p['rho_dry']:.2f} \\cdot 9.81", p['gamma_dry'])
                        changed = True
                    if known('gamma_dry') and not known('rho_dry'):
                        p['rho_dry'] = p['gamma_dry'] / self.gamma_w

                    # 1. Fundamental Relations
                    if known('n') and not known('e') and p['n'] < 1:
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
                    if known('w') and known('Gs') and known('e') and not known('Sr') and p['e'] > self.tol:
                        p['Sr'] = (p['w'] * p['Gs']) / p['e']
                        sub = r'\frac{' + f"{p['w']:.3f} \\cdot {p['Gs']:.2f}" + r'}{' + f"{p['e']:.3f}" + r'}'
                        self.add_log('Sr', r'\frac{w G_s}{e}', sub, p['Sr'])
                        changed = True
                    if known('w') and known('Gs') and known('Sr') and not known('e') and abs(p['Sr']) > self.tol:
                        p['e'] = (p['w'] * p['Gs']) / p['Sr']
                        sub = r'\frac{' + f"{p['w']:.3f} \\cdot {p['Gs']:.2f}" + r'}{' + f"{p['Sr']:.3f}" + r'}'
                        self.add_log('e', r'\frac{w G_s}{S_r}', sub, p['e'])
                        changed = True
                    if known('Sr') and known('e') and known('Gs') and not known('w') and p['Gs'] > self.tol:
                        p['w'] = (p['Sr'] * p['e']) / p['Gs']
                        sub = r'\frac{' + f"{p['Sr']:.3f} \\cdot {p['e']:.3f}" + r'}{' + f"{p['Gs']:.2f}" + r'}'
                        self.add_log('w', r'\frac{S_r e}{G_s}', sub, p['w'])
                        changed = True
                    if known('Sr') and known('e') and known('w') and not known('Gs') and abs(p['w']) > self.tol:
                        p['Gs'] = (p['Sr'] * p['e']) / p['w']
                        sub = r'\frac{' + f"{p['Sr']:.3f} \\cdot {p['e']:.3f}" + r'}{' + f"{p['w']:.3f}" + r'}'
                        self.add_log('Gs', r'\frac{S_r e}{w}', sub, p['Gs'])
                        changed = True

                    # 3. Unit Weights
                    if known('Gs') and known('e') and not known('gamma_dry'):
                        p['gamma_dry'] = (p['Gs'] * self.gamma_w) / (1 + p['e'])
                        sub = r'\frac{' + f"{p['Gs']:.2f} \\cdot 9.81" + r'}{1 + ' + f"{p['e']:.3f}" + r'}'
                        self.add_log('gamma_dry', r'\frac{G_s \gamma_w}{1 + e}', sub, p['gamma_dry'])
                        changed = True
                    if known('Gs') and known('e') and known('w') and not known('gamma_bulk'):
                        p['gamma_bulk'] = (p['Gs'] * self.gamma_w * (1 + p['w'])) / (1 + p['e'])
                        sub = r'\frac{' + f"{p['Gs']:.2f} \\cdot 9.81 (1 + {p['w']:.3f})" + r'}{1 + ' + f"{p['e']:.3f}" + r'}'
                        self.add_log('gamma_bulk', r'\frac{G_s \gamma_w (1+w)}{1+e}', sub, p['gamma_bulk'])
                        changed = True
                    if known('Gs') and known('e') and known('Sr') and not known('gamma_bulk'):
                        p['gamma_bulk'] = ((p['Gs'] + p['Sr'] * p['e']) * self.gamma_w) / (1 + p['e'])
                        sub = r'\frac{(' + f"{p['Gs']:.2f} + {p['Sr']:.3f}\\cdot{p['e']:.3f}" + r')9.81}{1 + ' + f"{p['e']:.3f}" + r'}'
                        self.add_log('gamma_bulk', r'\frac{(G_s + S_r e)\gamma_w}{1+e}', sub, p['gamma_bulk'])
                        changed = True
                    if known('Gs') and known('e') and not known('gamma_sat'):
                        p['gamma_sat'] = ((p['Gs'] + p['e']) * self.gamma_w) / (1 + p['e'])
                        sub = r'\frac{(' + f"{p['Gs']:.2f} + {p['e']:.3f}" + r')9.81}{1 + ' + f"{p['e']:.3f}" + r'}'
                        self.add_log('gamma_sat', r'\frac{(G_s + e)\gamma_w}{1+e}', sub, p['gamma_sat'])
                        changed = True
                    if known('gamma_dry') and known('w') and not known('gamma_bulk'):
                        p['gamma_bulk'] = p['gamma_dry'] * (1 + p['w'])
                        sub = f"{p['gamma_dry']:.2f}(1 + {p['w']:.3f})"
                        self.add_log('gamma_bulk', r'\gamma_{dry}(1+w)', sub, p['gamma_bulk'])
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
                        sub = r'\frac{' + f"{p['Gs']:.2f} \\cdot 9.81" + r'}{' + f"{p['gamma_dry']:.2f}" + r'} - 1'
                        self.add_log('e', r'\frac{G_s \gamma_w}{\gamma_{dry}} - 1', sub, p['e'])
                        changed = True
                    if known('gamma_bulk') and known('gamma_dry') and not known('w') and p['gamma_dry'] > self.tol:
                        p['w'] = (p['gamma_bulk'] / p['gamma_dry']) - 1
                        sub = r'\frac{' + f"{p['gamma_bulk']:.2f}" + r'}{' + f"{p['gamma_dry']:.2f}" + r'} - 1'
                        self.add_log('w', r'\frac{\gamma_{bulk}}{\gamma_{dry}} - 1', sub, p['w'])
                        changed = True
                    if known('gamma_sat') and known('Gs') and not known('e'):
                        numerator = (p['Gs'] * self.gamma_w) - p['gamma_sat']
                        denom = p['gamma_sat'] - self.gamma_w
                        if abs(denom) > self.tol:
                            p['e'] = numerator / denom
                            sub = r'\frac{' + f"{p['Gs']:.2f}9.81 - {p['gamma_sat']:.2f}" + r'}{' + f"{p['gamma_sat']:.2f} - 9.81" + r'}'
                            self.add_log('e', r'\frac{G_s \gamma_w - \gamma_{sat}}{\gamma_{sat} - \gamma_w}', sub, p['e'])
                            changed = True
                    if known('gamma_sat') and known('gamma_dry') and not known('n'):
                        p['n'] = (p['gamma_sat'] - p['gamma_dry']) / self.gamma_w
                        sub = r'\frac{' + f"{p['gamma_sat']:.2f} - {p['gamma_dry']:.2f}" + r'}{9.81}'
                        self.add_log('n', r'\frac{\gamma_{sat} - \gamma_{dry}}{\gamma_w}', sub, p['n'])
                        changed = True
                    if known('gamma_dry') and known('n') and not known('gamma_sat'):
                        p['gamma_sat'] = p['gamma_dry'] + p['n'] * self.gamma_w
                        sub = f"{p['gamma_dry']:.2f} + {p['n']:.3f}\\cdot9.81"
                        self.add_log('gamma_sat', r'\gamma_{dry} + n \gamma_w', sub, p['gamma_sat'])
                        changed = True

                    # --- NEW: Solve for Gs (Specific Gravity) ---
                    # Case: Given Gamma_dry and e -> Find Gs
                    if known('gamma_dry') and known('e') and not known('Gs'):
                        p['Gs'] = (p['gamma_dry'] * (1 + p['e'])) / self.gamma_w
                        sub = r'\frac{' + f"{p['gamma_dry']:.2f}(1 + {p['e']:.3f})" + r'}{9.81}'
                        self.add_log('Gs', r'\frac{\gamma_{dry}(1+e)}{\gamma_w}', sub, p['Gs'])
                        changed = True

                    # Case: Given Gamma_sat and e -> Find Gs
                    if known('gamma_sat') and known('e') and not known('Gs'):
                        p['Gs'] = ((p['gamma_sat'] * (1 + p['e'])) / self.gamma_w) - p['e']
                        sub = r'\frac{' + f"{p['gamma_sat']:.2f}(1 + {p['e']:.3f})" + r'}{9.81} - ' + f"{p['e']:.3f}"
                        self.add_log('Gs', r'\frac{\gamma_{sat}(1+e)}{\gamma_w} - e', sub, p['Gs'])
                        changed = True
                        
                    # Case: Given Gamma_bulk, w, and e -> Find Gs
                    if known('gamma_bulk') and known('w') and known('e') and not known('Gs'):
                        p['Gs'] = (p['gamma_bulk'] * (1 + p['e'])) / (self.gamma_w * (1 + p['w']))
                        sub = r'\frac{' + f"{p['gamma_bulk']:.2f}(1 + {p['e']:.3f})" + r'}{9.81(1 + ' + f"{p['w']:.3f})" + r'}'
                        self.add_log('Gs', r'\frac{\gamma_{bulk}(1+e)}{\gamma_w(1+w)}', sub, p['Gs'])
                        changed = True

                    # 5. Saturation
                    if known('gamma_sat') and not known('gamma_sub'):
                        p['gamma_sub'] = p['gamma_sat'] - self.gamma_w
                        sub = f"{p['gamma_sat']:.2f} - 9.81"
                        self.add_log('gamma_sub', r'\gamma_{sat} - \gamma_w', sub, p['gamma_sub'])
                        changed = True
                    if known('gamma_bulk') and known('Sr') and abs(p['Sr'] - 1.0) <= self.tol and not known('gamma_sub'):
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

            
            if e > 5: e = 5
            if e < 0: e = 0.1

            Vs = 1.0
            Vv = e
            Vw = Sr * e
            Va = Vv - Vw
            
            Ms = Gs 
            Mw = w * Ms if (w is not None and Gs is not None) else Vw * 1.0 

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
                ax.plot([brace_x, brace_x], [Vs, Vs+Vv], color='black', lw=1)
                ax.plot([brace_x, brace_x+0.1], [Vs, Vs], color='black', lw=1)
                ax.plot([brace_x, brace_x+0.1], [Vs+Vv, Vs+Vv], color='black', lw=1)
                txt = get_label('e', raw_e)
                col = get_color('e')
                ax.text(brace_x-0.1, Vs+Vv/2, f'$e={txt}$', ha='right', va='center', fontsize=10, color=col, fontweight='bold')

            ax.text(1.8, 1+e+0.1, r'$Mass$', ha='center', fontsize=10, fontweight='bold')
            txt_gs = get_label('Gs', raw_Gs, "{:.2f}")
            col_gs = get_color('Gs')
            ax.text(1.1, Vs/2, f'$M_s$ ($G_s={txt_gs}$)', ha='left', va='center', fontsize=9, color=col_gs)

            if Vw > 0.001:
                txt_w = get_label('w', raw_w, "{:.3f}")
                col_w = get_color('w')
                ax.text(1.1, Vs + Vw/2, f'$M_w$ ($w={txt_w}$)', ha='left', va='center', fontsize=9, color=col_w)

            txt_sr = get_label('Sr', raw_Sr, "{:.2f}")
            col_sr = get_color('Sr')
            ax.text(0.5, 1+e+0.15, f'$S_r={txt_sr}$', ha='center', fontsize=10, color=col_sr, fontweight='bold')

            title = "Input Preview" if not is_result_mode else "Final State"
            ax.set_title(title, fontsize=10)
            return fig

        # ==================================================
        # LAYOUT: NUMERIC DASHBOARD
        # ==================================================
        
        solver = SoilState()
        
        # --- TOP SECTION: INPUTS & PREVIEW ---
        top_col1, top_col2 = st.columns([1, 1])
        
        with top_col1:
            st.markdown("### 1. Inputs")
            
            condition = st.radio("Soil State:", ["Partially Saturated", "Fully Saturated (Sr=1)", "Dry (Sr=0)"])
            if "Fully" in condition: solver.set_param('Sr', 1.0)
            elif "Dry" in condition: solver.set_param('Sr', 0.0)

            c1, c2 = st.columns(2)
            with c1:
                w_in = st.number_input("Water Content (w)", 0.0, step=0.01, format="%.3f")
                Gs_in = st.number_input("Specific Gravity (Gs)", 0.0, step=0.01, format="%.2f")
                e_in = st.number_input("Void Ratio (e)", 0.0, step=0.01)
                n_in = st.number_input("Porosity (n)", 0.0, step=0.01)
                Sr_in = st.number_input("Saturation (Sr)", 0.0, 1.0, step=0.01)
                
            with c2:
                # UPDATED LABELS TO USE γ_bulk / γ_dry (Consistent with Symbolic Mode)
                gamma_b_in = st.number_input("Bulk Unit Wt (γ_bulk)", 0.0, step=0.1)
                gamma_d_in = st.number_input("Dry Unit Wt (γ_dry)", 0.0, step=0.1)
                rho_b_in = st.number_input("Bulk Density (ρ_bulk)", 0.0, step=0.01)
                rho_d_in = st.number_input("Dry Density (ρ_dry)", 0.0, step=0.01)

            if w_in > 0: solver.set_param('w', w_in)
            if Gs_in > 0: solver.set_param('Gs', Gs_in)
            if e_in > 0: solver.set_param('e', e_in)
            if n_in > 0: solver.set_param('n', n_in)
            if "Partially" in condition and Sr_in > 0: solver.set_param('Sr', Sr_in)
            if gamma_b_in > 0: solver.set_param('gamma_bulk', gamma_b_in)
            if gamma_d_in > 0: solver.set_param('gamma_dry', gamma_d_in)
            if rho_b_in > 0: solver.set_param('rho_bulk', rho_b_in)
            if rho_d_in > 0: solver.set_param('rho_dry', rho_d_in)

        with top_col2:
            st.markdown("### Input Monitor")
            fig_preview = draw_phase_diagram(solver.params, solver.inputs, is_result_mode=False)
            st.pyplot(fig_preview)
            plt.close(fig_preview)

        
        solve_btn = st.button("Solve Numeric Problem", type="primary", use_container_width=True)

        # --- BOTTOM SECTION: RESULTS ---
        if solve_btn:
            solver.solve()
            st.markdown("### 2. Solution")
            
            if not solver.log:
                st.error("Not enough information provided to solve.")
            else:
                bot_col1, bot_col2 = st.columns([1, 1])
                with bot_col1:
                    st.success("Calculation Complete!")
                    p = solver.params
                    if p['w'] is not None: st.latex(f"w = {p['w']:.4f}")
                    if p['Gs'] is not None: st.latex(f"G_s = {p['Gs']:.3f}")
                    if p['e'] is not None: st.latex(f"e = {p['e']:.4f}")
                    if p['Sr'] is not None: st.latex(f"S_r = {p['Sr']:.4f}")
                    if p['gamma_bulk']: st.latex(r"\gamma_{bulk} = " + f"{p['gamma_bulk']:.2f}")
                    if p['gamma_dry']: st.latex(r"\gamma_{dry} = " + f"{p['gamma_dry']:.2f}")
                    if p['rho_bulk']: st.latex(r"\rho_{bulk} = " + f"{p['rho_bulk']:.2f}")
                    if p['rho_dry']: st.latex(r"\rho_{dry} = " + f"{p['rho_dry']:.2f}")
                    
                    if p['gamma_sat']: st.latex(r"\gamma_{sat} = " + f"{p['gamma_sat']:.2f}")
                    if p['gamma_sub']: st.latex(r"\gamma' = " + f"{p['gamma_sub']:.2f}")

                with bot_col2:
                    fig_final = draw_phase_diagram(solver.params, solver.inputs, is_result_mode=True)
                    st.pyplot(fig_final)
                    plt.close(fig_final)

                with st.expander("Show Calculation Steps", expanded=True):
                    for step in solver.log:
                        st.latex(f"{step['Variable']} = {step['Formula']} = {step['Substitution']} = \\mathbf{{{step['Result']:.4f}}}")

        # --- RELATIVE DENSITY ---
        st.markdown("---")
        st.markdown("")
        with st.container(border=True):
            st.subheader("Relative Density ($D_r$) Calculator")
            rc1, rc2, rc3 = st.columns(3)
            with rc1: e_curr = st.number_input("Current e", 0.0, step=0.01, key="dr_e")
            with rc2: e_max = st.number_input("Max e", 0.0, step=0.01, key="dr_emax")
            with rc3: e_min = st.number_input("Min e", 0.0, step=0.01, key="dr_emin")
            
            if st.button("Calculate Dr"):
                if e_max > e_min:
                    Dr = (e_max - e_curr) / (e_max - e_min)
                    st.latex(r"D_r = \frac{e_{max} - e}{e_{max} - e_{min}} = " + f"{Dr*100:.1f}\\%")
                else:
                    st.error("e_max must be > e_min")

    # ==========================================
    # MODE B: SYMBOLIC / FORMULA FINDER
    # ==========================================
    elif "Symbolic" in mode:
        st.subheader("Formula Finder")
        st.caption("Select the variables you **KNOW** to find the formula for the variable you **WANT**.")

        col1, col2 = st.columns(2)
        with col1:
            # 100% CONSISTENT DROPDOWN OPTIONS (Using γ_subscript format)
            known_vars = st.multiselect(
                "I have these variables (Inputs):",
                options=[
                    "w (Water Content)", 
                    "Gs (Specific Gravity)", 
                    "e (Void Ratio)", 
                    "n (Porosity)", 
                    "Sr (Saturation)", 
                    "γ_bulk (Bulk Unit Wt)", 
                    "γ_dry (Dry Unit Wt)",   
                    "γ_sat (Saturated Unit Wt)" 
                ],
                default=["Gs (Specific Gravity)", "e (Void Ratio)"]
            )
            # This splits the string and grabs the symbol (e.g., "γ_bulk")
            cleaned_knowns = set([k.split(" ")[0] for k in known_vars])

        with col2:
            target_var_raw = st.selectbox(
                "I want to find (Target):",
                options=[
                    "Gs (Specific Gravity)",
                    "γ_dry (Dry Unit Wt)", 
                    "γ_bulk (Bulk Unit Wt)",
                    "γ_sat (Saturated Unit Wt)", 
                    "γ' (Submerged Unit Wt)",   
                    "e (Void Ratio)", "n (Porosity)", "Sr (Saturation)", "w (Water Content)"
                ]
            )
            target = target_var_raw.split(" ")[0]

        # UPDATED DICTIONARY MATCHING DROPDOWN EXACTLY
        formulas = {
            'Gs': [
                ({'γ_dry', 'e'}, r"G_s = \frac{\gamma_{dry}(1+e)}{\gamma_w}", "Back-calculated from Dry Unit Weight."),
                ({'γ_sat', 'e'}, r"G_s = \frac{\gamma_{sat}(1+e)}{\gamma_w} - e", "Back-calculated from Saturated Unit Weight."),
                ({'w', 'Sr', 'e'}, r"G_s = \frac{S_r e}{w}", "From the fundamental relationship Se = wGs.")
            ],
            'γ_dry': [
                ({'Gs', 'e'}, r"\gamma_{dry} = \frac{G_s \gamma_w}{1 + e}", "Basic definition using Void Ratio."),
                ({'γ_bulk', 'w'}, r"\gamma_{dry} = \frac{\gamma_{bulk}}{1 + w}", "Derived from Bulk Density and Water Content."),
                ({'Gs', 'n'}, r"\gamma_{dry} = G_s \gamma_w (1 - n)", "Using Porosity instead of Void Ratio.")
            ],
            'γ_bulk': [
                ({'Gs', 'e', 'w'}, r"\gamma_{bulk} = \frac{G_s \gamma_w (1 + w)}{1 + e}", "The general relationship for unit weight."),
                ({'Gs', 'e', 'Sr'}, r"\gamma_{bulk} = \frac{(G_s + S_r e)\gamma_w}{1 + e}", "Using Saturation instead of Water Content."),
                ({'γ_dry', 'w'}, r"\gamma_{bulk} = \gamma_{dry}(1 + w)", "From dry unit weight and water content.")
            ],
            'γ_sat': [
                ({'Gs', 'e'}, r"\gamma_{sat} = \frac{(G_s + e)\gamma_w}{1 + e}", "Assumes Sr = 1 (Fully Saturated)."),
                ({'γ_dry', 'n'}, r"\gamma_{sat} = \gamma_{dry} + n \gamma_w", "Relation between saturated and dry states.")
            ],
            "γ'": [
                ({'γ_sat'}, r"\gamma' = \gamma_{sat} - \gamma_w", "Archimedes' principle for submerged soil."),
                ({'Gs', 'e'}, r"\gamma' = \frac{(G_s - 1)\gamma_w}{1 + e}", "Standard submerged weight formula.")
            ],
            'e': [
                ({'n'}, r"e = \frac{n}{1 - n}", "Conversion from Porosity."),
                ({'w', 'Gs', 'Sr'}, r"e = \frac{w G_s}{S_r}", "From the fundamental relationship Se = wGs."),
                ({'γ_dry', 'Gs'}, r"e = \frac{G_s \gamma_w}{\gamma_{dry}} - 1", "Back-calculated from Dry Unit Weight."),
                ({'γ_sat', 'Gs'}, r"e = \frac{G_s \gamma_w - \gamma_{sat}}{\gamma_{sat} - \gamma_w}", "Back-calculated from Saturated Unit Weight.")
            ],
            'n': [
                ({'e'}, r"n = \frac{e}{1 + e}", "Conversion from Void Ratio."),
                ({'γ_sat', 'γ_dry'}, r"n = \frac{\gamma_{sat} - \gamma_{dry}}{\gamma_w}", "Difference between Sat and Dry states.")
            ],
            'Sr': [
                ({'w', 'Gs', 'e'}, r"S_r = \frac{w G_s}{e}", "Rearranged from Se = wGs.")
            ],
            'w': [
                ({'Sr', 'e', 'Gs'}, r"w = \frac{S_r e}{G_s}", "Rearranged from Se = wGs."),
                ({'γ_bulk', 'γ_dry'}, r"w = \frac{\gamma_{bulk}}{\gamma_{dry}} - 1", "From bulk and dry unit weights.")
            ]
        }

        st.markdown("---")
        found_any = False
        
        if target in formulas:
            for requirements, latex, description in formulas[target]:
                if requirements.issubset(cleaned_knowns):
                    st.success(f"**Formula Found:** {description}")
                    st.latex(latex)
                    found_any = True
        
        if not found_any:
            st.warning(f"No direct formula found for **{target}** with the variables you selected.")
            if target in formulas:
                st.markdown("**To find this variable, you typically need combinations like:**")
                for reqs, _, _ in formulas[target]:
                    pretty_reqs = ", ".join(list(reqs))
                    st.markdown(f"- {pretty_reqs}")
