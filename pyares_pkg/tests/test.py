import pyares as pa

from _datetime import datetime

dp = pa.init_param_sampleprovider()
#meta = dp.get_param_metadata_df()

params = ['sa', 'sy', 'sx']
start = 1388534400000
end = 1388620800000

start_dt = datetime.now()
df = dp.get_parameter_data_df(params, start, end)
print('DF elapsed: %s'%str(datetime.now()-start_dt))
print(df.shape)

start_dt = datetime.now()
obs = [o for obj in dp.get_parameter_data_objs(params, start, end) for o in obj]
print('Objs elapsed: %s'%str(datetime.now()-start_dt))
print(obs)



dp = pa.init_param_sampleprovider()
meta = dp.get_param_metadata_df()
print(meta)

