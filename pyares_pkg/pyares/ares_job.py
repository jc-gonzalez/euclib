import pickle
import re
import subprocess

from inspect import signature

from pyspark import SQLContext, SparkConf, SparkContext, HiveContext
from pyspark.sql import Row, utils, Window
import pyspark.sql.functions as F
from pyspark.sql.types import StringType, FloatType, IntegerType, BooleanType

from pyares.pyares_conf_factory import PyAresConfigFactory as paconf
from pyares.parameter_sample_provider import ParameterSampleProvider

"""
# old imports, saved here until the next stable release
import pyarrow
import pyares.data_source as ds
import pyares.hbase_connect as hc
import pyares.protobuf as pb
import pyares.sample as sa
from pyares.byte_buffer import *
from pyares.data_provisioning_factory import *
"""


class AresJob:
    """
    Class only needed for Spark jobs, not for immediate data retrieval from HBase
    """
    def __init__(self, name='pyares_job'):
        self.__name = name
        self.__app_id = None

    def define_job(self,
                   function_dict=None,
                   perform_search=True,
                   persist_search=False,
                   calc_stats=False,
                   resolution='5m',
                   previous_results=None
                   ):
        """
        Define a job that can run calculations on parameter sample data in the ARES cluster.
        Read documentation for a more thorough description of the input dictionaries.
        :param function_dict: Dict containing the UDFs and the columns to perform them on.
        :param perform_search: Bool to flag whether you want to search for params in the job
        :param persist_search: Bool to persist the results of your search query as a seperate df in HDFS
        :param calc_stats: Bool if you want to calculate and persist statistics with the resolution
        :param resolution: Can be String 5m, 30m, 1d, OR any Int in microseconds
        :param previous_results: Dict defining which job_id's and which result types you want to reuse in the job
        """
        # TODO able to pass multiple functions on multiple columns
        # TODO columns is (nested) array of columns
        # TODO columns can also be 'all'
        # TODO create standard statistics calc function

        # TODO confirm that the statistics job is being correctly parallelized
        # TODO confirm if it's preferred to have a single DF for the stat job results or seperate ones for each param

        # TODO there is a lot going on in this function. Is there a way to seggregate the duties in subfunctions

        """
        Spark SQL defines the following types of functions:
        (https://jaceklaskowski.gitbooks.io/mastering-spark-sql/spark-sql.html)
        standard functions or User-Defined Functions (UDFs) that take values from a single row as input to generate a single return value for every input row.
        basic aggregate functions that operate on a group of rows and calculate a single return value per group.
        window aggregate functions that operate on a group of rows and calculate a single return value for each row in a group.
        """
        # Security checks #
        # If you try to run an empty job.
        if perform_search is False and previous_results is None and calc_stats is False:
            return "Can't run an empty job."

        # If you try to run calculations on no data.
        if perform_search is False and previous_results is None and function_dict is not None:
            return "You need data to do calculations. Either use a search or previous results to run the job."

        # Get the HDFS path to write the results to
        conf = paconf('pyares_conf.ini').get_conf('HDFS')
        result_path = conf['result_path']

        # initialize the spark context and the logger
        sc = SparkContext(conf=SparkConf().setAppName(self.__name))
        log4jlogger = sc._jvm.org.apache.log4j
        logger = log4jlogger.LogManager.getLogger('PyAres')
        logger.info("Running PyAres job.")
        # part of the fix related to JIRA ARESPY-20
        #sqlc = HiveContext(sc)
        sqlc = SQLContext(sc)

        # get the needed data from the pickle file
        with open('pyares.pkl', 'rb') as file:
            param_names, start, end = pickle.load(file)

        # if the data needs to come from HBase
        if perform_search:
            params = sc.parallelize(param_names)
            try:
                samples = params.flatMap(lambda x: self.__get_samples(x, start, end)).filter(lambda x: x is not None)
                rows = samples.map(lambda x: Row(timestamp=x.get_time(), value=x.get_value(), var_name=x.get_name()))
                acdf = sqlc.createDataFrame(rows, schema=['timestamp', 'value', 'var_name'])
                # TODO; for now type is inferred from the sampling ratio, later this should be in the sample object
            except ValueError:
                logger.info("Search returned no data. "
                            "Please consider using different parameters or a different time period.")
                return

            df = acdf.groupBy('timestamp').pivot('var_name').sum('value')
            #df = self.__fill_nans(df)
            acdf.unpersist()  # remove the old df from memory
            old_columns = df.columns[1:]

            # check which parameter didn't return data from MariaDB
            for param_name in param_names:
                if param_name not in old_columns:
                    logger.info("Parameter ['%s'] was not found in the database or was not found within the "
                                "given time frame. Please check if this is a valid parameter name and consider "
                                "using a different time frame." % param_name)

            if persist_search:
                df.write.save(('%s/%s_search_result' % (result_path, str(sc.applicationId))), mode='append')

        # If you want to use results from previous jobs
        if previous_results is not None:
            paths = ['%s/%s_%s_result/' % (result_path, key, value)
                     for key in previous_results.keys()
                     for value in previous_results[key]]
            if perform_search:
                for path in paths:
                    df = df.join(sqlc.parquetFile(path), on='timestamp')
                old_columns = df.columns[1:]
            else:
                df = sqlc.parquetFile(paths[0])
                for path in paths[1:]:
                    df = df.join(sqlc.parquetFile(path), on='timestamp')
                old_columns = df.columns[1:]

        # If you want to run a statistics jobs
        if calc_stats:
            stat_df = self.__calc_stats(df, resolution)
            stat_df.write.save(('%s/%s_stat_result' % (result_path, str(sc.applicationId))), mode='append')

        """ If you want to run udfs on the parameters
        According to https://medium.com/@mrpowers/performing-operations-on-multiple-columns-in-a-pyspark-dataframe-36e97896c378
        performance should be equal to doing this with map reduce.
        """
        if function_dict is not None:
            for key in function_dict.keys():
                try:
                    f = F.udf(function_dict[key][0], self.__check_f_type(function_dict[key][0]))
                    df = df.withColumn('%s' % key, f(*[F.col(x) for x in function_dict[key][1]]))

                    # part of the fix related to JIRA ARESPY-20
                    #bad_func = F.udf(self.__check_not_bad, BooleanType())
                    #cols = [F.col(x) for x in function_dict[key][1]]
                    #df = df.withColumn('%s' % key, f(*[F.col(x) for x in cols]))

                    #df = df.withColumn('test', F.lit(bad_func(*cols)))
                    #df = df.withColumn('test', F.lit(bad_func(*cols)).cast('string')=='false')
                    #df = df.withColumn('test_%s' % key , F.when(F.lit(bad_func(*cols)).cast('string')=='false', f(*cols)).otherwise(F.lit('None')))

                        #*[F.col(x) for x in function_dict[key][1]],
                        #                              f(*[F.col(x) for x in function_dict[key][1]])))
                except utils.AnalysisException:
                    logger.info("Cannot find parameter of query %s in result given current columns %s. "
                                "Please consider using different parameters or a different time period."
                                % (str(function_dict[key][1]),str(df.columns)))
                    pass

            # persist only the new results
            df.select([column for column in df.columns if column not in old_columns])\
                .write.save(('%s/%s_udf_result' % (result_path, str(sc.applicationId))), mode='append')

        logger.info("Finished PyAres job.")

    def execute_job(self, param_names, start, end,
                    script='spark_job.py',
                    wait_completion=False,
                    venvs= 'venv.zip'):
        """
        UNDER CONSTRUCTION
        Method for applying Spark jobs to the Yarn Cluster in cluster mode
        :param script: Python script (inclusion of path optional)
        :param memory: Amount of memory the job is allowed on each node
        :param executors: Number of executors the job is allowed to have on the cluster
        :param venvs: Python Virtualenv to include in the job
        """

        data_path = paconf().get_data_path()
        config_path = paconf().get_conf_path()
        spark_conf = paconf().get_conf('Spark')

        with open(data_path+'pyares.pkl', 'wb') as file:
            pickle.dump((param_names, start, end), file)

        print("Starting Spark job...")
        cmd = ('PYSPARK_PYTHON=./SP/bin/python3 '
               'spark-submit '
               '--master yarn '
               '--deploy-mode cluster '
               '--files %s#pyares.pkl,%s#pyares_conf.ini '
               '--archives %s#SP '
               '--conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=./SP/bin/python3 '
               '--conf spark.yarn.submit.waitAppCompletion=%s '
               '--driver-memory %s '
               '--executor-memory %s '
               '--num-executors %d '
               '%s' % (data_path+'pyares.pkl', config_path+'pyares_conf.ini',
                       data_path+venvs, str(wait_completion).lower(), str(spark_conf['driver_memory']),
                       str(spark_conf['executor_memory']), int(spark_conf['executors']),  script)
               )

        cmd_out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        cmd_out = cmd_out.decode("utf-8")

        yarn_app_ids = re.findall(r"application_\d{13}_\d{2,10}", cmd_out)
        self.__app_id = yarn_app_ids[0]

        if wait_completion:
            print("Job finished with id %s" % yarn_app_ids[0])
        else:
            print("Job submitted with id %s" % yarn_app_ids[0])

        return yarn_app_ids[0]

    def get_job_status(self, job_id=None):
        """
        Get the job status of either the last submitted job from current shell or the job with specified job ID
        :param job_id: String of full job_id as returned by execute_job (format application_<13 digits>_<4 digits>)
                        Set to None by default because the job_id persists in the AresJob as well.
        :return: dict with progress, state and final state of the job
        """

        if job_id:
            self.__app_id = job_id
        cmd = ('yarn application -status %s' % self.__app_id)
        cmd_out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        cmd_out = cmd_out.decode("utf-8")

        progress = re.findall(r"Progress : \d{1,3}%", cmd_out)[0].split()
        state = re.findall(r"State : \w{0,20}", cmd_out)[0].split()
        final_state = re.findall(r"Final-State : \w{0,20}", cmd_out)[0].split()
        status_dict = {progress[0]:progress[-1], state[0]: state[-1], final_state[0]: final_state[-1]}

        return status_dict

    def get_job_logs(self, job_id=None):
        if job_id:
            self.__app_id = job_id
        cmd = ('yarn logs -applicationId %s' % self.__app_id)
        cmd_out = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        cmd_out = cmd_out.decode("utf-8")
        output = "\n".join(re.findall(r".*PyAres:.*", cmd_out))
        return output

    def __get_samples(self, param_name, start, end):
        """
        Helper function that initiates the hbase connection inside the node, because connection objects
        cannot be serialized and transferred to the nodes from the driver.
        Fetches all the samples for a given parameter name.
        Only to be used from within a Spark job with a paralellized param_names rdd.
        Returns empty if the parameter cannot be found in the MariaDB
        :param param_name: String
        :param start: timestamp
        :param end: timestamp
        :return: generator with parameter data objects
        """

        dp = ParameterSampleProvider('pyares_conf.ini')

        try:
            #samples = dp.get_parameter_data_objs([param_name], start, end) # old implementation
            sample_objs = dp.get_parameter_data_objs([param_name], start, end)
            samples = [s for sample in sample_objs for s in sample]
            return samples

        except TypeError:
            return [None]

    def __calc_stats(self, df, resolution):
        """
        Calculates statistics for every column in the Spark DF and returns a seperate DF with the results.
        Statistics: sum, min, max, count, mean, kurtosis, skewness, stddev, variance.
        :param df: DF containing the columns that you want to run your statistics calculations on
        :param resolution: int resolution in milli or microseconds OR string '5m'/'1h'/'1d'
        :return: aggregation dataframe containing statistics
        """

        if type(resolution) is str:
            # resolution to microseconds
            res_dict = {'5m': 300000000,
                        '1h': 3600000000,
                        '1d': 86400000000}
            agg_interval = res_dict[resolution]

        elif type(resolution) is int:
            if len(str(resolution)) < 16:
                resolution = int(str(resolution).ljust(16, '0'))
            agg_interval = resolution

        ts_col = F.col('timestamp')
        df_ori_cols = list(set(df.columns) - set(['timestamp']))

        df = df.withColumn('interval_start', (F.floor(ts_col/agg_interval) * agg_interval))#\
               #.withColumn('interval_stop', F.ceil(ts_col/agg_interval) * agg_interval)\
               #.orderBy(F.col('interval_start'))
        agg_df = df.groupBy('interval_start').agg(F.max(ts_col).alias('max_ts'))

        # TODO Column type checking: string columns are automatically ignored and parse as NaN, so
        # TODO drop NaN columns?

        # TODO: interval_stop ignore, as well as drop max_ts
        # TODO: filter out NaN columns

        # TODO: question: run the statistics job as a seperate job without having to make a udf script

        stat_cols = df_ori_cols # [c for c in df_ori_cols if c not in ['interval_start', 'interval_stop', 'timestamp', 'max_ts']]
        for column in stat_cols:
            grouped_df = df.groupBy('interval_start')\
                           .agg(F.sum(column).alias('sum_%s' % column),
                                F.min(column).alias('min_%s' % column),
                                F.max(column).alias('max_%s' % column),
                                F.count(column).alias('count_%s' % column),
                                F.kurtosis(column).alias('kurtosis_%s' % column),
                                F.mean(column).alias('mean_%s' % column),
                                F.skewness(column).alias('skewness_%s' % column),
                                F.stddev(column).alias('stddev_%s' % column),
                                F.variance(column).alias('var_%s' % column))
            agg_df = grouped_df.join(agg_df, on='interval_start')
        #agg_df = agg_df.drop('max_ts').drop(F.when(F.col('*').isna())).dropna(how='all').drop_duplicates()

        return agg_df

    def __check_f_type(self, f):
        """
        Helper function to check for the annotation type of the function to base the return type of the UDF on.
        It currently accounts for ints, floats and defaults to strings.
        :param f: function as defined in the job definition
        :return: spark sql type matching the annotation type
        """
        sig = signature(f)
        return_type = sig.return_annotation
        if return_type is int:
            return IntegerType()
        elif return_type is float:
            return FloatType()
        else:
            return StringType()

    def __fill_nans(self, df):
        """
        UNDER CONSTRUCTION
        part of the fix related to JIRA ARESPY-20

        Helper funtion to forward of backward fill missing values in the dataframe
        Spark 2.x offers better functionality for this than 1.6
        """

        window = Window.partitionBy('timestamp').orderBy('timestamp').rowsBetween(-100000,0)
        for column in df.columns:
            df = df.withColumn('filled_%s' % column, F.last(F.col(column)).over(window).isNotNull())
        return df

    def __check_not_bad(self, *arg):
        """
        UNDER CONSTRUCTION
        part of the fix related to JIRA ARESPY-20

        Helper function for checking if the current value of the column is NaN on None
        :param n: column or list of columns
        :return: boolean for bad (true) or not bad (false)
        """
        bad = True
        for value in arg:
            if (value == value) | (value is not None): #(value != None)
                bad = False
        return bad
