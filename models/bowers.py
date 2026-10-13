import numpy as np
import pandas as pd
from .base_model import GeopressureModel

class BowersModel(GeopressureModel):
    def calculate_pore_pressure(self):
        gsv = self.results['GSV']
        depth = self.results['Depth']
        
        # Arrays para soportar zonificación geomecánica
        v_ml_array = pd.Series(self.params.get('bowers_vml', 5000.0), index=depth.index)
        a_array = pd.Series(self.params.get('bowers_a', 15.0), index=depth.index)
        b_array = pd.Series(self.params.get('bowers_b', 0.75), index=depth.index)
        
        # Aplicar zonificación si el usuario la definió en la tabla interactiva
        for zone in self.params.get('params_zones', []):
            mask = (depth >= zone['start']) & (depth <= zone['end'])
            if 'bowers_a' in zone: a_array[mask] = zone['bowers_a']
            if 'bowers_b' in zone: b_array[mask] = zone['bowers_b']
        
        if self.params['curve_type'] == 'Sonic':
            dt = self.results.get('DT', self.results.get('DTC'))
            
            v = 1000000.0 / dt
            self.results['Vp'] = v
            
            # Esfuerzo Efectivo
            v_diff = np.maximum(v - v_ml_array, 1e-5)
            sigma_e_psi = (v_diff / a_array) ** (1.0 / b_array)
            
            safe_depth = np.maximum(depth, 1.0)
            sigma_e_ppg = sigma_e_psi / (0.052 * safe_depth)
            
            pp_uncal = gsv - sigma_e_ppg
            
            # Límites físicos (Pp entre gradiente hidrostático normal y Sobrecarga)
            self.results['Pp_Uncal'] = pp_uncal.clip(lower=8.5, upper=gsv)
            self.results['Pp_Cal'] = self.results['Pp_Uncal']
            
        else:
            self.results['Pp_Uncal'] = gsv * 0.465 
            self.results['Pp_Cal'] = self.results['Pp_Uncal']