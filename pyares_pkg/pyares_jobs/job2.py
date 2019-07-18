import numpy as np
import pyares as pa


def calc_add(data):
    return np.add(data, 100)


function_dict = {'addmore_sx': (calc_add, ['add100_sx']),
                 'addmore_sa': (calc_add, ['add100_sa'])}

aj = pa.init_aresjob()
#result = aj.define_job(function_dict=function_dict, perform_search=False, persist_search=False, previous_results=)
