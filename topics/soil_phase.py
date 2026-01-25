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
                    'gamma_sub': r'\gamma^\prime',
                    'na': r'n_a'
                }

            def set_param(self, key, value):
                if value is not None: self.params[key] = float(value)

            def add_log(self, target_key, formula_latex, sub_latex, result):
                symbol = self.latex_map.get(target_key, target_key)
                # Avoid duplicate logs
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
                    
                    # --- 1. BASIC RELATIONSHIPS (n <-> e) ---
                    if known('n') and not known('e'):
                        p['e'] = p['n'] / (1 - p['n'])
                        self.add_log('e', r'\frac{n}{1 - n}', r'Calc...', p['e'])
                        changed = True
                    if known('e') and not known('n'):
                        p['n'] = p['e'] / (1 + p['e'])
                        self.add_log('n', r'\frac{e}{1 + e}', r'Calc...', p['n'])
                        changed = True

                    # --- 2. THE "Se = wGs" TRIANGLE ---
                    # Solve for Sr
                    if known('w') and known('Gs') and known('e') and not known('Sr'):
                        p['Sr'] = (p['w'] * p['Gs']) / p['e']
                        self.add_log('Sr', r'\frac{w G_s}{e}', r'Calc...', p['Sr'])
                        changed = True
                    # Solve for e
                    if known('w') and known('Gs') and known('Sr') and not known('e') and p['Sr'] != 0:
                        p['e'] = (p['w'] * p['Gs']) / p['Sr']
                        self.add_log('e', r'\frac{w G_s}{S_r}', r'Calc...', p['e'])
                        changed = True
                    # Solve for w
                    if known('Sr') and known('e') and known('Gs') and not known('w'):
                        p['w'] = (p['Sr'] * p['e']) / p['Gs']
                        self.add_log('w', r'\frac{S_r e}{G_s}', r'Calc...', p['w'])
                        changed = True
                    # Solve for Gs
                    if known('Sr') and known('e') and known('w') and not known('Gs') and p['w'] != 0:
                        p['Gs'] = (p['Sr'] * p['e']) / p['w']
                        self.add_log('Gs', r'\frac{S_r e}{w}', r'Calc...', p['Gs'])
                        changed = True

                    # --- 3. UNIT WEIGHT FORWARD CALCULATIONS (Find Gamma) ---
                    # Gamma Dry
                    if known('Gs') and known('e') and not known('gamma_dry'):
                        p['gamma_dry'] = (p['Gs'] * self.gamma_w) / (1 + p['e'])
                        self.add_log('gamma_dry', r'\frac{G_s \gamma_w}{1 + e}', r'Calc...', p['gamma_dry'])
                        changed = True
                    # Gamma Bulk
                    if known('Gs') and known('e') and known('w') and not known('gamma_bulk'):
                        # Using w is often safer than Sr if Sr is derived
                        p['gamma_bulk'] = (p['Gs'] * self.gamma_w * (1 + p['w'])) / (1 + p['e'])
                        self.add_log('gamma_bulk', r'\frac{G_s \gamma_w (1+w)}{1+e}', r'Calc...', p['gamma_bulk'])
                        changed = True

                    # --- 4. [NEW] REVERSE CALCULATIONS (Find e from Gamma) ---
                    # Find e from Gamma Bulk (This is what fixed your bug!)
                    if known('gamma_bulk') and known('Gs') and known('w') and not known('e'):
                        # Derivation: gamma_bulk = Gs(1+w)gamma_w / (1+e)  ->  1+e = Gs(1+w)gamma_w / gamma_bulk
                        val = (p['Gs'] * (1 + p['w']) * self.gamma_w) / p['gamma_bulk']
                        p['e'] = val - 1
                        self.add_log('e', r'\frac{G_s(1+w)\gamma_w}{\gamma_{bulk}} - 1', r'Calc...', p['e'])
                        changed = True

                    # Find e from Gamma Dry
                    if known('gamma_dry') and known('Gs') and not known('e'):
                        # Derivation: gamma_dry = Gs*gamma_w / (1+e)
                        val = (p['Gs'] * self.gamma_w) / p['gamma_dry']
                        p['e'] = val - 1
                        self.add_log('e', r'\frac{G_s \gamma_w}{\gamma_{dry}} - 1', r'Calc...', p['e'])
                        changed = True

                    # --- 5. SATURATION & SUBMERGED CHECKS ---
                    if known('gamma_bulk') and p['Sr'] == 1.0 and not known('gamma_sat'):
                         p['gamma_sat'] = p['gamma_bulk']
                         
                    if known('gamma_bulk') and p['Sr'] == 1.0 and not known('gamma_sub'):
                        p['gamma_sub'] = p['gamma_bulk'] - self.gamma_w
                        self.add_log('gamma_sub', r'\gamma_{sat} - \gamma_w', r'Calc...', p['gamma_sub'])
                        changed = True

                    iterations += 1
