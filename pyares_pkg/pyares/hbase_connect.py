import happybase

# TODO connection open/close take closer look at what is preferred


class HBaseConnect:
    """
    Connection layer for HBase. Connection is only opened when actual data is getting fetched.
    :param hostname: String hostname
    :param port: Integer port
    """

    def __init__(self, hbase_conf_obj):
        self.__hostname = hbase_conf_obj['host']
        self.__port = int(hbase_conf_obj['port'])
        self.__connectionpool = None
        self.__dataspace = hbase_conf_obj['dataspace']

        # TODO in the future the table specification should be more general, not just for parameter samples
        self.__table = "ARES_%s_ParamSamples" % self.__dataspace

    def create_hbase_layer(self):
        """
        Create the connection to HBase. ConnectionPool establishes the first connection immediately,
        so wrong host or port are immediately detected.
        """
        self.__connectionpool = happybase.ConnectionPool(size=25,
                                                         host=self.__hostname,
                                                         port=self.__port)

    def get_families(self):
        """
        Get the table families of a certain table
        :param table: String table that you want to fetch data from
        :return: Dictionary with nested family and quantifier information
        """
        with self.__connectionpool.connection() as connection:
            conn_table = connection.table(self.__table)
            families = conn_table.families()
        return families

    def get_row(self, rowkey):
        """
        Get multiple rows for a list of rowkeys.
        :param rowkey: String of rowkey
        :param table: String table that you want to fetch data from
        :return: List of (row_key, rowd_ict) tuples ??
        """
        with self.__connectionpool.connection() as connection:
            conn_table = connection.table(self.__table)
            row = conn_table.row(rowkey)
        return row

    def get_rows(self, rowkeys):
        """
        Get multiple rows for a list of rowkeys.
        :param rowkeys: List of rowkeys
        :param table: String table that you want to fetch data from
        :return: List of (row_key, rowd_ict) tuples
        """
        rows = (self.get_row(rowkey) for rowkey in rowkeys)
        return rows

    def create_scan(self, start_key, end_key, buffsize=100000, #10000
                    maxsamples=100000):
        """
        Scans HBase for a specific parameter in a timestamp range
        Creates an iterator that can iterate over the retrieved rows.
        :param start: Int start timestamp
        :param end: Int end timestamp
        :param buffsize: Int
        :param maxsamples: Int
        :param table: String HBase table to search
        :return: iterable for looping over the matching rows
        """
        with self.__connectionpool.connection() as connection:
            conn_table = connection.table(self.__table)
            scan = conn_table.scan(row_start=start_key,
                                   row_stop=end_key,
                                   reverse=False,
                                   batch_size=min(buffsize, maxsamples),
                                   scan_batching=None) #True

        return scan
