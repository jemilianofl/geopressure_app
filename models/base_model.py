from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class GeopressureModel(ABC):
    def __init__(self, data: pd.DataFrame, params: dict):
        self.data = data.copy()
        self.params = params
        
        # Selección dinámica de profundidad (TVD o MD)
        self.depth_col = self.params.get('depth_col', self.data.columns[0])
        self.depth = self.data[self.depth_col]
        
        self.results = self.data.copy()
        self.results['Depth'] = self.depth
        
    def calculate_overburden(self):
        if 'RHOB' in self.data.columns and not self.data['RHOB'].isnull().all():
            rho_matrix = self.params.get('rho_matrix', 2.65)
            rhob = self.data['RHOB'].fillna(rho_matrix)
            self.results['GSV'] = rhob.expanding().mean() 
        else:
            po = self.params.get('po', 1.95)
            k = self.params.get('k', 0.01)
            c = self.params.get('c', 0.5)
            sv = 0.145 * (po * 9.81 * self.depth + k * 9.81 * (self.depth ** (c + 1)) / (c + 1))
            self.results['SV'] = sv
            self.results['GSV'] = sv / (self.depth * 1.422)

    def calculate_fracture_pressure(self):
        pp = self.results.get("Pp_Cal", self.results.get("Pp_Uncal"))
        gsv = self.results["GSV"]
        
        safe_depth = np.where(self.depth <= 0, np.nan, self.depth)
        v = 0.0645 * np.log(safe_depth) - 0.067
        self.results["Pf"] = pp + (v / (1 - v)) * (gsv - pp)

    @abstractmethod
    def calculate_pore_pressure(self):
        pass

    def run(self):
        self.calculate_overburden()
        self.calculate_pore_pressure()
        self.calculate_fracture_pressure()
        return self.results