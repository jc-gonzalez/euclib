class Sample:
    """
    Description class for Sample
    :param pid: Integer
    :param name: String
    :param time: Long
    :param value: Type depending on value type in the buffer
    :param syselem: String
    :param validity: Validity of the sample
    :param type: Type of the value, corresponding with what is in the buffer
    """

    def __init__(self, pid, syselem, name=None, time=None, value=None, validity=None, type=None):
        self.__pid = pid
        self.__name = name
        self.__time = time
        self.__value = value
        self.__syselem = syselem
        self.__validity = validity
        self.__type = type
        # raw value
        # raw type
        # type

    """
    Setters
    """
    def set_pid(self, pid):
        self.__pid = pid

    def set_name(self, name):
        self.__name = name

    def set_time(self, time):
        self.__time = time

    def set_value(self, value):
        self.__value = value

    def set_syselem(self, syselem):
        self.__syselem = syselem

    def set_validity(self, validity):
        self.__validity = validity

    def set_type(self, type):
        self.__type = type

    """
    Getters
    """
    def get_pid(self):
        return self.__pid

    def get_name(self):
        return self.__name

    def get_time(self):
        return self.__time

    def get_value(self):
        return self.__value

    def get_syselem(self):
        return self.__syselem

    def get_validity(self):
        return self.__validity

    def get_type(self):
        return self.__type