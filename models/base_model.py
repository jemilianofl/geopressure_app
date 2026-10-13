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
        # Cálculo Continuo de GSV en PPG integrando la curva de Densidad
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
            sv = 0.145 * (po * safe_depth + k * (safe_depth ** (c + 1)) / (c + 1))
            self.results['GSV'] = sv / safe_depth

    def calculate_fracture_pressure(self):
        # Ecuación Poroelástica para Esfuerzo Horizontal Mínimo y Fractura
        pp = self.results.get("Pp_Cal", self.results.get("Pp_Uncal"))
        gsv = self.results["GSV"]
        
        # 1. Relación de Poisson (v)
        # Si la curva existe en el LAS (ej. POIS o PR), se usa; si no, se usa el valor del usuario o empírico
        pois_col = next((c for c in self.data.columns if c.upper() in ['POIS', 'PR']), None)
        if pois_col and not self.data[pois_col].isnull().all():
            v = self.data[pois_col]
        else:
            v_default = self.params.get('poisson_ratio', None)
            if v_default is not None:
                v = pd.Series(v_default, index=self.depth.index)
            else:
                safe_depth = np.where(self.depth <= 0, np.nan, self.depth)
                v = 0.0645 * np.log(safe_depth) - 0.067
                
        # 2. Coeficiente de Biot (alpha)
        alpha = self.params.get('biot_alpha', 1.0)
        
        # 3. Cálculo de Esfuerzo Horizontal Mínimo (Ecuación poroelástica)
        k_ratio = v / (1 - v)
        sh_calc = k_ratio * (gsv - (alpha * pp)) + (alpha * pp)
        
        # La presión de fractura (Pf) y el límite hidráulico usan la base de Sh
        # Se acota físicamente entre la presión de poro y la sobrecarga
        self.results["Pf"] = sh_calc.clip(lower=pp, upper=gsv)

    @abstractmethod
    def calculate_pore_pressure(self):
        pass

    def run(self):
        self.calculate_overburden()
        self.calculate_pore_pressure()
        self.calculate_fracture_pressure()
        return self.results