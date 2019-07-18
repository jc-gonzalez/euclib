import numpy as np
import pyares as pa

# all solar aspect angles and all the timestamps.
# params = ['sa','sx','sy','sz']
# start = 1388534410697
# end = 1420070380120


def project_angles(param) -> float:
    return float(max(0, np.cos(np.radians(param))))


def project_angles_pi(param) -> float:
    return float(max(0, np.cos(np.radians(param)+np.pi)))


# this function is wrong, but something like this
def pen_umbra_factor(umbra, penumbra) -> float:
    if umbra == 1:
        return 0.0
    elif penumbra == 1:
        return 0.3
    else:
        return 1.0


function_dict = {'panels': (project_angles, ['sa'])}#,
                 #'front': (project_angles, ['sx']),
                 #'left': (project_angles, ['sy']),
                 #'up': (project_angles, ['sz']),
                 #'back': (project_angles_pi, ['sx']),
                 #'right': (project_angles_pi, ['sy']),
                 #'down': (project_angles_pi, ['sz'])
                 #}


aj = pa.init_aresjob()
aj.define_job(function_dict=function_dict,
              perform_search=True,
              persist_search=True,
              calc_stats=True,
              resolution='5m')
