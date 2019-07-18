import pyarrow
import os
from pyares.pyares_conf_factory import PyAresConfigFactory as paconf


class ParameterJobResultRetriever:

    def get_job_result_df(self, job_id=None, result_type='search'):
        """
        Get the results stored in a Parquet file in HDFS returned into a Pandas DF.
        Job results from either the last submitted job from current shell or the job with specified job ID
        The subset that can be retrieved depends on the persisted results in the job
        :param job_id: String of full job_id as returned by execute_job (format application_<13 digits>_<4 digits>)
                        Set to None by default because the job_id persists in the AresJob as well.
        :param result_type: String with which subset of results you want to return. Can be 'udf', 'stat' or 'search'
        :return: Pandas DF with the results from the job
        """
        hdfs_conf = paconf().get_conf('HDFS')

        kerb_path = '/tmp/krb5cc_%s' % os.geteuid()
        if os.path.exists(kerb_path):
            kerb_ticket = kerb_path
        else:
            kerb_ticket = None

        fs = pyarrow.hdfs.connect('hdfs://%s' % hdfs_conf['namespace'],
                                  user=hdfs_conf['user'],
                                  kerb_ticket=kerb_ticket)

        result_path = hdfs_conf['result_path']

        file_dict = {'udf': '%s/%s_udf_result' % (result_path, job_id),
                     'stat': '%s/%s_stat_result' % (result_path, job_id),
                     'search': '%s/%s_search_result' % (result_path, job_id)}
        try:
            file = fs.read_parquet(file_dict[result_type])
            return file.to_pandas()
        except KeyError:
            return "%s is not a valid string for result_type. Choose 'udf', 'search' or 'stat'." % result_type