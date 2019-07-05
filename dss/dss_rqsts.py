import datetime
import hashlib
import os
import socket
import time
import urllib

from dss.dataio import DataIO
from dss.dssserver_client import dssaccessfile
from dss.dss_data import EAS_DPS_CUS_url, Env
from dss.file_util import message


def find_ticket(server, username):
    """ find ticket for server and user
    """
    tnow = time.time()
    for line in dssaccessfile:
        if line[0] == server and line[1] == username:
            try:
                if float(line[3]) > tnow:
                    return line[2]
                else:
                    machine_name = socket.gethostname()
                    #print('%s %s find_ticket: Ticket for %s expired, repeat dssinit' % (
                    #    time.strftime('%B %d %H:%M:%S', time.localtime()), machine_name, server))
            except:
                return None
    return None


def add_ticket(server, username, ticket, validity):
    """ find ticket for server and user
    """
    for line in dssaccessfile:
        if line[0] == server and line[1] == username:
            line[3] = validity
            line[2] = ticket
            return 1
    line=[server, username, ticket, validity]
    dssaccessfile.append(line)
    return -1


def delete_ticket(server, username):
    """ remove ticket for server and user
    """
    for line in dssaccessfile:
        if line[0] == server and line[1] == username:
            dssaccessfile.remove(line)
    return 1


def delete_tickets():
    """ delete expired tickets
    """
    tnow = (datetime.datetime.utcnow()-datetime.datetime(1970,1,1)).total_seconds()
    machine_name = socket.gethostname()
    for line in dssaccessfile:
        if float(line[3]) < tnow:
            dssaccessfile.remove(line)
            #print('%s %s delete_tickets: Ticket for %s expired, repeat dssinit' % (
            #    time.strftime('%B %d %H:%M:%S', time.localtime()), machine_name, line[0]))


def _ping(host, port):
    """
    See if there is a server running out there
    """
    r = True
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
    except Exception:
        r = False
    s.close()
    return r


def dataserver_result_to_dict(result):
    '''
    method to make dictionary of dataserver locate result
    '''
    d = {}
    for elem in result.split(','):
        key, value = elem.split('=')
        d[key] = value
    return d


def fetch_file_from_dataserver(filename, hostport=None, savepath=None, query=None):
    '''
    method to retrieve a file from a dataserver
    '''
    if savepath and os.path.exists(savepath):
        raise Exception('File  %s already exists!' % savepath)
    if not savepath and os.path.exists(filename):
        raise Exception('File  %s already exists!' % filename)
    if not hostport:
        hostport = Env['data_server'] + ':' + Env['data_port']
    c = DataIO(hostport)
    return c.get(filename, query=query, savepath=savepath)


def getmd5db(filename):
    url_md5= EAS_DPS_CUS_url + "/EuclidXML?class_name=TestDataContainerStorage&Filename=%(filename)s&PROJECT=DSS" % vars()
    response=urllib.urlopen(url_md5)
    inp_xml=response.read()
    s1=inp_xml.find('<CheckSumValue>')
    s2=inp_xml.find('</CheckSumValue>')
    if s1>-1 and s2>-1 and s2>(s1+15):
        return inp_xml[s1+15:s2]
    return None


def messageIAL(command,filename,localfilename,exitcode,errormessage):
    m_type_1='''filename=%s\nfileuri=%s\nexitcode=%s\nmessage=%s\n'''
    m_type_2='''filename=%s\nstatus=%s\nmessage=%s\n'''
    m_type_retrieve='''{"filename":"%s","fileuri":"%s","exitcode":"%s","message":"%s"}'''
    m_type_store='''{"filename":"%s","fileuri":"%s","status":"%s","exitcode":"%s","message":"%s"}'''
    m_type_local='''{"filename":"%s","status":"%s","status_message":"%s","exitcode":"%s","message":"%s"}'''
    m_type_local_asy='''{"exitcode":"%s","message":"%s","result":[%s]
                    }
                      '''
    file_template='''{"filename":"%s","status":"%s","status_message":"%s"}'''
    message_str=''
    if command=='store':
        filename_local=filename.strip().replace("'","")
        if localfilename:
            fileuri=localfilename.strip().replace("'","")
        else:
            fileuri=filename_local
        filename_local=filename_local.split("/")[-1]
        if exitcode:
