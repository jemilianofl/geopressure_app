import numpy as np
import pandas as pd
from .base_model import GeopressureModel

class BowersModel(GeopressureModel):
    def calculate_pore_pressure(self):
        gsv = self.results['GSV']
        depth = self.results['Depth']
        
        # Parámetros de Bowers (Curva Virgen)
        v_ml = self.params.get('bowers_vml', 5000.0) # Velocidad sónica en el lecho marino (ft/s)
        a = self.params.get('bowers_a', 15.0)        # Parámetro de calibración A
        b = self.params.get('bowers_b', 0.75)        # Parámetro de calibración B
        
        if self.params['curve_type'] == 'Sonic':
            dt = self.results.get('DT', self.results.get('DTC'))
            
            # 1. Convertir Tiempo de Tránsito (us/ft) a Velocidad (ft/s)
            # Vp = 1,000,000 / DT
            v = 1000000.0 / dt
            self.results['Vp'] = v
            
            # 2. Calcular el Esfuerzo Efectivo (Sigma_e) en PSI
            # V = V_ml + A * (Sigma_e)^B => Sigma_e = ((V - V_ml) / A)^(1/B)
            v_diff = np.maximum(v - v_ml, 1e-5) # Evitar bases negativas
            sigma_e_psi = (v_diff / a) ** (1.0 / b)
            
            # 3. Convertir Esfuerzo Efectivo de PSI a Gradiente PPG
            # PPG = PSI / (0.052 * TVD)
            safe_depth = np.maximum(depth, 1.0)
            sigma_e_ppg = sigma_e_psi / (0.052 * safe_depth)
            
            # 4. Presión de Poro = GSV - Sigma_e
            pp_uncal = gsv - sigma_e_ppg
            
            # Aplicar límites físicos: La Pp no puede ser menor a la hidrostática (aprox 8.5) ni mayor a la sobrecarga
            self.results['Pp_Uncal'] = pp_uncal.clip(lower=8.5, upper=gsv)
            self.results['Pp_Cal'] = self.results['Pp_Uncal']
            
        else:
            # Fallback en caso de que intenten usar resistividad con Bowers (Bowers clásico es sónico)
            self.results['Pp_Uncal'] = gsv * 0.465 
            self.results['Pp_Cal'] = self.results['Pp_Uncal']