import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ==========================================================
# MATERIAL MODEL
# ==========================================================
class Material:
    def __init__(self, fck, fyk):
        self.fck = fck
        self.fyk = fyk
        self.Es = 200000  # MPa
        self.ecu = 0.003

        # TS500 beta1 equivalent
        if fck <= 25:
            self.k_1 = 0.85
        elif fck == 30:
            self.k_1 = 0.82
        elif fck == 35:
            self.k_1 = 0.79
        elif fck == 40:
            self.k_1 = 0.76
        elif fck == 45:
            self.k_1 = 0.73
        elif fck >= 50:
            self.k_1 = 0.70

# ==========================================================
# SECTION GEOMETRY
# ==========================================================
class SectionGeometry:
    def __init__(self, b, h, cover, bar_dia):
        self.b = b
        self.h = h
        self.cover = cover
        self.bar_dia = bar_dia
        self.d = h - cover  # effective depth

# ==========================================================
# FLEXURE SOLVER
# ==========================================================
class FlexureSolver:
    def __init__(self, section, material, As):
        self.sec = section
        self.mat = material
        self.As = As

    # --------------------------------------
    # Neutral Axis
    # --------------------------------------
    def neutral_axis(self):
        c = (self.As * self.mat.fyk) / (0.85 * self.mat.fck * self.sec.b * self.mat.k_1)
        return c

    # --------------------------------------
    # Steel Strain & Stress
    # --------------------------------------
    def steel_strain_stress(self, c):
        eps_s = self.mat.ecu * (self.sec.d - c) / c
        fs = min(self.mat.Es * eps_s, self.mat.fyk)
        return eps_s, fs

    # --------------------------------------
    # Moment Capacity
    # --------------------------------------
    def moment_capacity(self, c, fs):
        a = self.mat.k_1 * c
        z = self.sec.d - a / 2
        Mn = self.As * fs * z / 1e6  # kNm
        return Mn, a, z

    # --------------------------------------
    # Balanced Neutral Axis
    # --------------------------------------
    def balanced_neutral_axis(self):
        eps_y = self.mat.fyk / self.mat.Es
        c_bal = self.sec.d * self.mat.ecu / (self.mat.ecu + eps_y)
        return c_bal

    # --------------------------------------
    # Internal Forces
    # --------------------------------------
    def internal_forces(self, c, fs):
        a = self.mat.k_1 * c
        T = self.As * fs
        C = 0.85 * self.mat.fck * self.sec.b * a
        return T, C

    # --------------------------------------
    # Reinforcement Ratio
    # --------------------------------------
    def reinforcement_ratio(self):
        rho = self.As / (self.sec.b * self.sec.d)
        return rho

    # --------------------------------------
    # Failure Mode
    # --------------------------------------
    def failure_mode(self, eps_s):
        eps_y = self.mat.fyk / self.mat.Es
        if eps_s > eps_y:
            return "Tension Controlled (Ductile)"
        elif abs(eps_s - eps_y) < 1e-4:
            return "Balanced Failure"
        else:
            return "Compression Controlled (Brittle)"

# ==========================================================
# INPUTS AND DIAGRAM
# ==========================================================
def render_inputs_and_diagram(goal_id):
    data = {}

    st.subheader("Geometry & Material Inputs")
    col1, col2 = st.columns([1,1])

    with col1:
        data["b"] = st.number_input("Width b [mm]", 100.0, value=300.0)
        data["h"] = st.number_input("Height h [mm]", 200.0, value=500.0)
        data["cover"] = st.number_input("Clear Cover [mm]", value=30.0)
        data["bar_dia"] = st.number_input("Bar Diameter [mm]", value=16.0)

        data["fck"] = st.number_input("Concrete Class fck [MPa]", min_value=16, max_value=50, value=30, step=1)
        data["fyk"] = st.selectbox("Steel Grade fyk [MPa]", [220, 420, 500], index=1)

        # Goal dependent inputs
        if goal_id in ["moment_capacity", "neutral_axis", "internal_forces", "reinforcement_ratio", "failure_mode"]:
            data["As"] = st.number_input("Steel Area As [mm²]", value=1257.0)
        elif goal_id in ["preliminary_section_sizing"]:
            data["Md"] = st.number_input("Design Moment Md [kNm]", value=250.0)
            data["rho_target"] = st.slider("Assumed Reinforcement Ratio ρ", 0.005, 0.02, 0.01)

    # --------------------------
    # Dynamic Diagram
    # --------------------------
    with col2:
        fig, ax = plt.subplots(figsize=(4,4))
        ax.add_patch(plt.Rectangle((0,0), data.get("b",300), data.get("h",500),
                                   edgecolor='black', facecolor='lightgray'))
        # Steel bars
        As_num = int(data.get("As", 1257)/100)  # arbitrary scaling for visualization
        bar_y = data.get("cover",30) + 10
        for i in range(As_num):
            ax.add_patch(plt.Circle((data.get("cover",30)+i*20, bar_y), radius=data.get("bar_dia",16)/2, color='red'))
        ax.set_xlim(0, data.get("b",300))
        ax.set_ylim(0, data.get("h",500))
        ax.set_aspect('equal')
        ax.set_title("Cross Section Diagram")
        ax.axis('off')
        st.pyplot(fig)

    return data

