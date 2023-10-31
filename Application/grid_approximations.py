
# T. J. Overbye, T. R. Hutchins, K. Shetye, J. Weber and S. Dahman, 
# "Integration of geomagnetic disturbance modeling into the power flow: A methodology for large-scale system studies," 
# 2012 North American Power Symposium (NAPS), Champaign, IL, USA, 2012, pp. 1-7, doi: 10.1109/NAPS.2012.6336365.

""" Rpu/Rbasehighside = Rhighside + at^2 * Rlowside""" # for regular transformer

""" Rpu/Rbasehighside = Rseries + (at - 1)^2 * Rcommon""" # for auto transformer

def estimate_winding_impedance(Rpu: float, R_base_high_side: float, at: float, is_auto: bool) -> [float, float]:
    """ This function estimates the winding resistance for an auto transformer and a standard transformer as described in
            T. J. Overbye, T. R. Hutchins, K. Shetye, J. Weber and S. Dahman, "Integration of geomagnetic disturbance 
                modeling into the power flow: A methodology for large-scale system studies," 2012 North American Power 
                Symposium (NAPS), Champaign, IL, USA, 2012, pp. 1-7, doi: 10.1109/NAPS.2012.6336365.

        @param Rpu: per unit resistance from the transformer equivalent circuit
        @param R_base_high_side: per unit base of the resistance
        @param at: turns ratio of the transformer. This can be calculated as XFNomkVbaseFrom/XFNomkVbaseTo if this is less than one, invert it.
        @param is_auto: boolean to perform calculation for auto or standard

        return: R_high_side, R_low_side: high side and low side resistance if standard
        return: R_series, R_common: series and common resistance if it is an auto transformer
    """
    lhs = Rpu / R_base_high_side

    if is_auto:
        R_series = lhs/2

        R_common = (lhs/2) / ((at - 1)**2)
        return R_series, R_common
    
    else:
        R_high_side = lhs/2

        R_low_side = (lhs/2) / (at**2)

        return R_high_side, R_low_side
    

def get_grounding_resistance(subNomKv: float) -> float:
    """ This method provides a ballpark estimate of the substation grounding resistance as in
            T. J. Overbye, T. R. Hutchins, K. Shetye, J. Weber and S. Dahman, "Integration of geomagnetic disturbance 
                modeling into the power flow: A methodology for large-scale system studies," 2012 North American Power 
                Symposium (NAPS), Champaign, IL, USA, 2012, pp. 1-7, doi: 10.1109/NAPS.2012.6336365.

        @param: subNomKv the nominal voltage of the highest voltage in the substation.
        return: "Ballpark" estimate of the grounding resistance
    """
    if subNomKv >= 230.0:
        return 0.64
    return 1.57