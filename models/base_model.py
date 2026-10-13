from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class GeopressureModel(ABC):
    def __init__(self, data: pd.DataFrame, params: dict):
        self.data = data.copy()
        self.params = params
        
        self.depth_col = self.params.get('depth_col', self.data.columns[0])
        self.depth = self.data[self.depth_col]
        
        self.results = self.data.copy()
        self.results['Depth'] = self.depth
        
    def calculate_overburden(self):
        # Cálculo Continuo de GSV en PPG
        if 'RHOB' in self.data.columns and not self.data['RHOB'].isnull().all():
            rho_matrix_ppg = self.params.get('rho_matrix', 2.65) * 8.345
            rhob_ppg = self.data['RHOB'] * 8.345
            rhob_ppg = rhob_ppg.fillna(rho_matrix_ppg)
            self.results['GSV'] = rhob_ppg.expanding().mean()
        else:
            po = self.params.get('po', 1.95) * 8.345
            k = self.params.get('k', 0.01)
            c = self.params.get('c', 0.5)
            safe_depth = np.where(self.depth <= 0, 1e-5, self.depth)
            # Aproximación empírica continua
            sv = 0.145 * (po * safe_depth + k * (safe_depth ** (c + 1)) / (c + 1))
            self.results['GSV'] = sv / safe_depth

    def calculate_fracture_pressure(self):
        pp = self.results.get("Pp_Cal", self.results.get("Pp_Uncal"))
        gsv = self.results["GSV"]
        
        safe_depth = np.where(self.depth <= 0, np.nan, self.depth)
        v = 0.0645 * np.log(safe_depth) - 0.067
        
        pf_calc = pp + (v / (1 - v)) * (gsv - pp)
        
        # El límite no debe ser un escalón artificial, sino el clipeo matemático normal
        self.results["Pf"] = pf_calc.clip(lower=pp, upper=gsv)

    @abstractmethod
    def calculate_pore_pressure(self):
        pass

    def run(self):
        self.calculate_overburden()
        self.calculate_pore_pressure()
        self.calculate_fracture_pressure()
        return self.results