# ==========================================================
# RESULTS DISPLAY
# ==========================================================
def display_results(goal_id, solver, c=None, fs=None):
    st.subheader("Results")

    if goal_id == "neutral_axis":
        st.latex(f"c = {c:.2f} mm")
        st.latex(f"εs = {solver.steel_strain_stress(c)[0]:.5f}")
        st.latex(f"fs = {solver.steel_strain_stress(c)[1]:.2f} MPa")

    elif goal_id == "moment_capacity":
        Mn, a, z = solver.moment_capacity(c, fs)
        st.latex(f"M_n = {Mn:.2f} kNm")
        st.latex(f"a = {a:.2f} mm")
        st.latex(f"z = {z:.2f} mm")

    elif goal_id == "balanced_na":
        c_bal = solver.balanced_neutral_axis()
        st.latex(f"Balanced Neutral Axis c_bal = {c_bal:.2f} mm")

    elif goal_id == "internal_forces":
        T, C = solver.internal_forces(c, fs)
        st.latex(f"Tension Force T = {T:.2f} N")
        st.latex(f"Compression Force C = {C:.2f} N")

    elif goal_id == "reinforcement_ratio":
        rho = solver.reinforcement_ratio()
        st.latex(f"Reinforcement Ratio ρ = {rho:.5f}")

    elif goal_id == "failure_mode":
        eps_s, _ = solver.steel_strain_stress(c)
        mode = solver.failure_mode(eps_s)
        st.latex(f"Failure Mode: {mode}")

    elif goal_id == "preliminary_section_sizing":
        st.info("Preliminary section sizing feature not fully implemented yet.")


# ==========================================================
# GOALS
# ==========================================================
GOAL_OPTIONS = {
    "Find Moment Capacity": "moment_capacity",
    "Find Neutral Axis & Strain": "neutral_axis",
    "Design Steel Area": "design_As",
    "Find Balanced Neutral Axis": "balanced_na",
    "Compute Internal Forces": "internal_forces",
    "Compute Reinforcement Ratio": "reinforcement_ratio",
    "Check Failure Mode": "failure_mode",
    "Preliminary Section Sizing": "preliminary_section_sizing"
}

# ==========================================================
# MAIN APP
# ==========================================================
def app():
    st.title("TS500 Flexure Solver")

    goal_label = st.selectbox("Select Calculation Goal", list(GOAL_OPTIONS.keys()))
    goal_id = GOAL_OPTIONS[goal_label]

    # Inputs + diagram
    inputs = render_inputs_and_diagram(goal_id)

    if st.button("Solve"):
        sec = SectionGeometry(inputs["b"], inputs["h"], inputs["cover"], inputs["bar_dia"])
        mat = Material(inputs["fck"], inputs["fyk"])

        if goal_id in ["moment_capacity", "neutral_axis", "internal_forces",
                       "reinforcement_ratio", "failure_mode", "balanced_na"]:
            solver = FlexureSolver(sec, mat, inputs["As"])
            c = solver.neutral_axis()
            eps_s, fs = solver.steel_strain_stress(c)
            display_results(goal_id, solver, c, fs)
        elif goal_id == "design_As":
            st.info("Design Steel Area feature not fully implemented yet.")
        elif goal_id == "preliminary_section_sizing":
            st.info("Preliminary Section Sizing feature not fully implemented yet.")

# ==========================================================
# RUN
# ==========================================================
if __name__ == "__main__":
    app()
