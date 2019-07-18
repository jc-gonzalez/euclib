from _datetime import datetime
from time import sleep

import pyares as pa
import pandas as pd

# all solar aspect angles and all the timestamps.
params = ['sa', 'sx', 'sy', 'sz']
start = 1388534400000 # GMT: Wednesday, 1 January 2014 00:00:10.697
#end = 1389139200000 # GMT: Wednesday, 8 January 2014 00:00:00
#end = 1420070380120 # Wednesday, 31 December 2014 23:59:40.120
#end = 1388584759000 #  Wednesday, 1 January 2014 13:59:19
end = 1388620800000 # GMT: Thursday, 2 January 2014 00:00:00
#end = 1391212800000 # 1 month

data_provider = pa.init_aresjob()
job_id = data_provider.execute_job(script='mex_job.py',
                                   param_names=params,
                                   start=start,
                                   end=end)
start_time = datetime.now()

while True:
    status = data_provider.get_job_status()
    print(status)
    if status['Final-State'] == 'SUCCEEDED':
        print(data_provider.get_job_logs())
        print("Time elapsed: %s" % str(datetime.now()-start_time))

        retriever = pa.init_param_jobresultretriever().get_job_result_df
        search = retriever(job_id=job_id, result_type='search')
        stat = retriever(job_id=job_id, result_type='stat')
        udf = retriever(job_id=job_id, result_type='udf')
        break

    if status['Final-State'] == 'FAILED':
        print(data_provider.get_job_logs())
        print("Job failed.")
        break
    sleep(10)

print(search)
print(stat)
#print(stat.columns)
#print(stat.describe())
print(udf)

