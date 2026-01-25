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
        st.caption("Enter parameters. The INPUT diagram (top) updates live. The RESULT diagram (bottom) appears after solving.")
        
        # --- CLASS DEFINITION ---
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
                self.inputs = [] 

                self.latex_map = {
                    'w': 'w', 'Gs': 'G_s', 'e': 'e', 'n': 'n', 'Sr': 'S_r',
                    'rho_bulk': r'\rho_{bulk}', 'rho_dry': r'\rho_{dry}',
                    'gamma_bulk': r'\gamma_{bulk}', 'gamma_dry': r'\gamma_{dry}', 
                    'gamma_sat': r'\gamma_{sat}', 'gamma_sub': r'\gamma^\prime', 'na': r'n_a'
                }

            def set_param(self, key, value):
                # CHANGE: Changed "> 0" to ">= 0" so 0.0 is accepted (needed for Dry state)
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

                    # 5. Saturation & Submerged
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

        # --- DRAWING FUNCTION (DUAL MODE) ---
        def draw_phase_diagram(params, inputs_list, is_result_mode=False):
            """
            is_result_mode=False: Draws INPUT diagram (Preview). 
                                  Uses fixed geometry but labels knowns Green/Unknowns Red.
            is_result_mode=True:  Draws RESULT diagram.
                                  Uses actual calculated geometry.
            """
            
            # 1. Setup Geometry Variables
            # If Result Mode: Use actual calculated values.
            # If Input Mode: Use placeholders (e=0.7, Sr=0.5) just to make the box look nice,
            # unless the user actually typed a value, then use that to be responsive.
            
            raw_e = params.get('e')
            raw_Sr = params.get('Sr')
            raw_w = params.get('w')
            raw_Gs = params.get('Gs')

            if is_result_mode:
                # Use Calculated Values
                e = raw_e if raw_e is not None else 0.5
                Sr = raw_Sr if raw_Sr is not None else 0.5
                Gs = raw_Gs if raw_Gs is not None else 2.7
                w = raw_w if raw_w is not None else 0.1
            else:
                # Use Placeholders for geometry unless specified, so diagram doesn't look broken
                e = raw_e if raw_e is not None else 0.7 
                Sr = raw_Sr if raw_Sr is not None else 0.5
                Gs = raw_Gs if raw_Gs is not None else 2.7
                w = raw_w if raw_w is not None else 0.2

            # Calculations for Rectangle Heights
            Vs = 1.0
            Vv = e
            Vw = Sr * e
            Va = Vv - Vw
            
            Ms = Gs 
            Mw = w * Ms if w is not None else Vw * 1.0 
            Ma = 0

            # 2. Setup Plot
            fig, ax = plt.subplots(figsize=(5, 3.5)) # Compact size
            ax.set_xlim(-1.5, 2.5) 
            ax.set_ylim(0, max(1.5, 1 + e + 0.3)) 
            ax.axis('off')

            # Helper for text color
            def get_color(key):
                if key in inputs_list: return 'green' # User typed it
                if is_result_mode: return 'red'       # Calculator found it
                return 'red'                          # Missing in input mode

            # Helper for label text
            def get_label(key, val, fmt="{:.3f}"):
                if key in inputs_list: return fmt.format(val) # Show value if typed
                if is_result_mode and val is not None: return fmt.format(val) # Show if solved
                return "?" # Show ? if missing in input mode

            # --- DRAW RECTANGLES ---
            # Solids
            ax.add_patch(patches.Rectangle((0, 0), 1, Vs, linewidth=2, edgecolor='black', facecolor='#D2B48C'))
            ax.text(0.5, Vs/2, 'S', ha='center', va='center', fontsize=10, fontweight='bold')

            # Water
            if Vw > 0.001:
                ax.add_patch(patches.Rectangle((0, Vs), 1, Vw, linewidth=2, edgecolor='black', facecolor='#87CEEB'))
                if Vw > 0.15: ax.text(0.5, Vs + Vw/2, 'W', ha='center', va='center', fontsize=10, fontweight='bold')

            # Air
            if Va > 0.001:
                ax.add_patch(patches.Rectangle((0, Vs + Vw), 1, Va, linewidth=2, edgecolor='black', facecolor='#F0F8FF'))
                if Va > 0.15: ax.text(0.5, Vs + Vw + Va/2, 'A', ha='center', va='center', fontsize=10, fontweight='bold')

            # --- LABELS (Using helper for color/text) ---
            
            # Left Side (Volumes)
            ax.text(-0.8, 1+e+0.1, r'$Vol$', ha='center', fontsize=10, fontweight='bold')
            ax.text(-0.1, Vs/2, f'$V_s=1$', ha='right', va='center', fontsize=9)
            
            # e Label (The curly brace)
            if Vv > 0:
                brace_x = -0.6
                ax.plot([brace_x, brace_x], [Vs, Vs+Vv], color='black', lw=1)
                ax.plot([brace_x, brace_x+0.1], [Vs, Vs], color='black', lw=1)
                ax.plot([brace_x, brace_x+0.1], [Vs+Vv, Vs+Vv], color='black', lw=1)
                
                txt = get_label('e', raw_e)
                col = get_color('e')
                ax.text(brace_x-0.1, Vs+Vv/2, f'$e={txt}$', ha='right', va='center', fontsize=10, color=col, fontweight='bold')

            # Right Side (Masses)
            ax.text(1.8, 1+e+0.1, r'$Mass$', ha='center', fontsize=10, fontweight='bold')
            
            # Ms (Gs)
            txt_gs = get_label('Gs', raw_Gs, "{:.2f}")
            col_gs = get_color('Gs')
            ax.text(1.1, Vs/2, f'$M_s$ ($G_s={txt_gs}$)', ha='left', va='center', fontsize=9, color=col_gs)

            # Mw (w)
            if Vw > 0.001:
                txt_w = get_label('w', raw_w, "{:.3f}")
                col_w = get_color('w')
                ax.text(1.1, Vs + Vw/2, f'$M_w$ ($w={txt_w}$)', ha='left', va='center', fontsize=9, color=col_w)

            # Sr Label (Top Center)
            txt_sr = get_label('Sr', raw_Sr, "{:.2f}")
            col_sr = get_color('Sr')
            ax.text(0.5, 1+e+0.15, f'$S_r={txt_sr}$', ha='center', fontsize=10, color=col_sr, fontweight='bold')

            # Title
            title = "Input Preview" if not is_result_mode else "Final State"
            ax.set_title(title, fontsize=10)

            return fig

        # ==================================================
        # LAYOUT: SPLIT SCREEN (INPUTS | PREVIEW DIAGRAM)
        # ==================================================
        
        # We define the variables first so we can draw the preview immediately
        solver = SoilState()
        
        # --- TOP SECTION: INPUTS & PREVIEW ---
        top_col1, top_col2 = st.columns([1, 1])
        
        with top_col1:
            st.markdown("### 1. Inputs")
            
            # Condition Radio
            condition = st.radio("Soil State:", ["Partially Saturated", "Fully Saturated (Sr=1)", "Dry (Sr=0)"])
            if "Fully" in condition: solver.set_param('Sr', 1.0)
            elif "Dry" in condition: solver.set_param('Sr', 0.0)

            # Input Fields
            c1, c2 = st.columns(2)
            with c1:
                w_in = st.number_input("Water Content (w)", 0.0, step=0.01, format="%.3f")
                Gs_in = st.number_input("Specific Gravity (Gs)", 0.0, step=0.01, format="%.2f")
                e_in = st.number_input("Void Ratio (e)", 0.0, step=0.01)
            with c2:
                n_in = st.number_input("Porosity (n)", 0.0, step=0.01)
                Sr_in = st.number_input("Saturation (Sr)", 0.0, 1.0, step=0.01)
                gamma_b_in = st.number_input("Bulk Unit Wt", 0.0, step=0.1)
                gamma_d_in = st.number_input("Dry Unit Wt", 0.0, step=0.1)

            # Register Inputs into Solver Object IMMEDIATELY
            if w_in > 0: solver.set_param('w', w_in)
            if Gs_in > 0: solver.set_param('Gs', Gs_in)
            if e_in > 0: solver.set_param('e', e_in)
            if n_in > 0: solver.set_param('n', n_in)
            if "Partially" in condition and Sr_in > 0: solver.set_param('Sr', Sr_in)
            if gamma_b_in > 0: solver.set_param('gamma_bulk', gamma_b_in)
            if gamma_d_in > 0: solver.set_param('gamma_dry', gamma_d_in)

        with top_col2:
            st.markdown("### Input Monitor")
            # Draw Preview Diagram (is_result_mode=False)
            fig_preview = draw_phase_diagram(solver.params, solver.inputs, is_result_mode=False)
            st.pyplot(fig_preview)

        # --- SOLVE BUTTON ---
        st.markdown("---")
        solve_btn = st.button("Solve Numeric Problem", type="primary", use_container_width=True)

        # --- BOTTOM SECTION: RESULTS & FINAL DIAGRAM ---
        if solve_btn:
            solver.solve()
            
            st.markdown("### 2. Solution")
            
            if not solver.log:
                st.error("Not enough information provided to solve.")
            else:
                bot_col1, bot_col2 = st.columns([1, 1])
                
                with bot_col1:
                    st.success("Calculation Complete!")
                    # Text Results
                    p = solver.params
                    st.latex(f"w = {p['w']:.4f}")
                    st.latex(f"G_s = {p['Gs']:.3f}")
                    st.latex(f"e = {p['e']:.4f}")
                    st.latex(f"S_r = {p['Sr']:.4f}")
                    if p['gamma_bulk']: st.latex(r"\gamma_{bulk} = " + f"{p['gamma_bulk']:.2f}")
                    if p['gamma_dry']: st.latex(r"\gamma_{dry} = " + f"{p['gamma_dry']:.2f}")

                with bot_col2:
                    # Draw Final Diagram (is_result_mode=True)
                    fig_final = draw_phase_diagram(solver.params, solver.inputs, is_result_mode=True)
                    st.pyplot(fig_final)

                # Step by Step Expander
                with st.expander("Show Calculation Steps"):
                    for step in solver.log:
                        st.latex(f"{step['Variable']} = {step['Formula']} = {step['Substitution']} = \\mathbf{{{step['Result']:.4f}}}")

        # --- RELATIVE DENSITY ---
        st.markdown("---")
        st.subheader("Relative Density (Dr)")
        c1, c2, c3 = st.columns(3)
        with c1: e_curr = st.number_input("Current e", 0.0, step=0.01, key="dr_e")
        with c2: e_max = st.number_input("Max e (Loose)", 0.0, step=0.01, key="dr_emax")
        with c3: e_min = st.number_input("Min e (Dense)", 0.0, step=0.01, key="dr_emin")
        
        if st.button("Calc Dr"):
            if e_max > e_min:
                Dr = (e_max - e_curr) / (e_max - e_min)
                st.info(f"Relative Density Dr = {Dr*100:.1f}%")
            else:
                st.error("e_max must be > e_min")
