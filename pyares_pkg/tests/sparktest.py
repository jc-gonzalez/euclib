# test with using persisted results in ares_jobs, and with defining which udf has to be performed over which column

import pyspark.sql.functions as F
from pyspark.sql.types import StringType, FloatType, IntegerType
from pyspark import SQLContext, SparkConf, SparkContext
from inspect import signature


def add10(data) -> int:
    return data + 10


def addcols(x,y):
    return x+y


def add10cols(x,y):
    return x+y



sc = SparkContext(conf=SparkConf().setAppName('sparkoptimizationtest'))
sqlc = SQLContext(sc)

# persisted results also in dict
results_dict = {'application_1533282160533_0003': ['udf']}

# create a function that can check the column names from persisted results

paths = ['hdfs://nameservice1/tmp/sparkdev/%s_%s_result/' % (key, value) for key in results_dict.keys() for value in results_dict[key]]

df = sqlc.parquetFile(paths[0])
for path in paths[1:]:
    df = df.join(sqlc.parquetFile(path), on='timestamp')

#df.show()
df = df.withColumn('add100_sa', F.col('add100_sa').astype('int'))
#print(df.dtypes)

#function_dict = {'add10_sa': (add10, ['sa']), 'add10_sx': (add10, ['sx']), 'addcols_sxsy': (addcols, ['sx', 'sy'])}
#function_dict = {'add10_sa': (add_udf, ['sa'])}
function_dict = {'add10_sa': (add10, ['add100_sa'])}

add_udf = F.udf(lambda x: '1' if x >=30 else '0', StringType())


def check_type(f):
    sig = signature(f)
    return_type = sig.return_annotation
    if return_type is int:
        return IntegerType()
    elif return_type is float:
        return FloatType()
    else:
        return StringType()

for key in function_dict.keys():
    f = F.udf(function_dict[key][0], check_type(function_dict[key][0]))
    df = df.withColumn('%s' % key, f(*[F.col(x) for x in function_dict[key][1]]))

#df.show()
print(df.dtypes)

# statistics

agg_interval = 900000000 # microseconds, so 15 mins
#agg_interval = 604800000000 # 1 week in mus
ts_col = F.col('timestamp')
columns = df.columns[1:]
df = df.withColumn('floor', (F.floor(ts_col/agg_interval) * agg_interval))\
    .withColumn('ceiling', (F.ceil(ts_col/agg_interval) * agg_interval)).orderBy(F.col('floor'))
#df.show()
#print(df.dtypes)
column = 'add100_sa'

print(columns)
# mean, median, std,
agg_df = df.groupBy('floor').agg(F.sum(column), F.min(column), F.max(column))#, F.count(column),
                                           #F.kurtosis(column), F.mean(column), F.skewness(column),
                                           #F.stddev(column), F.variance(column))
dropcols = agg_df.select([agg_df.where(F.isnan(F.col(c)), c).alias(c) for c in agg_df.columns])
dropcols.show()

agg_df = agg_df.drop('ceiling').dropna(how='all').drop_duplicates()
#agg_df.show()

#otheragg_df = df.groupBy('floor').agg()
#otheragg_df.show()

#new_agg = otheragg_df.join(agg_df, on='floor')
#new_agg.show()


#df = df.withColumn('%s' % (str(key.__name__)), key(*[F.col(x) for x in function_dict[key]]))



#stat_df = df.describe(df.columns[1:])
#stat_df.show()

# persist only the new results
# old_columns = []
# df.drop(old_columns)