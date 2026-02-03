import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# =========================================================
# MAIN APP
# =========================================================
def app():
    st.markdown("---")

    # =====================================================
    # MODE SELECT
    # =====================================================
    mode = st.radio(
        "Select Solver Mode:",
        ["Numeric Calculation", "Symbolic / Formula Finder"],
        horizontal=True
    )

    # =====================================================
    # NUMERIC MODE
    # =====================================================
    if "Numeric" in mode:
        st.caption(
            "Enter parameters. The INPUT diagram updates live. "
            "The RESULT diagram appears after solving."
        )

        # =================================================
        # SOLVER CLASS
        # =================================================
        class SoilState:
            def __init__(self):
                self.params = {
                    'w': None, 'Gs': None, 'e': None, 'n': None, 'Sr': None,
                    'rho_bulk': None, 'rho_dry': None,
                    'gamma_bulk': None, 'gamma_dry': None,
                    'gamma_sat': None, 'gamma_sub': None, 'na': None
                }

                self.gamma_w = 9.81
                self.tol = 1e-6
                self.log = []
                self.inputs = []

                self.latex_map = {
                    'w': 'w', 'Gs': 'G_s', 'e': 'e', 'n': 'n', 'Sr': 'S_r',
                    'rho_bulk': r'\rho_{bulk}', 'rho_dry': r'\rho_{dry}',
                    'gamma_bulk': r'\gamma_{bulk}', 'gamma_dry': r'\gamma_{dry}',
                    'gamma_sat': r'\gamma_{sat}', 'gamma_sub': r"\gamma'",
                    'na': r'n_a'
                }

            def set_param(self, key, value):
                if value is not None and value >= 0:
                    self.params[key] = float(value)
                    self.inputs.append(key)

            def add_log(self, key, formula, sub, result):
                sym = self.latex_map.get(key, key)
                self.log.append({
                    "Variable": sym,
                    "Formula": formula,
                    "Substitution": sub,
                    "Result": result
                })

            def solve(self):
                p = self.params
                known = lambda k: p[k] is not None
                changed = True
                iterations = 0

                while changed and iterations < 20:
                    changed = False

                    # -------------------------------
                    # n <-> e
                    # -------------------------------
                    if known('n') and not known('e') and p['n'] < 1:
                        p['e'] = p['n'] / (1 - p['n'])
                        self.add_log('e', r'\frac{n}{1-n}', f"{p['n']:.3f}", p['e'])
                        changed = True

                    if known('e') and not known('n'):
                        p['n'] = p['e'] / (1 + p['e'])
                        self.add_log('n', r'\frac{e}{1+e}', f"{p['e']:.3f}", p['n'])
                        changed = True

                    # -------------------------------
                    # Se = wGs
                    # -------------------------------
                    if known('w') and known('Gs') and known('e') and not known('Sr') and p['e'] > self.tol:
                        p['Sr'] = (p['w'] * p['Gs']) / p['e']
                        self.add_log('Sr', r'\frac{wG_s}{e}', "-", p['Sr'])
                        changed = True

                    if known('Sr') and known('e') and known('Gs') and not known('w'):
                        p['w'] = (p['Sr'] * p['e']) / p['Gs']
                        self.add_log('w', r'\frac{S_r e}{G_s}', "-", p['w'])
                        changed = True

                    # -------------------------------
                    # Unit weights
                    # -------------------------------
                    if known('Gs') and known('e') and not known('gamma_dry'):
                        p['gamma_dry'] = (p['Gs'] * self.gamma_w) / (1 + p['e'])
                        self.add_log(
                            'gamma_dry',
                            r'\frac{G_s \gamma_w}{1+e}',
                            "-",
                            p['gamma_dry']
                        )
                        changed = True

                    if known('Gs') and known('e') and known('w') and not known('gamma_bulk'):
                        p['gamma_bulk'] = (
                            p['Gs'] * self.gamma_w * (1 + p['w'])
                        ) / (1 + p['e'])
                        self.add_log(
                            'gamma_bulk',
                            r'\frac{G_s \gamma_w (1+w)}{1+e}',
                            "-",
                            p['gamma_bulk']
                        )
                        changed = True

                    # γ_sat ONLY if fully saturated
                    if (
                        known('Gs') and known('e')
                        and known('Sr') and abs(p['Sr'] - 1.0) < self.tol
                        and not known('gamma_sat')
                    ):
                        p['gamma_sat'] = (
                            (p['Gs'] + p['e']) * self.gamma_w
                        ) / (1 + p['e'])
                        self.add_log(
                            'gamma_sat',
                            r'\frac{(G_s+e)\gamma_w}{1+e}',
                            "Sr = 1",
                            p['gamma_sat']
                        )
                        changed = True

                    # -------------------------------
                    # Submerged unit weight
                    # -------------------------------
                    if known('gamma_sat') and not known('gamma_sub'):
                        p['gamma_sub'] = p['gamma_sat'] - self.gamma_w
                        self.add_log(
                            'gamma_sub',
                            r'\gamma_{sat}-\gamma_w',
                            "-",
                            p['gamma_sub']
                        )
                        changed = True

                    iterations += 1

        # =================================================
        # PHASE DIAGRAM
        # =================================================
        def draw_phase_diagram(params, inputs, is_result=False):
            e = params.get('e', 0.7) or 0.7
            Sr = params.get('Sr', 0.5) or 0.5
            Gs = params.get('Gs', 2.7) or 2.7
            w = params.get('w', 0.2) or 0.2

            e = min(max(e, 0.1), 5)

            Vs = 1
            Vv = e
            Vw = Sr * e
            Va = Vv - Vw

            fig, ax = plt.subplots(figsize=(5, 3.5))
            ax.axis('off')
            ax.set_xlim(-1.3, 2.4)
            ax.set_ylim(0, 1 + e + 0.3)

            ax.add_patch(patches.Rectangle((0, 0), 1, Vs, fc="#D2B48C", ec="black", lw=2))
            ax.text(0.5, Vs / 2, "S", ha="center", va="center", weight="bold")

            if Vw > 0:
                ax.add_patch(patches.Rectangle((0, Vs), 1, Vw, fc="#87CEEB", ec="black", lw=2))
                ax.text(0.5, Vs + Vw / 2, "W", ha="center", va="center", weight="bold")

            if Va > 0:
                ax.add_patch(patches.Rectangle((0, Vs + Vw), 1, Va, fc="#F0F8FF", ec="black", lw=2))
                ax.text(0.5, Vs + Vw + Va / 2, "A", ha="center", va="center", weight="bold")

            title = "Final State" if is_result else "Input Preview"
            ax.set_title(title, fontsize=10)

            return fig

        # =================================================
        # UI
        # =================================================
        solver = SoilState()

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Inputs")
            w = st.number_input("w", 0.0, step=0.01)
            Gs = st.number_input("Gs", 0.0, step=0.01)
            e = st.number_input("e", 0.0, step=0.01)
            Sr = st.number_input("Sr", 0.0, 1.0, step=0.01)

            if w > 0: solver.set_param('w', w)
            if Gs > 0: solver.set_param('Gs', Gs)
            if e > 0: solver.set_param('e', e)
            if Sr >= 0: solver.set_param('Sr', Sr)

        with col2:
            st.subheader("Preview")
            fig = draw_phase_diagram(solver.params, solver.inputs)
            st.pyplot(fig)
            plt.close(fig)

        if st.button("Solve", type="primary", use_container_width=True):
            solver.solve()

            if solver.log:
                st.success("Solved")

                for k, v in solver.params.items():
                    if v is not None:
                        st.latex(f"{solver.latex_map.get(k,k)} = {v:.4f}")

                fig2 = draw_phase_diagram(solver.params, solver.inputs, True)
                st.pyplot(fig2)
                plt.close(fig2)

                with st.expander("Steps", expanded=True):
                    for s in solver.log:
                        st.latex(
                            f"{s['Variable']} = {s['Formula']} = \\mathbf{{{s['Result']:.4f}}}"
                        )
            else:
                st.error("Insufficient data.")

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
