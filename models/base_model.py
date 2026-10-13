from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class GeopressureModel(ABC):
    def __init__(self, data: pd.DataFrame, params: dict):
        self.data = data
        self.params = params
        self.results = data.copy()
        # Asegurar que tenemos una columna de profundidad estándar
        self.depth = self.data.get('TVD', self.data.get('Depth', self.data.iloc[:, 0]))
        self.results['Depth'] = self.depth
        
    def calculate_overburden(self):
        # Si hay RHOB, calculamos integrando la densidad. Si no, usamos extrapolación empírica.
        if 'RHOB' in self.data.columns and not self.data['RHOB'].isnull().all():
            rhob = self.data['RHOB'].fillna(self.params.get('rho_matrix', 2.65))
            # Aproximación de integración (simplificada para el ejemplo)
            self.results['GSV'] = rhob.expanding().mean() 
        else:
            # Extrapolación empírica (Fórmula de tu script original)
            po = self.params.get('po', 1.95)
            k = self.params.get('k', 0.01)
            c = self.params.get('c', 0.5)
            
            # sv = 0.145 * (po * 9.81 * depth + k * 9.81 * (depth ** (c + 1)) / (c + 1))
            sv = 0.145 * (po * 9.81 * self.depth + k * 9.81 * (self.depth ** (c + 1)) / (c + 1))
            self.results['SV'] = sv
            self.results['GSV'] = sv / (self.depth * 1.422)

    def calculate_fracture_pressure(self):
        pp = self.results.get("Pp_Cal", self.results.get("Pp_Uncal"))
        gsv = self.results["GSV"]
        
        # Coeficiente v empírico
        v = 0.0645 * np.log(self.depth.replace(0, np.nan)) - 0.067
        self.results["Pf"] = pp + (v / (1 - v)) * (gsv - pp)

    @abstractmethod
    def calculate_pore_pressure(self):
        pass

    def run(self):
        self.calculate_overburden()
        self.calculate_pore_pressure()
        self.calculate_fracture_pressure()
        return self.results