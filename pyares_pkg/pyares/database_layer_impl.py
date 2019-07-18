# assumption is that one paramid only matches with one paramname and vice versa
# for each systemelement at least.
# so each query should only match one row.

# TODO include loggers
# TODO looaaaaads of try/except/asserts etc
# TODO make sure that there are no trailing SQL connections (connection pool?)

"""
TODO: Consider optimizations
Does it help to sort a list of params? For HBase, yes, because it's sorted by pid, so sorted on pid
Does it help to optimize for branch mispredictions? Don't think so, but sorting things might.
"""


class DatabaseLayerImpl:

    def __init__(self, connection, schema):
        self.__connection = connection
        self.__schema = schema

    def fetch_all(self):
        """
        Connects to the database and returns all the rows
        Only for testing, not recommended to use in production
        :return: dictionary with all the rows
        """
        with self.__connection.cursor() as cursor:
            query = "SELECT * FROM %s" % self.__schema
            cursor.execute(query)
            return cursor.fetchall()

    def get_param_id(self, param_name, syselem):
        """
        Get the ID that corresponds with a certain parameter name and corresponding system element
        :param param_name: string that is the name of the parameter
        :param syselem: string that is the system element
        :return: integer value that is the ID
        """

        with self.__connection.cursor() as cursor:
            query = "SELECT PID FROM %s WHERE NAME= '%s' AND SYSTEM_ELEMENT= '%s'" % (self.__schema, param_name, syselem)
            cursor.execute(query)
            result = cursor.fetchone()
        return result['PID']
#------
    def get_param_re_names(self, param_name_re, syselem):
        """
        Get the ID that corresponds with a certain parameter name and corresponding system element
        :param param_name: string that is the name of the parameter
        :param syselem: string that is the system element
        :return: integer value that is the ID
        """

        with self.__connection.cursor() as cursor:
            query = "SELECT PID FROM %s WHERE NAME LIKE '%s' AND SYSTEM_ELEMENT= '%s'" % (self.__schema, param_name_re, syselem)
            cursor.execute(query)
            result = cursor.fetchone()
        return result['PID']

    def get_params_from_pids(self, frompid, topid, syselem=None):
        """
        Get the ID that corresponds with a certain parameter name and corresponding system element
        :param param_name: string that is the name of the parameter
        :param syselem: string that is the system element
        :return: integer value that is the ID
        """

        with self.__connection.cursor() as cursor:
            query = ''
            if not syselem:
                query = ("SELECT NAME FROM %s WHERE " +
                         " PID BETWEEN %s AND %s") % (self.__schema, frompid, topid)
            else:
                query = ("SELECT NAME FROM %s WHERE " +
                         " SYSTEM_ELEMENT='%s'" +
                         " AND PID BETWEEN %s AND %s") % (self.__schema, syselem, frompid, topid)
            cursor.execute(query)
            result = cursor.fetchall()

        return result

    def get_params_sysel_from_pids(self, frompid, topid, syselem=None):
        """
        Get the ID that corresponds with a certain parameter name and corresponding system element
        :param param_name: string that is the name of the parameter
        :param syselem: string that is the system element
        :return: integer value that is the ID
        """

        with self.__connection.cursor() as cursor:
            query = ''
            if not syselem:
                query = ("SELECT NAME,SYSTEM_ELEMENT FROM %s WHERE " +
                         " PID BETWEEN %s AND %s") % (self.__schema, frompid, topid)
            else:
                query = ("SELECT NAME,SYSTEM_ELEMENT FROM %s WHERE " +
                         " SYSTEM_ELEMENT='%s'" +
                         " AND PID BETWEEN %s AND %s") % (self.__schema, syselem, frompid, topid)
            cursor.execute(query)
            result = cursor.fetchall()

        return result

    def get_params_pid_sysel_from_names(self, names):
        """
        Get the ID that corresponds with a certain parameter name and corresponding system element
        :param param_name: string that is the name of the parameter
        :param syselem: string that is the system element
        :return: integer value that is the ID
        """

        with self.__connection.cursor() as cursor:
            namelist = ','.join(["'{}'".format(name) for name in names])
            query = ("SELECT PID,SYSTEM_ELEMENT FROM %s WHERE " +
                     " NAME IN (%s)") % (self.__schema, namelist)
            print(query)
            cursor.execute(query)
            result = cursor.fetchall()

        return result

#-----
    def get_description(self, param, syselem): #, param_name=None, pid=None, ):
        """
        Get the description that corresponds to a certain parameter name or parameter id.
        Give either param_name or pid. If both given, the param_name will be used
        :param param: string parameter name or integer pid
        :param syselem: string of system element
        :return: string with description
        """
        if type(param) == str:
            query = "SELECT DESCRIPTION FROM %s WHERE NAME='%s' AND SYSTEM_ELEMENT='%s'" % (self.__schema, param, syselem)
        elif type(param) == int:
            query = "SELECT DESCRIPTION FROM %s WHERE PID='%s' AND SYSTEM_ELEMENT='%s'" % (self.__schema, param, syselem)
        else:
            print("Can't execute an empty query. Give a parameter name or id number.")
            return None

        with self.__connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
        return result['DESCRIPTION']

    def get_paramnames_list(self):
        """
        Fetch all the paramnames in the database to know what's in there.
        Not recommended for large databases
        :return: List of all param names
        """
        # TODO include syselem?

        query = "SELECT NAME FROM %s" % self.__schema
        with self.__connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        return [val['NAME'] for val in result]

    def get_param_name(self, param_id, syselem):
        """
        Get the name that corresponds with a certain parameter ID and corresponding system element
        :param param_id: int that is the ID of the parameter
        :param syselem: string that is the system element
        :return: String value that is the name
        """

        with self.__connection.cursor() as cursor:
            query = "SELECT NAME FROM %s WHERE PID= '%s' AND SYSTEM_ELEMENT= '%s'" % (self.__schema, param_id, syselem)
            cursor.execute(query)
            result = cursor.fetchone()
        return result['NAME']

    def get_metadata(self):
        query = "SELECT a.*, " \
                "b.VALUE as DATACATEGORY_str, " \
                "c.VALUE as RAW_DATACATEGORY_str " \
                "FROM %s a " \
                "LEFT JOIN DATA_DEFS_TYPE_TBL b ON a.DATACATEGORY=b.PKEY " \
                "LEFT JOIN DATA_DEFS_TYPE_TBL c ON a.RAW_DATACATEGORY=c.PKEY " \
                "order by a.PID;" % self.__schema
        with self.__connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
        return result
