import numpy as np
import pyares as pa


def calc_add(data):
    return np.add(data, 100)


function_dict = {'add100_sx': (calc_add, ['sx']),
                 'add100_sa': (calc_add, ['sa'])}

aj = pa.init_aresjob()
result = aj.define_job(function_dict=function_dict, persist_search=False)
