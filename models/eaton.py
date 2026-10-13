import numpy as np
import pandas as pd
from .base_model import GeopressureModel

class EatonModel(GeopressureModel):
    def calculate_pore_pressure(self):
        gsv = self.results['GSV']
        depth = self.results['Depth']
        
        # Parámetros base en PPG
        ppn_array = pd.Series(self.params.get('ppn_default', 8.60), index=depth.index)
        exp_array = pd.Series(self.params.get('eaton_exp_default', 3.0), index=depth.index)
        
        # Aplicar zonificación de Eaton si existe
        for zone in self.params.get('params_zones', []):
            mask = (depth >= zone['start']) & (depth <= zone['end'])
            ppn_array[mask] = zone.get('ppn', 8.60)
            exp_array[mask] = zone.get('eaton_exp', 3.0)
        
        if self.params['curve_type'] == 'Sonic':
            dt = self.results.get('DT', self.results.get('DTC'))
            
            # Tendencia Normal de Compactación Matemática (Exponencial)
            # DTn = DT_ml * e^(-c * Depth)
            dt_ml = self.params.get('dt_ml', 180.0)
            c_comp = self.params.get('c_compaction', 0.00015)
            dtn = dt_ml * np.exp(-c_comp * depth)
            self.results['DTN'] = dtn
            
            # EATON: Pp = GSV - (GSV - Ppn) * (DTn / DT)^3
            self.results['Pp_Uncal'] = gsv - (gsv - ppn_array) * ((dtn / dt) ** exp_array)
            
        elif self.params['curve_type'] == 'Resistivity':
            rt = self.results.get('RT', self.results.get('RES'))
            rt_ml = self.params.get('rt_ml', 1.0)
            c_comp = self.params.get('c_compaction_res', 0.0001)
            rtn = rt_ml * np.exp(c_comp * depth)
            self.results['RTN'] = rtn
            
            self.results['Pp_Uncal'] = gsv - (gsv - ppn_array) * ((rt / rtn) ** exp_array)
            
        # Calibración final
        self.results['Pp_Cal'] = self.results['Pp_Uncal']