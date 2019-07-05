import binascii
import os
import pickle

from dss.dssserver_client import dssaccessfile


def python_to_ascii(*args):
    ''' binary to ascii '''
    return binascii.b2a_hex(pickle.dumps(args))


def ascii_to_python(arg):
    ''' ascii to binary '''
    return pickle.loads(binascii.a2b_hex(arg))


def read_access_file(filename=''):
    """ read file with DSS tickets
    """
    if not filename:
        filename = os.path.join(os.environ['HOME'], '.dssaccess')
    if os.path.isfile(filename):
        f = open(filename, 'r')
        for line in f.readlines():
            tockens = line.split(',')
            if len(tockens) == 4:
                tockens[3]=float(tockens[3])
                dssaccessfile.append(tockens)
        f.close()


def write_access_file(filename=''):
    """ write file with DSS tickets
    """
    if not filename:
        filename = os.path.join(os.environ['HOME'], '.dssaccess')
    f = open(filename, 'w')
    for line in dssaccessfile:
        line[3]=str(line[3])
        f.write(','.join(k for k in line) + '\n')
    f.close()


def message(s):
    """
    substitute message with print
    """
#    machine_name = socket.gethostname()
#    s_add = "%s %s " % (time.strftime('%B %d %H:%M:%S', time.localtime()), machine_name)
    print(s)