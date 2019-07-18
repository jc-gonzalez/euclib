from _datetime import datetime
from time import sleep

import pyares as pa


#params = ['sa','sb', 'sx', 'sy', 'sz', 'GAC11060']
params = ['sa', 'sy', 'sx']
#timestamps = sorted([1387524800000, 1388584759000])
#timestamps = sorted([1387424800000, 1388584759000])
timestamps = sorted([1388534410697, 1420070380120])  # all the timestamps

params = ['sa','sb']
#params = ['GAC11060', 'sa']
timestamps = sorted([1387524800000, 1388584759000])
#timestamps = sorted([1387424800000, 1388584759000])


data_provider = pa.init_aresjob()
job_id = data_provider.execute_job(script='spark_test_dev.py',
                                   param_names=params, start=timestamps[0], end=timestamps[-1])

start_time = datetime.now()
retriever = pa.init_param_jobresultretriever().get_job_result_df

while True:
    status = data_provider.get_job_status()
    print(status)
    if status['Final-State'] == 'SUCCEEDED':
        print("Time elapsed: %s" % str(datetime.now()-start_time))

        retriever = pa.init_param_jobresultretriever().get_job_result_df

        #print(retriever(job_id=job_id, result_type='search'))
        #print(retriever(job_id=job_id, result_type='stat'))
        result = retriever(job_id=job_id, result_type='udf')

        print(retriever(job_id=job_id, result_type='search'))
        #print(retriever(job_id=job_id, result_type='stat'))
        print(retriever(job_id=job_id, result_type='udf'))

        break
    if status['Final-State'] == 'FAILED':
        print("Job failed.")
        break
    sleep(10)


print(result)


print(data_provider.get_job_logs())
