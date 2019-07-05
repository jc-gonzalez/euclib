#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dssserver_clientr.py

DSS client code
"""
#----------------------------------------------------------------------

# make print & unicode backwards compatible
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys

_filedir_ = os.path.dirname(__file__)
_appsdir_, _ = os.path.split(_filedir_)
_basedir_, _ = os.path.split(_appsdir_)
sys.path.insert(0, os.path.abspath(os.path.join(_filedir_, _basedir_, _appsdir_)))

PYTHON2 = False
PY_NAME = "python3"
STRING = str

#----------------------------------------------------------------------

from dss.dataio import DataIO
from dss.dss_rqsts import find_ticket, add_ticket, delete_ticket, delete_tickets, messageIAL
from dss.file_util import read_access_file, write_access_file, message

__version__ = 'Revision: 0.5.3.2'

import os
import sys
import datetime
import string
import ast

# DSS server, username, validity, ticket
dssaccessfile = []

def main():
    """
    call of the client interface
    """
    table = {
        'cachefile':    'cachefile',
        'get':          'get',
        'getcaps':      'getcaps',
        'getexact':     'getexact',
        'getid':        'getid',
        'getlocal':     'getlocal',
        'getremote':    'getremote',
        'getstats':     'getstats',
        'delete':       'delete',
        'head':         'head',
        'headlocal':    'headlocal',
        'locate':       'locate',
        'locatefile':   'locatefile',
        'locatelocal':  'locatelocal',
        'locateremote': 'locateremote',
        'md5sum':       'md5sum',
        'mirrorput':    'mirrorput',
        'ping':         'ping',
        'register':     'register',
        'release':      'release',
        'retrieve':     'get',
        'size':         'size',
        'stat':         'stat',
        'store':        'put',
        'testfile':     'testfile',
        'testcache':    'testcache',
        'teststore':    'teststore',
    }

    table_dss = {
        'retrieve': 'get',
        'store': 'put',
        'make_local': 'makelocal',
        'make_local_asy': 'makelocalasy',
        'ping': 'ping',
        'dsstestget': 'dsstestget',
        'dsstestnetwork': 'dsstestnetwork',
        'dsstestconnection': 'dsstestconnection',
        'dssinit': 'dssinit',
        'dssinitforce': 'dssinitforce',
        'dssgetticket': 'dssgetticket',
        'delete':'delete',
    }

    def usage():
        """
        print out of usage of client
        """
        message('''\
Usage:  %s operation=<o> server=<s> filename=<f> certfile=<c> debug=<d> secure=<b> query=<q>

        <o>     wanted operation, one of %s
        <s>     wanted server(s) in hostname:portnumber format
        <f>     filename
        <c>     certfile with certificate and key [no secure connect]
        <d>     debuglevel, 0 to 255 [0]
        <b>     True or False (don't need a certfile) [False]
        <q>     query to be attached to the filename

''' % (os.path.basename(sys.argv[0]), ','.join([k for k in table.keys()])))
        sys.exit(0)

    def usage_dss():
        message('''\
Usage:  %s operation=<o> server=<s> filename=<f> [localfilename=<l>] inputlist=<i>
                  certfile=<c> debug=<d> secure=<b> query=<q> username=<u> password=<p> 
                  [timeout=<t>] [looptime=<l>] [logfile=<g>] [accessfile=<a>]

        <o>     wanted operation, one of %s
        <s>     wanted server(s) in [http://|https://]hostname:portnumber format
        <f>     filename
        <l>     local filename to be used instead of filename, optional 
        <c>     certfile with certificate and key [no secure connect]
        <d>     debuglevel, 0 to 255 [0]
        <b>     True or False (don't need a certfile) [False]
        <q>     query to be attached to the filename
        <u>     username, username=ticket for SSO ticket
        <p>     password or SSO ticket
        <t>     timeout for connection to DSS server, in sec
        <l>     loop between requests to DSS server for asynchronious commands, in sec
        <g>     logfile 
        <i>     input list of filenames
        <a>     path to file with tickets

''' % (os.path.basename(sys.argv[0]), string.join([k for k in table_dss.keys()],', ')))
        sys.exit(0)


    uvars = {
        'operation':    '',
        'server':       '',
        'filename':     '',
        'localfilename': '',
        'certfile':     '',
        'debug':        0,
        'secure':       True,
        'query':        '',
        'fd':           '',
        'username':     '',
        'password':     '',
        'timeout':      None,
        'looptime':      1.0,
        'logfile':       '',
        'inputlist':     '',
        'accessfile':    '',
    }
    init_cookie={}
    o_no_filename = ['ping', 'dsstestget', 'dsstestnetwork', 'dsstestconnection',
                     'dssgetticket', 'dssinit', 'dssinitforce']
    if len(sys.argv) < 3:
        usage_dss()
    cnt=0
    for arg in sys.argv[1:]:
        (key, val) = string.split(arg, '=', maxsplit=1)
        if key in uvars.keys():
            if type(uvars[key]) == str:
                if key=='filename' and len(uvars[key])>0:
                    uvars[key]=uvars[key]+";"+val
                    cnt=cnt+1
                else:
                    uvars[key] = val
            else:
                uvars[key] = eval(val)
        else:
            raise Exception('Unknown key "%(key)s"' % vars())
#    print(cnt)
    if 'inputlist' in uvars and os.path.isfile(uvars['inputlist']):
        with open(uvars['inputlist']) as f_input: 
            data_list=f_input.read()
        filenames_list=";".join(k.strip() for k in data_list.split("\n") if k.strip())
        if 'filename' in uvars and len(uvars['filename'])>0: 
            uvars['filename']=uvars['filename']+";"+filenames_list
        else:
            uvars['filename']=filenames_list
    if 'filename' in uvars and uvars['filename'].find(";") >-1: 
        uvars['filename']=uvars['filename'].replace('"','')
    if uvars['operation'] not in table_dss.keys():
        raise Exception('Unknown operation "%s"' % uvars['operation'])
    # if table[uvars['operation']] not in ['getcaps', 'getid', 'getstats', 'ping',
    #                                      'release', 'reload', 'testcache', 'teststore'] and \
    #     not uvars['filename']: raise Exception, 'Need filename'
    if table_dss[uvars['operation']] not in o_no_filename and not uvars['filename']:
        raise Exception('Need filename')
    if uvars['server'].find("://") >-1: 
        (protocol,server)=uvars['server'].split("://")
        if protocol=='https': 
            uvars['secure']=True
        else: 
            uvars['secure']=False 
        uvars['server']=server
    #if not uvars['username']:
    #    print('WARNING: username is not provided, tickets will not be used')

    read_access_file(filename=uvars['accessfile'])
    delete_tickets()
    if uvars['server'] and uvars['username']:
        ticket = find_ticket(uvars['server'], uvars['username'])
        if ticket:
            init_cookie = {'server':uvars['server'], 'username':uvars['username'], 'ticket':ticket}

    ds_connect = DataIO(uvars['server'], debug=uvars['debug'], secure=uvars['secure'], \
                        certfile=uvars['certfile'], timeout=uvars['timeout'], \
                        looptime=uvars['looptime'], logfile=uvars['logfile'], \
                        username=uvars['username'], password=uvars['password'], cookie=init_cookie)
    errormes = ''
    try:
        if uvars['filename']:
            fd = None
            if uvars['fd']:
                fd = open(uvars['fd'], 'w')
            if uvars['query']:
                result = getattr(ds_connect, table_dss[uvars['operation']])\
                                (path=uvars['filename'], savepath=uvars['localfilename'],
                                query=uvars['query'], fd=fd)
            elif uvars['operation'] in 'make_local_asy':
                filenames_makelocal=uvars['filename'].split(";")
                n_files=len(filenames_makelocal)
#                print(n_files)
                if n_files>100:
                    result={}
                    count=0
                    while True: 
                        i_min=count*100
                        i_max=(count+1)*100
                        if i_min > n_files:
                            break
                        if i_max > n_files:
                            i_max=n_files+1
                        inp_filelist=";".join(filenames_makelocal[i_min:i_max])
                        if len(inp_filelist)>0:
                            result_i = getattr(ds_connect, table_dss[uvars['operation']])\
                                              (path=inp_filelist, savepath=uvars['localfilename'],
                                                fd=fd)
#                            print('Result:',inp_filelist,result_i)
                            output_dict = ast.literal_eval(result_i)
                            for key in list(output_dict.keys()):
                                result[key]=output_dict[key]
                        count=count+1 
                        if i_max > n_files:
                            break
#                    print(len(result.keys()))
                    result=str(result)
                else:
                    result = getattr(ds_connect, table_dss[uvars['operation']])\
                                    (path=uvars['filename'], savepath=uvars['localfilename'], fd=fd)
            else:
                result = getattr(ds_connect, table_dss[uvars['operation']])\
                                (path=uvars['filename'], savepath=uvars['localfilename'], fd=fd)
        else:
            result = getattr(ds_connect, table_dss[uvars['operation']])()
    except Exception as errmes:
        errormes = str(errmes)
        if ds_connect.response:
            errormes += ' DSS Server message:'
            errormes += str(ds_connect.response.reason)
        result = None
#        traceback.print_tb(sys.exc_info()[2])
    if errormes:
        #        message("operation %s failure!  Reason: %s" %(uvars['operation'], errmes))
        messageIAL(uvars['operation'], uvars['filename'], uvars['localfilename'], False, errormes)
    elif uvars['operation'] in ['ping']:
        messageIAL(uvars['operation'], uvars['filename'], uvars['localfilename'], result, errormes)
    elif uvars['operation'] in ['dssinit']:
        ticket = ds_connect.cookie['ticket']
        cookie_server = ds_connect.cookie['server']
        validity = (datetime.datetime.strptime(ds_connect.cookie['expires'], \
                                               "%A, %d %B %Y %H:%M:%S GMT") - \
                    datetime.datetime(1970,1,1)).total_seconds()
        add_ticket(cookie_server, uvars['username'], ticket, validity)
        write_access_file(filename=uvars['accessfile'])
        messageIAL(uvars['operation'], uvars['filename'], uvars['localfilename'], result, errormes)
    elif uvars['operation'] in ['dssinitforce']:
        ticket = ds_connect.cookie['ticket']
        cookie_server = ds_connect.cookie['server']
        validity = (datetime.datetime.strptime(ds_connect.cookie['expires'], \
                                               "%A, %d %B %Y %H:%M:%S GMT") - \
                    datetime.datetime(1970,1,1)).total_seconds()
        delete_ticket(cookie_server, uvars['username'])
        add_ticket(cookie_server, uvars['username'], ticket, validity)
        write_access_file(filename=uvars['accessfile'])
        messageIAL(uvars['operation'], uvars['filename'], uvars['localfilename'], result, errormes)
    else:
        #        message("operation %s success!  Result: %s" %(uvars['operation'], result))
        if uvars['operation'] in ['dsstestnetwork', 'dsstestconnection', 'make_local_asy']:
            errormes = result
        messageIAL(uvars['operation'], uvars['filename'], uvars['localfilename'], True, errormes)


if __name__ == '__main__':
    main()
