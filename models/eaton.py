import numpy as np
from .base_model import GeopressureModel

class EatonModel(GeopressureModel):
    def calculate_pore_pressure(self):
        gsv = self.results['GSV']
        ppn = self.params.get('ppn', 1.03) # Presión hidrostática normal
        
        # Diferenciar si usa Sónico (DT) o Resistividad (RT)
        if self.params['curve_type'] == 'Sonic':
            dt = self.results['DT']
            dtn = self.params['dtn_trend'] # Tendencia normal precalculada (NCTL)
            exponent = self.params.get('eaton_exp_sonic', 3.0)
            
            # Pp = GSV - (GSV - Ppn) * (DTn / DT)^3
            self.results['Pp_Uncal'] = gsv - (gsv - ppn) * ((dtn / dt) ** exponent)
            
        elif self.params['curve_type'] == 'Resistivity':
            rt = self.results['RT']
            rtn = self.params['rtn_trend']
            exponent = self.params.get('eaton_exp_res', 1.2)
            
            # Pp = GSV - (GSV - Ppn) * (R / Rn)^1.2
            self.results['Pp_Uncal'] = gsv - (gsv - ppn) * ((rt / rtn) ** exponent)
            
        self.results['Pp_Cal'] = self.results['Pp_Uncal'] # Ajustar con calibración si aplica