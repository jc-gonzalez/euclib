import pyares.param_pb2 as param_pb2


class ProtoBuf:
    def __init__(self, buf):
        self.__paramsam = param_pb2.ParamSample()
        self.__paramsam.ParseFromString(buf)

        self.__paramdef = param_pb2.ParamDefinition()
        self.__paramdef.ParseFromString(buf)

    def get_protobuf(self):
        return self.__paramsam, self.__paramdef

    def get_buf_pid(self):
        return self.__paramsam.pid

    def get_buf_gen_time(self):
        return self.__paramsam.gen_time

    def get_buf_validity(self):
        # TODO translate validity numbers to strings?
        return self.__paramsam.validity

    def get_buf_type(self):
        return self.__paramsam.type

    def get_buf_value(self):
        # TODO built in check if val and raw_val is equal
        #assert self.__paramsam.type == self.__paramdef.raw_type

        type_map = {0: str(self.__paramsam.v_str), # unknown
                    1: int(self.__paramsam.v_bit), # bit
                    2: int(self.__paramsam.v_long), # utinyint
                    3: int(self.__paramsam.v_long), # stinyint
                    4: int(self.__paramsam.v_long), # usmallint
                    5: int(self.__paramsam.v_long), # ssmallint
                    6: int(self.__paramsam.v_long), # umediumint
                    7: int(self.__paramsam.v_long), # smediumint
                    8: int(self.__paramsam.v_long), # sint
                    9: int(self.__paramsam.v_long), # uint
                    10: float(self.__paramsam.v_flt), # float
                    11: float(self.__paramsam.v_dbl), # double
                    12: str(self.__paramsam.v_str), # string
                    13: str(self.__paramsam.v_str), # datetime
                    14: str(self.__paramsam.v_str), # job
                    15: str(self.__paramsam.v_str), # log
                    }

        value = type_map[self.__paramsam.type]
        return value

    def get_buf_name(self):
        return self.__paramdef.name

    def get_buf_syselem(self):
        return self.__paramdef.system_element
