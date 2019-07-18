import numpy as np
import pyares as pa

#import pyspark.sql.functions as F

# the udfs have to be numpy compatible operations,
# because the columns behave like numpy arrays
# functions need to be able to process element-wise




def calc_add(data):
    return np.add(data, 100)


def addcols(x,y):
    return x+y

# cannot convert column into bool, please use '&' for 'and', '|' for 'or', '~' for 'not' when building DataFrame boolean expressions
def encodethings(x,y):
    if (x>=30):
        return 1
    elif (x < 30) & (y >=86):
        return 2
    else:
        return 0
# because you cannot compare individual values of the column


# encode more is the compatible version of encode things
def encodemore(x,y):
    new = np.array([])

    new[np.where(x>=30)] = 1
    new[(x<30) & (y>=86)] = 2
    new[x<30]=0
    return x


def sin_calc(x):
    return np.sin(x)

def encodemore(x,y):
    return np.where(x>=30, 1, 2)



function_dict = {'add10_sa': (calc_add, ['sa']),
                 'add10_sx': (calc_add, ['sx']),
                 'addcols_sxsy': (addcols, ['sx', 'sy']),
                 'ecode_sxsy': (encodemore, ['sx', 'sy'])}


results_dict = {'application_1531834578612_0145': ['search']}

aj = pa.init_aresjob()
result = aj.define_job(function_dict=function_dict, perform_search=True)

results_dict = {'application_1531834578612_0145': ['search'],
                'application_1531834578612_0034': ['udf']}

aj = pa.init_aresjob()
result = aj.define_job(function_dict=function_dict, perform_search=False, calc_stats=True, previous_results=results_dict)

