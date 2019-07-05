import os

EAS_DPS_CUS_url= "http://eas-dps-cus.test.euclid.astro.rug.nl"

Env = os.environ

# extensions for decompressed, gzip and bzip2 compressed
Compressed_Exts = [
    '',
#    '.gz',
#    '.bz2',
]
Compressors = {
    '':         '',
#    '.gz':      'gzip --to-stdout --no-name ',
#    '.bz2':     'bzip2 --stdout --compress ',
}
Decompressors = {
    '':         '',
#    '.gz':      'gzip --to-stdout --decompress ',
#    '.bz2':     'bzip2 --stdout --decompress ',
}
MapAction = {
    'DSSGET': 'GET',
    'DSSSTORE':  'POST',
    'DSSSTORED':  'GET',
    'DSSMAKELOCAL': 'GET',
    'DSSMAKELOCALASY': 'GET',
    'DSSGETLOG': 'GET',
    'GETLOCALSTATS': 'GET',
    'GETGROUPSTATS': 'GET',
    'GETTOTALSTATS': 'GET',
    'LOCATE': 'GET',
    'LOCATEFILE': 'GET',
    'LOCATELOCAL': 'GET',
    'LOCATEREMOTE': 'GET',
    'MD5SUM': 'GET',
    'PING': 'GET',
    'SIZE': 'GET',
    'STAT': 'GET',
    'GET': 'GET',
    'GETANY': 'GET',
    'GETEXACT': 'GET',
    'GETLOCAL': 'GET',
    'GETREMOTE': 'GET',
    'STORE': 'POST',
    'STORED': 'POST',
    'HEAD': 'GET',
    'HEADLOCAL': 'GET',
    'DELETE': 'GET',
    'TAKEOVER': 'GET',
    'TESTCACHE': 'GET',
    'TESTSTORE': 'GET',
    'TESTFILE': 'GET',
    'REGISTER': 'GET',
    'RELEASE': 'GET',
    'RELOAD': 'GET',
    'DSSTESTGET': 'GET',
    'DSSTESTCONNECTION': 'GET',
    'DSSTESTNETWORK': 'GET',
    'DSSINIT': 'GET',
    'DSSINITFORCE': 'GET',
    'DSSGETTICKET': 'GET',
}