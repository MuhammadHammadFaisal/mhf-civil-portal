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
