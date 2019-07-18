import numpy as np
import pyares as pa


def calc_add(data):
    return str(data+100)


def addcols(x,y):
    return str(x+y)


# for now only string types can be returned, this will change in the future
def encodethings(x,y):
    if (x >= 30):
        return '1'
    elif (x < 30 and y >=83):
        return '2'
    else:
        return '0'


# spark can deal with lambdas extremely well
add_udf = lambda x: '1' if x >=30 else '0'

#encode_udf = lambda x,y:

#encodethings = lambda x, y: '1' if x>=30 elif y
#function_dict = {'add10_sa': (add10, ['sa']), 'add10_sx': (add10, ['sx']), 'addcols_sxsy': (addcols, ['sx', 'sy'])}
function_dict = {'encode_sa': (add_udf, ['sa']),
                 'add100_sa': (calc_add,['sa']),
                 'addcols_sasx': (addcols, ['sa', 'sx']),
                 'encode_sasx': (encodethings, ['sx','sy'])
                 }

aj = pa.init_aresjob()
result = aj.define_job(function_dict=function_dict, persist_search=False)
