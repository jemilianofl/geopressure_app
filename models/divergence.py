import numpy as np
import pandas as pd
from .base_model import GeopressureModel

class DivergenceModel(GeopressureModel):
    def calculate_pore_pressure(self):
        # Extraer parámetros de la UI
        dtco = self.params.get('dtco', 180)
        c1 = self.params.get('c1', -0.0004)
        z = self.params.get('ta', 3014) + self.params.get('rkb', 30.2)
        prf = self.params.get('prf', 3329)
        exp_eaton = self.params.get('exp_eaton', 0.5)
        ppn = self.params.get('ppn', 1.03)
        ms = self.params.get('ms', 1784)

        # Ubicar curva de tiempo de tránsito (puede llamarse DT o DTC)
        dt_curve = self.results.get('DT', self.results.get('DTC'))
        
        if dt_curve is None:
            raise ValueError("El modelo de divergencia requiere una curva de tiempo de tránsito (DT o DTC)")

        # DTC Promedio (Ventana móvil equivalente a tu iteración i+101)
        self.results['DTC_Prom'] = dt_curve.rolling(window=100, min_periods=1).mean()

        # Tendencia Normal de Compactación de Athy (DTN)
        self.results['DTN'] = dtco * np.exp(c1 * (self.depth - z))

        # Cálculo vectorizado del factor de divergencia (reemplaza tu for-loop)
        ratios = self.results['DTC_Prom'] / self.results['DTN']
        self.results['Div_DT_Ratio'] = ratios.cummax()

        self.results['Div_Factor'] = np.where(self.depth > prf, self.results['Div_DT_Ratio'], 1.0)
        self.results['DTSH'] = self.results['Div_Factor'] * self.results['DTN']

        # Presión de Poro no calibrada
        gsv = self.results['GSV']
        pp_div = gsv - (gsv - ppn) * ((self.results['DTN'] / self.results['DTSH']) ** exp_eaton)
        self.results['Pp_Uncal'] = pp_div

        # Calibración usando Mud Weight (si está en el archivo)
        mw = self.results.get('MW', pd.Series(np.nan, index=self.depth.index))
        self.results['Pp_Cal'] = np.where(
            self.depth < ms,
            self.results['Pp_Uncal'],
            mw.fillna(self.results['Pp_Uncal']) - 0.03
        )