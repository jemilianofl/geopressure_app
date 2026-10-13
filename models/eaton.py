import numpy as np
import pandas as pd
from .base_model import GeopressureModel

class EatonModel(GeopressureModel):
    def calculate_pore_pressure(self):
        gsv = self.results['GSV']
        depth = self.results['Depth']
        
        # Crear series con los parámetros por defecto
        ppn_array = pd.Series(self.params.get('ppn_default', 1.03), index=depth.index)
        exp_array = pd.Series(self.params.get('eaton_exp_default', 3.0), index=depth.index)
        
        # Aplicar los parámetros zonificados si el usuario los definió
        for zone in self.params.get('params_zones', []):
            mask = (depth >= zone['start']) & (depth <= zone['end'])
            ppn_array[mask] = zone.get('ppn', 1.03)
            exp_array[mask] = zone.get('eaton_exp', 3.0)
        
        if self.params['curve_type'] == 'Sonic':
            dt = self.results.get('DT', self.results.get('DTC'))
            dtn = self.params['dtn_trend']
            self.results['Pp_Uncal'] = gsv - (gsv - ppn_array) * ((dtn / dt) ** exp_array)
            
        elif self.params['curve_type'] == 'Resistivity':
            rt = self.results['RT']
            rtn = self.params['rtn_trend']
            self.results['Pp_Uncal'] = gsv - (gsv - ppn_array) * ((rt / rtn) ** exp_array)
            
        self.results['Pp_Cal'] = self.results['Pp_Uncal']