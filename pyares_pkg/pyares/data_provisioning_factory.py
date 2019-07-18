import pymysql.cursors

from pyares.database_layer_impl import DatabaseLayerImpl


class DataProvisioningFactory:
    """
    Class for initializing the connection without executing it.
    :param datasource: needs a datasource object to init
    :return: Object of DatabaseLayerImpl initialized with the connection and the schema defined in the datasource
    """
    def __init__(self, datasource):

        self.__datasource = datasource
        self.__connection = None

    def create_database_layer(self):
        self.__connection = pymysql.connect(host=self.__datasource.get_host(),
                                            port=self.__datasource.get_port(),
                                            user=self.__datasource.get_user(),
                                            password=self.__datasource.get_password(),
                                            db=self.__datasource.get_database(),
                                            cursorclass=pymysql.cursors.SSDictCursor)  # cursor returns in dict form
        return DatabaseLayerImpl(self.__connection, self.__datasource.get_schema())





