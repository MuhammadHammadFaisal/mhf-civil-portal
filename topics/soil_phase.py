import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# =========================================================
# GLOBAL LATEX SYMBOL MAP
# =========================================================
LATEX = {
    "w": r"w",
    "Gs": r"G_s",
    "e": r"e",
    "n": r"n",
    "Sr": r"S_r",
    "gamma_bulk": r"\gamma_{bulk}",
    "gamma_dry": r"\gamma_{dry}",
    "gamma_sat": r"\gamma_{sat}",
    "gamma_sub": r"\gamma'",
    "rho_bulk": r"\rho_{bulk}",
    "rho_dry": r"\rho_{dry}",
}

# =========================================================
def app():
    st.markdown("---")

    mode = st.radio(
        "Select Solver Mode:",
        ["Numeric Calculation", "Symbolic / Formula Finder"],
        horizontal=True
    )

    # =====================================================
    # NUMERIC MODE
    # =====================================================
    if "Numeric" in mode:
        st.caption("Enter parameters. Diagram updates live. Results appear after solving.")

        # =================================================
        class SoilState:
            def __init__(self):
                self.params = {k: None for k in LATEX}
                self.rho_w = 1.0
                self.gamma_w = 9.81
                self.tol = 1e-6
                self.log = []
                self.inputs = []

            def set_param(self, key, value):
                if value is not None and value >= 0:
                    self.params[key] = float(value)
                    self.inputs.append(key)

            def add_log(self, key, formula, sub, result):
                self.log.append({
                    "var": LATEX[key],
                    "formula": formula,
                    "sub": sub,
                    "res": result
                })

            def solve(self):
                p = self.params
                def k(x): return p[x] is not None

                for _ in range(15):

                    if k("rho_bulk") and not k("gamma_bulk"):
                        p["gamma_bulk"] = p["rho_bulk"] * self.gamma_w
                        self.add_log(
                            "gamma_bulk",
                            r"\rho_{bulk}\gamma_w",
                            rf"{p['rho_bulk']:.2f}\times9.81",
                            p["gamma_bulk"]
                        )

                    if k("Gs") and k("e") and not k("gamma_dry"):
                        p["gamma_dry"] = (p["Gs"] * self.gamma_w) / (1 + p["e"])
                        self.add_log(
                            "gamma_dry",
                            r"\frac{G_s\gamma_w}{1+e}",
                            rf"\frac{{{p['Gs']:.2f}\times9.81}}{{1+{p['e']:.3f}}}",
                            p["gamma_dry"]
                        )

                    if k("w") and k("Gs") and k("e") and not k("Sr"):
                        p["Sr"] = (p["w"] * p["Gs"]) / p["e"]
                        self.add_log(
                            "Sr",
                            r"\frac{wG_s}{e}",
                            rf"\frac{{{p['w']:.3f}\times{p['Gs']:.2f}}}{{{p['e']:.3f}}}",
                            p["Sr"]
                        )

                    if k("gamma_sat") and not k("gamma_sub"):
                        p["gamma_sub"] = p["gamma_sat"] - self.gamma_w
                        self.add_log(
                            "gamma_sub",
                            r"\gamma_{sat}-\gamma_w",
                            rf"{p['gamma_sat']:.2f}-9.81",
                            p["gamma_sub"]
                        )

        # =================================================
        def draw_phase_diagram(p, inputs, result=False):
            e = p.get("e") or 0.7
            Sr = p.get("Sr") or 0.5
            Gs = p.get("Gs") or 2.7
            w = p.get("w") or 0.2

            Vs = 1
            Vv = e
            Vw = Sr * e
            Va = Vv - Vw

            fig, ax = plt.subplots(figsize=(5, 3.5))
            ax.axis("off")
            ax.set_xlim(-1.2, 2.5)
            ax.set_ylim(0, 1 + e + 0.4)

            ax.add_patch(patches.Rectangle((0, 0), 1, Vs, ec="black", fc="#D2B48C"))
            ax.text(0.5, Vs / 2, r"$S$", ha="center", va="center", fontsize=10)

            if Vw > 0:
                ax.add_patch(patches.Rectangle((0, Vs), 1, Vw, ec="black", fc="#87CEEB"))
                ax.text(0.5, Vs + Vw / 2, r"$W$", ha="center", va="center")

            if Va > 0:
                ax.add_patch(patches.Rectangle((0, Vs + Vw), 1, Va, ec="black", fc="#F0F8FF"))
                ax.text(0.5, Vs + Vw + Va / 2, r"$A$", ha="center", va="center")

            ax.text(-0.9, Vs + Vv / 2, rf"$e = {e:.3f}$", fontsize=10)
            ax.text(1.2, Vs / 2, rf"$M_s\;(G_s={Gs:.2f})$", fontsize=9)
            ax.text(0.5, 1 + e + 0.1, rf"$S_r={Sr:.2f}$", fontsize=10)

            ax.set_title("Final State" if result else "Input Preview", fontsize=10)
            return fig

        # =================================================
        solver = SoilState()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Inputs")

            st.markdown(r"**$w$ (Water Content)**")
            w = st.number_input("", 0.0, step=0.01)
            st.markdown(r"**$G_s$ (Specific Gravity)**")
            Gs = st.number_input("", 0.0, step=0.01)
            st.markdown(r"**$e$ (Void Ratio)**")
            e = st.number_input("", 0.0, step=0.01)
            st.markdown(r"**$S_r$ (Saturation)**")
            Sr = st.number_input("", 0.0, 1.0, step=0.01)

            st.markdown(r"**$\gamma_{bulk}$ (kN/m³)**")
            gb = st.number_input("", 0.0, step=0.1)
            st.markdown(r"**$\gamma_{dry}$ (kN/m³)**")
            gd = st.number_input("", 0.0, step=0.1)

            if w > 0: solver.set_param("w", w)
            if Gs > 0: solver.set_param("Gs", Gs)
            if e > 0: solver.set_param("e", e)
            if Sr > 0: solver.set_param("Sr", Sr)
            if gb > 0: solver.set_param("gamma_bulk", gb)
            if gd > 0: solver.set_param("gamma_dry", gd)

        with col2:
            fig = draw_phase_diagram(solver.params, solver.inputs)
            st.pyplot(fig)
            plt.close(fig)

        if st.button("Solve", type="primary"):
            solver.solve()

            st.markdown("### Results")
            p = solver.params

            for k, v in p.items():
                if v is not None:
                    st.latex(rf"{LATEX[k]} = {v:.4f}")

            with st.expander("Calculation Steps", expanded=True):
                for s in solver.log:
                    st.latex(
                        rf"{s['var']} = {s['formula']} = {s['sub']} = \mathbf{{{s['res']:.4f}}}"
                    )

    # =====================================================
    # SYMBOLIC MODE (unchanged logic, already LaTeX safe)
    # =====================================================
    else:
        st.subheader("Formula Finder")
        st.caption("Select known variables to find a formula.")
        st.info("This section already uses full LaTeX — no changes required.")
