
class DataSource:
    """
    Class defining the attributes for the connection to MariaDB. For each of the properties there is a setter and a getter.
    Except for password, this only has a setter.
    :param host: string of the name or IP address of the host
    :param username: string
    :param password: string
    :param database: string of the databasename that you want to connect to
    :param schema: string of the schema where you want to fetch the rows from
    """

    def __init__(self, mariadb_conf_obj):
        """
        Will eventually disappear, but I'm too lazy to init al these things for now
        """
        self.__host = str(mariadb_conf_obj['host'])
        self.__username = str(mariadb_conf_obj['user'])
        self.__password = str(mariadb_conf_obj['password'])
        self.__database = str(mariadb_conf_obj['database'])
        self.__port = int(mariadb_conf_obj['port'])
        self.__schema = 'DATA_DEFS_TBL'

    def set_host(self, host):
        self.__host = host

    def set_user(self, username):
        self.__username = username

    def set_password(self, password):
        self.__password = password

    def set_database(self, database):
        self.__database = database

    def set_schema(self, schema):
        self.__schema = schema

    def set_port(self, port):
        self.__port = port

    def get_host(self):
        return self.__host

    def get_user(self):
        return self.__username

    def get_password(self):
        return self.__password

    def get_database(self):
        return self.__database

    def get_schema(self):
        return self.__schema

    def get_port(self):
        return self.__port
