"""
First edition of a testscript to show how to interact with the library.
SUBJECT TO CHANGE WHEN THE LIBRARY CHANGES
Author: Esther Kok
Date: 12-04-2018
"""
from datetime import datetime

import pyares as pa

# import matplotlib
# import pandas #because we need to work with dataframes later

# initalize the needed datasources
timestart = datetime.now()
data_provider = pa.HBaseParameterSampleProvider()

# get some params that you want to look for
# and of course some times as well

params = ['NPWD2491', 'NPWD2501', 'NPWD2531', 'NPWD2532', 'NPWD2551', 'NPWD2552', 'NPWD2561', 'NPWD2562', 'NPWD2691', 'NPWD2692']
timestamps = sorted([1387324800000, 1392024682831])
#params = ['NPWD2491', 'NPWD2501', 'NPWD2531', 'NPWD2532', 'NPWD2551', 'NPWD2552', 'NPWD2561', 'NPWD2562', 'NPWD2691', 'NPWD2692']
#timestamps = sorted([1387324800000, 1388584759000])

params = ['NPWD2372','NPWD2401','NPWD2402','NPWD2451','NPWD2471','NPWD2472','NPWD2481','NPWD2482','NPWD2491',
          'NPWD2501','NPWD2531','NPWD2532','NPWD2551','NPWD2552','NPWD2561','NPWD2562','NPWD2691','NPWD2692',
          'NPWD2721','NPWD2722','NPWD2742','NPWD2771','NPWD2791','NPWD2792','NPWD2801','NPWD2802','NPWD2821',
          'NPWD2851','NPWD2852','NPWD2871','NPWD2872','NPWD2881','NPWD2882']


timestamps = sorted([1388534410697, 1420070380120]) # ALL THE DATA T_T


df = data_provider.get_parameter_data_df(params, timestamps[0], timestamps[-1])
print(df.shape)
print(df)

timeend=datetime.now()
print(str(timeend-timestart))
"""
samples = data_provider.get_parameter_data_objs(params, timestamps[0], timestamps[-1])
values = []
for sample in samples:
    for s in sample:
        values.append(s.get_value())
print(values)
"""
#generators are iterators but you can only iterate over them once, because they don't store their results in mem
#raw_samples = (data_provider.get_scan(param, timestamps[0], timestamps[-1]) for param in params)


# get the samples from the raw_samples
#samples = (data_provider.get_param_sample(row) for scan in raw_samples for row in scan)


# convert samples into df and print the result
#df = data_provider.samples_into_dataframe(samples)
#print(df)
#df.plot()

"""
for sample in samples:
    print(sample.get_pid())
    print(sample.get_value())
"""
"""
def some_function(data):
    return data.count()


data_provider.execute_job(script='test_job.py', files='../dist/pyares-0.0.1-py3.4.egg',
                          venvs='../libs/venv.zip')


"""
"""


# get the pids belonging to the params


# create sample objects for each parameter and timestamp combination
# get all the needed rowkeys and save them in a list FOR NOW
rowkeys = []
for param in params:
    pid = pids.__next__()
    print(pid)
    for stamp in timestamps:
        sample = Sample(pid, 'TM', time=stamp, name=param)
        sample.set_rowkey()
        rowkeys.append(sample.get_rowkey())
print(rowkeys)
rows = hbaseconn.get_rows(rowkeys)
for i in rows:
    print(i)



# just to show what is in the generator, this is not something you are expected to do
import protobuf as pb
buf = pb.ProtoBuf

for scan in raw_samples:
    for s in scan:
        paramsam, paramdef = buf(s[1][b'v:e']).get_protobuf()
        print(paramsam,'\n',paramdef)


# we want to translate the raw samples into something that we can read and process
for scan in raw_samples:
    print(scan)
    for row in scan:
        print(row)
        print(hbase_provider.get_value(row))
        sample = hbase_provider.get_param_sample(row)

        print(sample.get_value())
"""
