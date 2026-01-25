# ==========================
    # MODE B: SYMBOLIC FINDER
    # ==========================
    elif "Symbolic" in mode:
        st.subheader("Formula Finder 🔍")
        st.caption("Select the variables you **KNOW** to find the formula for the variable you **WANT**.")

        col1, col2 = st.columns(2)
        
        with col1:
            # 1. What do they have?
            known_vars = st.multiselect(
                "I have these variables (Inputs):",
                options=[
                    "w (Water Content)", 
                    "Gs (Specific Gravity)", 
                    "e (Void Ratio)", 
                    "n (Porosity)", 
                    "Sr (Saturation)", 
                    "gamma_bulk (Bulk Unit Wt)", 
                    "gamma_dry (Dry Unit Wt)",
                    "gamma_sat (Saturated Unit Wt)"
                ],
                default=["Gs (Specific Gravity)", "e (Void Ratio)"] # Default example
            )
            
            # Clean up inputs to raw keys (e.g., "w (Water Content)" -> "w")
            cleaned_knowns = set([k.split(" ")[0] for k in known_vars])

        with col2:
            # 2. What do they want?
            target_var_raw = st.selectbox(
                "I want to find (Target):",
                options=[
                    "gamma_dry (Dry Unit Wt)",
                    "gamma_bulk (Bulk Unit Wt)",
                    "gamma_sat (Saturated Unit Wt)",
                    "gamma_sub (Submerged Unit Wt)",
                    "e (Void Ratio)",
                    "n (Porosity)",
                    "Sr (Saturation)",
                    "w (Water Content)"
                ]
            )
            target = target_var_raw.split(" ")[0]

        # --- FORMULA DATABASE ---
        # This dictionary maps 'Target' -> List of (Required Inputs, LaTeX Formula, Explanation)
        formulas = {
            'gamma_dry': [
                ({'Gs', 'e'}, r"\gamma_{dry} = \frac{G_s \gamma_w}{1 + e}", "Basic definition using Void Ratio."),
                ({'gamma_bulk', 'w'}, r"\gamma_{dry} = \frac{\gamma_{bulk}}{1 + w}", "Derived from Bulk Density and Water Content."),
                ({'Gs', 'n'}, r"\gamma_{dry} = G_s \gamma_w (1 - n)", "Using Porosity instead of Void Ratio.")
            ],
            'gamma_bulk': [
                ({'Gs', 'e', 'w'}, r"\gamma_{bulk} = \frac{G_s \gamma_w (1 + w)}{1 + e}", "The general relationship for unit weight."),
                ({'Gs', 'e', 'Sr'}, r"\gamma_{bulk} = \frac{(G_s + S_r e)\gamma_w}{1 + e}", "Using Saturation instead of Water Content.")
            ],
            'gamma_sat': [
                ({'Gs', 'e'}, r"\gamma_{sat} = \frac{(G_s + e)\gamma_w}{1 + e}", "Assumes Sr = 1 (Fully Saturated)."),
                ({'gamma_dry', 'n'}, r"\gamma_{sat} = \gamma_{dry} + n \gamma_w", "Relation between saturated and dry states.")
            ],
            'gamma_sub': [
                ({'gamma_sat'}, r"\gamma' = \gamma_{sat} - \gamma_w", "Archimedes' principle for submerged soil."),
                ({'Gs', 'e'}, r"\gamma' = \frac{(G_s - 1)\gamma_w}{1 + e}", "Standard submerged weight formula.")
            ],
            'e': [
                ({'n'}, r"e = \frac{n}{1 - n}", "Conversion from Porosity."),
                ({'w', 'Gs', 'Sr'}, r"e = \frac{w G_s}{S_r}", "From the fundamental relationship Se = wGs."),
                ({'gamma_dry', 'Gs'}, r"e = \frac{G_s \gamma_w}{\gamma_{dry}} - 1", "Back-calculated from Dry Unit Weight."),
                ({'gamma_sat', 'Gs'}, r"e = \frac{G_s \gamma_w - \gamma_{sat}}{\gamma_{sat} - \gamma_w}", "Back-calculated from Saturated Unit Weight.")
            ],
            'n': [
                ({'e'}, r"n = \frac{e}{1 + e}", "Conversion from Void Ratio."),
                ({'gamma_sat', 'gamma_dry'}, r"n = \frac{\gamma_{sat} - \gamma_{dry}}{\gamma_w}", "Difference between Sat and Dry states.")
            ],
            'Sr': [
                ({'w', 'Gs', 'e'}, r"S_r = \frac{w G_s}{e}", "Rearranged from Se = wGs.")
            ],
            'w': [
                ({'Sr', 'e', 'Gs'}, r"w = \frac{S_r e}{G_s}", "Rearranged from Se = wGs.")
            ]
        }

        # --- SEARCH LOGIC ---
        st.markdown("---")
        found_any = False
        
        if target in formulas:
            # Check every formula for this target
            for requirements, latex, description in formulas[target]:
                # If the user has ALL required variables (requirements is a subset of cleaned_knowns)
                if requirements.issubset(cleaned_knowns):
                    st.success(f"✅ **Formula Found:** {description}")
                    st.latex(latex)
                    found_any = True
        
        if not found_any:
            st.warning(f"No direct formula found for **{target}** with the variables you selected.")
            st.info("💡 **Tip:** Try adding more variables like **Gs**, **e**, or **w**.")
            
            # Hint: Show what IS needed
            if target in formulas:
                st.markdown("**To find this variable, you typically need combinations like:**")
                for reqs, _, _ in formulas[target]:
                    pretty_reqs = ", ".join(list(reqs))
                    st.markdown(f"- {pretty_reqs}")
