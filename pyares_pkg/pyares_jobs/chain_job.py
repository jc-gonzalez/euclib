# this is a demonstration to show you how you can chain multiple jobs together to use the results from other jobs
import pyares as pa

from time import sleep
from _datetime import datetime
import pandas as pd

def print_status(aj_obj):
    start_time = datetime.now()
    while True:
        status = aj_obj.get_job_status()
        print(status)
        if status['Final-State'] == 'SUCCEEDED':
            print("Time elapsed: %s" % str(datetime.now()-start_time))
            break
        if status['Final-State'] == 'FAILED':
            print("Job failed.")
            break
        sleep(10)


params = ['sa','sx', 'sy', 'sz']
timestamps = sorted([1387424800000, 1388584759000])
#timestamps = sorted([1388534410697, 1420070380120])  # all the timestamps

aj = pa.init_aresjob()
job_id1 = aj.execute_job(script='job1.py', param_names=params, start=timestamps[0], end=timestamps[-1])
print_status(aj)

job_id2 = aj.execute_job(script='job2.py', param_names=params, start=timestamps[0], end=timestamps[-1])
print_status(aj)

retriever = pa.init_param_jobresultretriever().get_job_result_df
result1 = retriever(job_id=job_id1, result_type='udf')
result2 = retriever(job_id=job_id2, result_type='udf')

result = pd.merge(result1, result2, how='left', on='timestamp')
print(result)

print(aj.get_job_logs())