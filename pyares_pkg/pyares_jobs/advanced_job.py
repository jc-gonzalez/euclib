# It is also possible to create your own jobs if you know what you are doing
from pyspark import SparkContext, SparkConf
from pyspark.sql import SQLContext
import pyares as pa

sc = SparkContext(conf=SparkConf().setAppName('AdvancedSparkTest'))
sqlc = SQLContext(sc)


# you always need to create a helper function, because you cannot serialize the data retrieval
def sample_retriever(param_name, start, end):
    sp = pa.init_param_sampleprovider('pyares_conf.ini')
    sample_objs = sp.get_parameter_data_objs(param_name, start, end)
    samples = [s for sample in sample_objs for s in sample]
    return samples
