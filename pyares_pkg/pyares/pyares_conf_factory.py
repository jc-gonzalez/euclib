from configparser import ConfigParser, ExtendedInterpolation

import inspect, os

class PyAresConfigFactory:
    """
    Handler for the configuration of PyAres
    Gets all the appropriate objects from the config file
    Pass them to the parts of code that need them
    """

    def __init__(self,
                 conf_file='/usr/lib/python3.4/site-packages/pyares/conf/pyares_conf.ini',
                 base_dir='/usr/lib/python3.4/site-packages/pyares'
                 ):

        # For testing use these
        #conf_file='/lhome2/sles12-dev-egos-mdb/sparkdev/pyares/pyares/conf/pyares_conf.ini',
        #base_dir='/lhome2/sles12-dev-egos-mdb/sparkdev/pyares/pyares'

        # To run in Docker, use these
        #conf_file='/usr/lib/python3.4/site-packages/pyares/conf/pyares_conf.ini',
        #base_dir='/usr/lib/python3.4/site-packages/pyares'

        if not base_dir:
            base_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))

        self.__conf_obj = ConfigParser(interpolation=ExtendedInterpolation())
        self.__conf_obj.read(conf_file)
        self.__base_dir = base_dir

    def get_conf(self, _type):
        return self.__conf_obj[_type]

    def get_conf_path(self):
        return self.__base_dir + '/conf/'

    def get_data_path(self):
        return self.__base_dir + '/data/'

