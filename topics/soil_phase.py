import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def app():
    st.markdown("---")
    
    # 1. SELECT MODE
    mode = st.radio("Select Solver Mode:", ["Numeric Calculation", "Symbolic / Formula Finder"], horizontal=True)

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
                    'gamma_sub': None, 'na': None
                }
                self.rho_w = 1.0
                self.gamma_w = 9.81
                self.log = [] 

                self.latex_map = {
                    'w': 'w', 'Gs': 'G_s', 'e': 'e', 'n': 'n', 'Sr': 'S_r',
                    'rho_bulk': r'\rho_{bulk}', 'rho_dry': r'\rho_{dry}',
                    'gamma_bulk': r'\gamma_{bulk}', 'gamma_dry': r'\gamma_{dry}', 
                    'gamma_sat': r'\gamma_{sat}',
                    'gamma_sub': r'\gamma^\prime (Submerged)',
                    'na': r'n_a (Air Content)'
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

                    # --- NEW: MISSING CONCEPTS ---
                    if known('gamma_bulk') and p['Sr'] == 1.0 and not known('gamma_sub'):
                        p['gamma_sub'] = p['gamma_bulk'] - self.gamma_w
                        self.add_log('gamma_sub', r'\gamma_{sat} - \gamma_w', f"{p['gamma_bulk']:.2f} - 9.81", p['gamma_sub'])
                        changed = True
                    
                    if known('n') and known('Sr') and not known('na'):
                        p['na'] = p['n'] * (1 - p['Sr'])
                        self.add_log('na', r'n(1 - S_r)', f"{p['n']:.3f}(1 - {p['Sr']:.3f})", p['na'])
                        changed = True

                    iterations += 1

        # --- DRAWING FUNCTION ---
        def draw_phase_diagram(solver_params):
            """Generates the 3-phase diagram using Matplotlib based on calculated results."""
            # Extract basic params needed for drawing (Use defaults if missing to avoid crash)
            e = solver_params.get('e', 0.5)
            if e is None: e = 0.5
            
            Gs = solver_params.get('Gs', 2.65)
            if Gs is None: Gs = 2.7
            
            Sr = solver_params.get('Sr', 0.5)
            if Sr is None: Sr = 0.5

            w = solver_params.get('w', 0.1)
            
            # Assumptions for Phase Diagram (Basis: Vs = 1)
            Vs = 1.0
            Vv = e
            Vw = Sr * e
            Va = Vv - Vw
            
            Ms = Gs # Since rho_w = 1 g/cm3 implicitly in this unitless scaling
            Mw = w * Ms if w is not None else Vw * 1.0 # Fallback
            Ma = 0

            # Plot Setup
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.set_xlim(-1, 2)
            ax.set_ylim(0, 1 + e + 0.2)
            ax.axis('off')

            # --- DRAW RECTANGLES ---
            # 1. Solids (Bottom)
            ax.add_patch(patches.Rectangle((0, 0), 1, Vs, linewidth=2, edgecolor='black', facecolor='#D2B48C'))
            ax.text(0.5, Vs/2, 'Solids (S)', ha='center', va='center', fontsize=12, fontweight='bold')

            # 2. Water (Middle)
            if Vw > 0:
                ax.add_patch(patches.Rectangle((0, Vs), 1, Vw, linewidth=2, edgecolor='black', facecolor='#87CEEB'))
                ax.text(0.5, Vs + Vw/2, 'Water (W)', ha='center', va='center', fontsize=12, fontweight='bold')

            # 3. Air (Top)
            if Va > 0.01:
                ax.add_patch(patches.Rectangle((0, Vs + Vw), 1, Va, linewidth=2, edgecolor='black', facecolor='#F0F8FF'))
                ax.text(0.5, Vs + Vw + Va/2, 'Air (A)', ha='center', va='center', fontsize=12, fontweight='bold')

            # --- ANNOTATIONS (LEFT - VOLUMES) ---
            # Header
            ax.text(-0.5, 1+e+0.1, r'$Volume \ (V)$', ha='center', fontsize=10, fontweight='bold')
            
            # Vs Label
            ax.text(0, Vs/2, f'$V_s = {Vs}$ ', ha='right', va='center')
            
            # Vw Label
            if Vw > 0:
                ax.text(0, Vs + Vw/2, f'$V_w = {Vw:.2f}$ ', ha='right', va='center')
            
            # Va Label
            if Va > 0.01:
                ax.text(0, Vs + Vw + Va/2, f'$V_a = {Va:.2f}$ ', ha='right', va='center')

            # Curly Brace for 'e' (Void Ratio)
            # We draw a bracket spanning Air + Water
            if Vv > 0:
                brace_x = -0.6
                brace_y_bottom = Vs
                brace_y_top = Vs + Vv
                # Draw main line
                ax.plot([brace_x, brace_x], [brace_y_bottom, brace_y_top], color='black', lw=1)
                # Draw top/bottom ticks
                ax.plot([brace_x, brace_x + 0.1], [brace_y_bottom, brace_y_bottom], color='black', lw=1)
                ax.plot([brace_x, brace_x + 0.1], [brace_y_top, brace_y_top], color='black', lw=1)
                # Label
                ax.text(brace_x - 0.1, Vs + Vv/2, f'$e = {e:.3f}$', ha='right', va='center', fontsize=12, color='red')

            # --- ANNOTATIONS (RIGHT - MASSES) ---
            # Header
            ax.text(1.5, 1+e+0.1, r'$Mass \ (M)$', ha='center', fontsize=10, fontweight='bold')
            
            # Ms Label
            ax.text(1.05, Vs/2, f'$M_s = {Ms:.2f}$', ha='left', va='center')
            
            # Mw Label
            if Vw > 0:
                ax.text(1.05, Vs + Vw/2, f'$M_w = {Mw:.2f}$', ha='left', va='center')
            
            # Ma Label
            if Va > 0.01:
                ax.text(1.05, Vs + Vw + Va/2, f'$M_a = 0$', ha='left', va='center')

            return fig

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
        
        if st.button("Solve Numeric Problem", type="primary"):
            solver.solve()
            st.success("Calculation Complete!")
            
            # 1. Standard Results
            if solver.log:
                with st.expander("📝 View Step-by-Step Solution", expanded=False):
                    for step in solver.log:
                        st.markdown(f"**Found ${step['Variable']}$:**")
                        st.latex(f"{step['Variable']} = {step['Formula']} = {step['Substitution']} = \\mathbf{{{step['Result']:.4f}}}")
            else:
                st.error("Not enough info to solve.")

            st.markdown("### Final Results")
            res_col1, res_col2 = st.columns(2)
            def get_val(key): return solver.params.get(key)

            with res_col1:
                st.markdown("**Physical Properties**")
                if get_val('w') is not None: st.latex(f"w = {get_val('w'):.4f}")
                if get_val('Gs') is not None: st.latex(f"G_s = {get_val('Gs'):.3f}")
                if get_val('e') is not None: st.latex(f"e = {get_val('e'):.4f}")
                if get_val('n') is not None: st.latex(f"n = {get_val('n'):.4f}")
                if get_val('Sr') is not None: st.latex(f"S_r = {get_val('Sr'):.4f}")
                if get_val('na') is not None: st.latex(f"n_a = {get_val('na'):.4f}")
            
            with res_col2:
                st.markdown("**Unit Weights**")
                if get_val('gamma_bulk') is not None: st.latex(r"\gamma_{bulk} = " + f"{get_val('gamma_bulk'):.2f}")
                if get_val('gamma_dry') is not None: st.latex(r"\gamma_{dry} = " + f"{get_val('gamma_dry'):.2f}")
                if get_val('gamma_sub') is not None: st.latex(r"\gamma' = " + f"{get_val('gamma_sub'):.2f}")

            # --- 2. PHASE DIAGRAM ---
            st.markdown("---")
            st.subheader("Interactive Phase Diagram")
            st.caption("Visual representation of Volumes (left) and Masses (right) assuming Vs = 1.")
            
            # Only draw if we have minimum params (e, Gs) to make a valid drawing
            if get_val('e') is not None and get_val('Gs') is not None:
                fig = draw_phase_diagram(solver.params)
                st.pyplot(fig)
            else:
                st.warning("Need at least 'Void Ratio (e)' and 'Specific Gravity (Gs)' to generate diagram.")

        # --- RELATIVE DENSITY ---
        st.markdown("---")
        st.subheader("Relative Density (Dr)")
        st.caption("Calculate density state based on e_max and e_min.")
        
        c1, c2, c3 = st.columns(3)
        with c1: e_curr = st.number_input("Current Void Ratio (e)", 0.0, step=0.01, key="dr_e")
        with c2: e_max = st.number_input("Max Void Ratio (e_max)", 0.0, step=0.01, key="dr_emax")
        with c3: e_min = st.number_input("Min Void Ratio (e_min)", 0.0, step=0.01, key="dr_emin")
        
        if st.button("Calculate Relative Density", type="primary"):
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
