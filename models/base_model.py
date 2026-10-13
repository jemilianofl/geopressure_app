from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class GeopressureModel(ABC):
    def __init__(self, data: pd.DataFrame, params: dict):
        self.data = data.copy()
        self.params = params
        
        # Selección dinámica de profundidad
        self.depth_col = self.params.get('depth_col', self.data.columns[0])
        self.depth = self.data[self.depth_col]
        
        self.results = self.data.copy()
        self.results['Depth'] = self.depth
        
    def calculate_overburden(self):
        # Tirante de agua (WD) + Air Gap (RKB)
        wd = self.params.get('wd', 138.0)
        rkb = self.params.get('rkb', 101.0)
        water_depth = wd + rkb
        
        # Cálculo de GSV en PPG (Sistema Inglés)
        if 'RHOB' in self.data.columns and not self.data['RHOB'].isnull().all():
            # Factor conversión: g/cm3 a ppg = 8.345
            rho_matrix_ppg = self.params.get('rho_matrix', 2.65) * 8.345
            water_rho_ppg = 8.5 # Agua de mar
            
            rhob_ppg = self.data['RHOB'] * 8.345
            rhob_ppg = rhob_ppg.fillna(rho_matrix_ppg)
            
            # Integración básica para GSV en ppg
            self.results['GSV'] = rhob_ppg.expanding().mean()
        else:
            # Fórmula empírica si no hay RHOB (aproximación en ppg)
            po = self.params.get('po', 1.95) * 8.345
            k = self.params.get('k', 0.01)
            c = self.params.get('c', 0.5)
            # Aproximación gruesa, es preferible la curva RHOB
            sv = 0.145 * (po * self.depth + k * (self.depth ** (c + 1)) / (c + 1))
            self.results['GSV'] = sv / self.depth

    def calculate_fracture_pressure(self):
        # Mathews & Kelly modificado
        pp = self.results.get("Pp_Cal", self.results.get("Pp_Uncal"))
        gsv = self.results["GSV"]
        
        safe_depth = np.where(self.depth <= 0, np.nan, self.depth)
        v = 0.0645 * np.log(safe_depth) - 0.067
        self.results["Pf"] = pp + (v / (1 - v)) * (gsv - pp)

    @abstractmethod
    def calculate_pore_pressure(self):
        pass
    
    def calculate_fracture_pressure(self):
        # Mathews & Kelly modificado
        pp = self.results.get("Pp_Cal", self.results.get("Pp_Uncal"))
        gsv = self.results["GSV"]
        
        # CORRECCIÓN: Evitar RuntimeWarning: invalid value encountered in log
        # Forzar valores <= 0 a ser NaN antes de sacar logaritmo
        safe_depth = np.where(self.depth <= 0, np.nan, self.depth)
        v = 0.0645 * np.log(safe_depth) - 0.067
        self.results["Pf"] = pp + (v / (1 - v)) * (gsv - pp)

    def run(self):
        self.calculate_overburden()
        self.calculate_pore_pressure()
        self.calculate_fracture_pressure()
        return self.results