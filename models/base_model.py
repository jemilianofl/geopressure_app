from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class GeopressureModel(ABC):
    def __init__(self, data: pd.DataFrame, params: dict):
        self.data = data
        self.params = params
        self.results = data.copy()
        
    def calculate_overburden(self):
        # Utilizar RHOB del LAS si existe, sino extrapolar
        if 'RHOB' in self.data.columns:
            # Integración de la densidad para GSV usando TVD o Depth
            depth = self.data.get('TVD', self.data['Depth'])
            rhob = self.data['RHOB'].fillna(self.params.get('rho_matrix', 2.65))
            # Cálculo simplificado de integración (debe ajustarse con dt/dz exacto)
            self.results['GSV'] = rhob.expanding().mean() 
        else:
            # Extrapolación empírica (ej. Amoco/Trougott)
            pass

    def calculate_fracture_pressure(self):
        # Método de Matthews & Kelly o Eaton para fractura
        depth = self.results["Depth"]
        pp = self.results.get("Pp_Cal", self.results.get("Pp_Uncal"))
        gsv = self.results["GSV"]
        
        # Coeficiente de Poisson / Relación de esfuerzos (v)
        v = 0.0645 * np.log(depth) - 0.067
        self.results["Pf"] = pp + (v / (1 - v)) * (gsv - pp)

    @abstractmethod
    def calculate_pore_pressure(self):
        pass

    def run(self):
        self.calculate_overburden()
        self.calculate_pore_pressure()
        self.calculate_fracture_pressure()
        return self.results