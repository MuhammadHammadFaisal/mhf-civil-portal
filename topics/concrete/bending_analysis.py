import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# ==========================================================
# MATERIAL MODEL
# ==========================================================
class Material:
    def __init__(self, fck, fyk):
        self.fck = fck
        self.fyk = fyk

        self.Es = 200000  # MPa
        self.ecu = 0.003

        if fck <= 25:
            self.k_1 = 0.85
        elif fck <= 30:
            self.k_1 = 0.82
        elif fck <= 35:
            self.k_1 = 0.79
        elif fck <= 40:
            self.k_1 = 0.76
        elif fck <= 45:
            self.k_1 = 0.73
        else:
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

        # Effective depth
        self.d = h - cover - bar_dia / 2


# ==========================================================
# FLEXURE SOLVER
# ==========================================================
class FlexureSolver:
    def __init__(self, section, material, As):
        self.sec = section
        self.mat = material
        self.As = As

    def neutral_axis(self):
        fy = self.mat.fyk
        fc = self.mat.fck
        b = self.sec.b
        k1 = self.mat.k_1
        As = self.As

        c = (As * fy) / (0.85 * fc * b * k1)
        return c

    def steel_strain_stress(self, c):

        ecu = self.mat.ecu
        Es = self.mat.Es
        fy = self.mat.fyk
        d = self.sec.d

        eps_s = ecu * (d - c) / c
        fs = min(Es * eps_s, fy)

        return eps_s, fs

    def moment_capacity(self, c, fs):

        b = self.sec.b
        k1 = self.mat.k_1
        As = self.As
        d = self.sec.d

        a = k1 * c
        z = d - a / 2

        Mn = As * fs * z * 1e-6  # kNm
        return Mn, a, z


# ==========================================================
# CROSS SECTION DIAGRAM
# ==========================================================
def draw_section(b, h, cover, bar_dia):

    fig, ax = plt.subplots()

    # Concrete rectangle
    rect = patches.Rectangle((0, 0), b, h, fill=False, linewidth=2)
    ax.add_patch(rect)

    # Steel bar (single layer bottom)
    bar_y = cover + bar_dia / 2
    bar_x = b / 2

    steel = patches.Circle((bar_x, bar_y), bar_dia / 2, fill=False, linewidth=2)
    ax.add_patch(steel)

    # Effective depth line
    d = h - cover - bar_dia / 2
    ax.plot([0, b], [d, d], linestyle="--")

    ax.set_aspect('equal')
    ax.set_xlim(-50, b + 50)
    ax.set_ylim(-50, h + 50)

    ax.set_title("RC Cross Section")

    ax.set_xlabel("Width (mm)")
    ax.set_ylabel("Depth (mm)")

    return fig


# ==========================================================
# INPUT MANAGER + DIAGRAM
# ==========================================================
def render_inputs(goal_id):

    data = {}

    left, right = st.columns([1, 1])

    # ---------------- INPUT SIDE ----------------
    with left:

        st.subheader("1. Geometry")

        data["b"] = st.number_input("Width b [mm]", min_value=100.0, value=300.0)
        data["h"] = st.number_input("Height h [mm]", min_value=200.0, value=500.0)
        data["cover"] = st.number_input("Cover [mm]", min_value=20.0, value=30.0)
        data["bar_dia"] = st.number_input("Bar Diameter [mm]", min_value=8.0, value=16.0)

        st.subheader("2. Material")

        data["fck"] = st.number_input(
            "Concrete Class (MPa)",
            min_value=16,
            max_value=50,
            value=20,
            step=1
        )

        data["fyk"] = st.selectbox("Steel Grade (MPa)", [220, 420, 500], index=1)

        st.subheader("3. Problem Variables")

        if goal_id in ["moment_capacity", "neutral_axis"]:
            data["As"] = st.number_input("Steel Area As [mm²]", value=1257.0)

        elif goal_id == "design_As":
            data["Md"] = st.number_input("Design Moment Md [kNm]", value=250.0)

    # ---------------- DIAGRAM SIDE ----------------
    with right:
        st.subheader("Section Diagram")

        fig = draw_section(
            data["b"],
            data["h"],
            data["cover"],
            data["bar_dia"]
        )

        st.pyplot(fig)

    return data


# ==========================================================
# RESULT DISPLAY
# ==========================================================
def display_results(goal_id, results):

    st.subheader("Results")

    if goal_id == "neutral_axis":

        st.latex(f"c = {results['c']:.2f} \\ mm")
        st.latex(f"\\varepsilon_s = {results['eps_s']:.5f}")
        st.latex(f"f_s = {results['fs']:.2f} \\ MPa")

    elif goal_id == "moment_capacity":

        st.latex(f"M_n = {results['Mn']:.2f} \\ kNm")
        st.latex(f"a = {results['a']:.2f} \\ mm")
        st.latex(f"z = {results['z']:.2f} \\ mm")


# ==========================================================
# GOAL OPTIONS
# ==========================================================
GOAL_OPTIONS = {
    "Find Moment Capacity (Mr)": "moment_capacity",
    "Find Neutral Axis & Strain": "neutral_axis",
    "Design Steel Area (As)": "design_As"
}


# ==========================================================
# MAIN APP
# ==========================================================
def app():

    st.title("TS500 Flexure Solver")

    goal_label = st.selectbox(
        "What needs to be calculated?",
        list(GOAL_OPTIONS.keys())
    )

    goal_id = GOAL_OPTIONS[goal_label]

    inputs = render_inputs(goal_id)

    if st.button("Solve", type="primary"):

        sec = SectionGeometry(
            inputs["b"],
            inputs["h"],
            inputs["cover"],
            inputs["bar_dia"]
        )

        mat = Material(inputs["fck"], inputs["fyk"])

        if goal_id in ["moment_capacity", "neutral_axis"]:

            solver = FlexureSolver(sec, mat, inputs["As"])

            c = solver.neutral_axis()
            eps_s, fs = solver.steel_strain_stress(c)

            results = {
                "c": c,
                "eps_s": eps_s,
                "fs": fs
            }

            if goal_id == "moment_capacity":
                Mn, a, z = solver.moment_capacity(c, fs)
                results.update({"Mn": Mn, "a": a, "z": z})

            display_results(goal_id, results)


# ==========================================================
# RUN APP
# ==========================================================
if __name__ == "__main__":
    app()