#           message_str = m_type_1 % (filename, localfilename,0,'')
            message_str=m_type_store % (filename_local,fileuri,"COMPLETED","True","null",)
        else:
            errormessage=errormessage.replace('"','').replace("'","").replace("{","").replace("}","")
            if errormessage.find("already exist")>-1:
                #check MD5
                md5_db = getmd5db(filename_local)
                if md5_db:
                    md5_local = None
                    with open(fileuri) as checkfile:
                        data_local = checkfile.read()
                        md5_local = hashlib.md5(data_local).hexdigest()
                    if md5_db == md5_local:
                        message_str=m_type_store % (filename_local,fileuri,"COMPLETED","True","File already exists in DSS")
                    else:
                        message_str=m_type_store % (filename_local,fileuri,"ERROR","False","File already exists in DSS")
                else:
                    message_str=m_type_store % (filename_local,fileuri,"ERROR","False","Cannot retrieve MD5 from EAS-DPS")
            else:
                message_str=m_type_store % (filename_local,fileuri,"ERROR","False", errormessage)
    elif command=='retrieve':
        filename_local=filename.strip().replace("'","")
        if localfilename:
            fileuri=localfilename.strip().replace("'","")
        else:
            fileuri=filename_local
        filename_local=filename_local.split("/")[-1]
        if exitcode:
#           message_str = m_type_1 % (filename, localfilename,0,'')
            message_str=m_type_retrieve % (filename_local,fileuri,"True","null",)
        else:
            errormessage=errormessage.replace('"','').replace("'","").replace("{","").replace("}","")
            message_str=m_type_retrieve % (filename_local,fileuri,"False", errormessage)
    elif command=='make_local' or command=='make_local_test':
        if exitcode:
            message_str=m_type_local % (filename.strip().replace("'",""),"COMPLETED","null","True","null")
        else:
            errormessage=errormessage.replace('"','').replace("'","").replace("{","").replace("}","")
            message_str=m_type_local % (filename.strip().replace("'",""),"ERROR",'null',"False",errormessage)
    elif command=='make_local_asy':
        if exitcode:
            content=errormessage.replace("u'","").replace("{","").replace("}","").replace("FAILED","ERROR").replace("FINISHED","COMPLETED").replace("RUNNING","EXECUTING").replace("STARTED","EXECUTING")
            files=content.split(",")
            files_content=[]
            try:
                for f_i in files:
                    f1,f2=f_i.split(":")
                    f1=f1.strip().replace("'","")
                    f2=f2.strip().replace("'","")
                    files_content.append(file_template % (f1,f2,'null'))
                message_str=m_type_local_asy % ("True","null",",\n".join(files_content))
            except Exception as e:
                message("ERROR in make_local_asy for file %s" % f_i)
                raise(e)
        else:
            errormessage=errormessage.replace('"','').replace("'","").replace("{","").replace("}","")
            message_str=m_type_local_asy % ("False",errormessage,"")
    elif command=='ping':
        errormessage=errormessage.replace('"','').replace("'","").replace("{","").replace("}","")
        message_str='''{exitcode:"%s",message:"%s"}''' % (exitcode,errormessage)
    elif command in ['dsstestget', 'dsstestconnection', 'dsstestnetwork','dssgetticket','dssinit','dssinitforce']:
        errormessage=errormessage.replace('"','').replace("'","").replace("{","").replace("}","")
        message_str='''{exitcode="%s",message:"%s"}''' % (exitcode,errormessage)
    else:
        message_str='''{exitcode="%s",message:"%s"}''' % ('False','Unknown command')
    message(message_str)
    return