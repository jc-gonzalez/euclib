
from pyares.data_provisioning_factory import DataProvisioningFactory
from pyares.data_source import DataSource
from pyares.hbase_connect import HBaseConnect
from pyares.pyares_conf_factory import PyAresConfigFactory as paconf
from pyares.protobuf import ProtoBuf
from pyares.sample import Sample
from pyares.byte_buffer import ByteBuffer

import os


class ParameterSampleProvider:
    """
    The HBase Parameter Sample Provider
    """

    def __init__(self, conf=None):
        if not conf:
            if 'PYARES_INI_FILE' in os.environ:
                conf = os.environ['PYARES_INI_FILE']
                conf_file = paconf(conf)
            else:
                conf_file = paconf()
        else:
            conf_file = paconf(conf)
        mariadb_conf = conf_file.get_conf('MariaDB')
        self.__mariadb = DataSource(mariadb_conf)

        factory = DataProvisioningFactory(self.__mariadb)
        self.__dblayer = factory.create_database_layer()

        hbase_conf = conf_file.get_conf('HBase')
        self.__hbaseconn = HBaseConnect(hbase_conf)
        self.__hbaseconn.create_hbase_layer()
        print("Parameter Sample Provider initialized.")

        # test this solution for large queries on performance
        # consider if other solution is more suitable
        self.pid_dict = {}
        self.param_dict = {}
        self.system_element = 'TM'

    """
    Public Methods
    """
    def set_system_element(self, syselem='TM'):
        """
        Set System Element (default is TM)
        """
        self.system_element = syselem

    def set_system_element_as_any(self):
        """
        Set System Element to None, so any is implied
        """
        self.system_element = None

    def get_param_metadata_df(self):
        """
        Get all the parameter metadata into a pandas dataframe.
        Not recommended for lange databases.
        :return: pandas dataframe with columns
        ['NAME', 'DESCRIPTION', 'ENGVALUNIT','DATA_TYPE', 'RAW_DATA_TYPE']
        """
        import pandas as pd
        metadata = self.__dblayer.get_metadata()
        meta_df = pd.DataFrame(metadata)
        meta_df = meta_df.set_index('PID')
        meta_df = meta_df.rename(columns={'DATACATEGORY_str':'DATA_TYPE', 'RAW_DATACATEGORY_str':'RAW_DATA_TYPE'})
        return meta_df[['NAME', 'DESCRIPTION', 'ENGVALUNIT','DATA_TYPE', 'RAW_DATA_TYPE']]

    def get_param_name_list(self):
        """
        DEPRECATED, please use get_param_metadata_df()
        Fetch all the paramnames in the database to know what's in there.
        Not recommended for large databases!
        :return: List of all param names
        """
        return self.__dblayer.get_paramnames_list()

    def get_parameter_data_df(self, param_names, start, end):
        """
        Get all the available samples for a given n parameter names and return a pandas dataframe with their data.
        Colums: Timestamp, Param_1, ..., Param_n
        Values: Correspond with the raw_values in HBase
        :param param_names: String or List of strings with parameter name(s)
        :param start: Timestamp with the start of the period
        :param end: Timestamp with the end of the period
        :return: the resulting dataframe
        """
        samples = self.get_parameter_data_objs(param_names, start, end)
        df = self.__samples_into_dataframe(samples)
        # part of the fix related to JIRA ARESPY-20, not implemented for version stability
        #df = df.fillna(method='ffill').fillna(method='bfill')
        return df

    def get_parameter_sysel_data_df(self, param_names, param_syselem, start, end):
        """
        Get all the available samples for a given n parameter names and return a pandas dataframe with their data.
        Colums: Timestamp, Param_1, ..., Param_n
        Values: Correspond with the raw_values in HBase
        :param param_names: String or List of strings with parameter name(s)
        :param start: Timestamp with the start of the period
        :param end: Timestamp with the end of the period
        :return: the resulting dataframe
        """
        samples = self.get_parameter_data_sysel_objs(param_names, param_syselem, start, end)
        df = self.__samples_into_dataframe(samples)
        # part of the fix related to JIRA ARESPY-20
        #df = df.fillna(method='ffill').fillna(method='bfill')
        return df

    def get_parameter_data_objs(self, param_names, start, end):
        """
        Get all the available samples for a given n parameter names and return a collection of sample objects
        :param param_names: List of strings with parameter name(s)
        :param start: Timestamp with the start of the period
        :param end: Timestamp with the end of the period
        :return: iterator for the samples
        """

        samples = []
        for param in param_names:
            pid = self.__dblayer.get_param_id(param, self.system_element)
            self.pid_dict[pid] = param
            self.param_dict[param] = pid

            raw_samples = self.__get_scan(param, start, end)
            samples.append(self.__get_param_sample(data) for key, data in raw_samples)

        return samples

    def get_parameter_sysel_data_objs(self, param_names, param_syselem, start, end):
        """
        Get all the available samples for a given n parameter names and return a collection of sample objects
        :param param_names: List of strings with parameter name(s)
        :param start: Timestamp with the start of the period
        :param end: Timestamp with the end of the period
        :return: iterator for the samples
        """

        samples = []
        for param, syselem in zip(param_names, param_syselem):
            pid = self.__dblayer.get_param_id(param, syselem)
            self.pid_dict[pid] = param
            self.param_dict[param] = pid

            raw_samples = self.__get_scan(param, start, end)
            samples.append(self.__get_param_sample(data) for key, data in raw_samples)

        return samples

    def get_parameter_pids_data_objs(self, from_pid, to_pid, start, end):
        """
        Get all the available samples for a given n parameter names and return a collection of sample objects
        :param param_names: List of strings with parameter name(s)
        :param start: Timestamp with the start of the period
        :param end: Timestamp with the end of the period
        :return: iterator for the samples
        """

        data = self.__dblayer.get_params_from_pids(from_pid, to_pid, self.system_element)
        param_names = [item['NAME'] for item in data]
        samples = []
        for param in param_names:
            pid = self.__dblayer.get_param_id(param, self.system_element)
            self.pid_dict[pid] = param
            self.param_dict[param] = pid

            raw_samples = self.__get_scan(param, start, end)
            samples.append(self.__get_param_sample(data) for key, data in raw_samples)

        return (param_names, samples)

    def get_parameter_names_from_pids(self, from_pid, to_pid):
        """
        Get all the available samples for a given n parameter names and return a collection of sample objects
        :param param_names: List of strings with parameter name(s)
        :param start: Timestamp with the start of the period
        :param end: Timestamp with the end of the period
        :return: iterator for the samples
        """

        data = self.__dblayer.get_params_sysel_from_pids(from_pid, to_pid, self.system_element)
        param_names = [item['NAME'] for item in data]
        param_syselem = [item['SYSTEM_ELEMENT'] for item in data]
        #print(list(zip(param_names, param_syselem)))
        return (param_names, param_syselem)

    def get_parameter_pid_sysel_from_names(self, names):
        """
        Get all the available samples for a given n parameter names and return a collection of sample objects
        :param param_names: List of strings with parameter name(s)
        :param start: Timestamp with the start of the period
        :param end: Timestamp with the end of the period
        :return: iterator for the samples
        """

        data = self.__dblayer.get_params_pid_sysel_from_names(names)
        param_pid = [item['PID'] for item in data]
        param_syselem = [item['SYSTEM_ELEMENT'] for item in data]
        return (param_pid, param_syselem)

    """
    Private Methods
    """
    def __get_param_sample(self, hbase_row):
        """
        Get all the sample attributes into an object, retrieved from the buffer.
        :param hbase_row: the raw buffer as retrieved from hbase
        :return: sample object
        """

        buf = ProtoBuf(hbase_row[b'v:e'])
        pid = buf.get_buf_pid()
        syselem = buf.get_buf_syselem() if buf.get_buf_syselem() != '' else self.system_element
        value = buf.get_buf_value()
        sam_type = buf.get_buf_type()
        time = buf.get_buf_gen_time()
        validity = buf.get_buf_validity()
        name = self.pid_dict[pid]
        raw_sample = Sample(pid, syselem, time=time, value=value, type=sam_type, validity=validity, name=name)

        return raw_sample

    def __get_scan(self, param_name, start_time, end_time):
        """
        Gets an HBase scan for a given parameter name and a given start and end time
        :param param_name: String
        :param start_time: Int
        :param end_time: Int
        :return: all the results from the scan
        """

        start_key = self.__get_rowkey(param_name, start_time)
        end_key = self.__get_rowkey(param_name, end_time)

        return self.__hbaseconn.create_scan(start_key, end_key)

    def __samples_into_dataframe(self, samples):
        """
        Converts n samples into a Pandas DF with columns
        Timestamp, Paramname for each unique paramname in samples
        :param samples: List of sample objects
        :return: pandas dataframe
        """

        import pandas as pd

        sample_dict = {'timestamp': [], 'var_name': [], 'value': []}
        for sample in samples:
            for s in sample:
                sample_dict['timestamp'].append(s.get_time())
                sample_dict['var_name'].append(s.get_name())
                sample_dict['value'].append(s.get_value())

        df = pd.DataFrame(data=sample_dict, columns=['timestamp', 'var_name', 'value'])
        df = df.pivot(index='timestamp', columns='var_name', values='value')
        return df

    def __get_rowkey(self, param_name, timestamp):
        """
        Translates a parameter name and corresponding timestamp to a bytebuffer rowkey
        :param param_name: String name of parameter
        :param timestamp: Integer timestamp in milli or micro seconds
        :return: the bytebuffer rowkey needed for the hbase scan
        """
        pid = self.param_dict[param_name]
        row_key = ByteBuffer()
        row_key.put_int(pid)
        if len(str(timestamp)) < 16:
            timestamp = int(str(timestamp).ljust(16, '0'))
        row_key.put_long(timestamp)
        return row_key.get_bytebuffer()

    def __get_value(self, hbase_row):
        """
        Get the decoded protobuf from the raw data hbase row
        :param hbase_row:
        :return: the decoded protobuf
        """
        value = hbase_row[1][b'v:e']
        return ProtoBuf(value).get_buf_value()

