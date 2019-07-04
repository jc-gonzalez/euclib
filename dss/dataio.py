import base64
import hashlib
import os
import pickle
import random
import shlex
import socket
import ssl
import stat
import subprocess
import time
import traceback
import uuid
from http.client import HTTPSConnection, HTTPConnection
from urllib.parse import urlparse, urlencode
from urllib.request import url2pathname

from dss.dssserver_client import message, __version__, Env, MapAction, Compressed_Exts, Decompressors, Compressors, \
    gpgencrypt, python_to_ascii, dataserver_result_to_dict


class DataIO(object):
    '''
    Class to provide data transfer between the server and client.
    '''
    _host = ''
    _port = 0
    _secure = True
    error_message = ''
    cookie ={}

    def myprint(self, level, text):
        self.textbuf.append(text)
        if level and not (self.debug & level):
            return
        if not self.silent:
            message(text)

    def removesecure(self):
        printsendheader = self.sendheader.copy()
        if 'password' in printsendheader:
            printsendheader['password'] = 'XXX'
        if 'authorization' in printsendheader:
            printsendheader['authorization'] = 'Authorization provided'
        if 'Authorization' in printsendheader:
            printsendheader['Authorization'] = 'Authorization provided'
        return printsendheader

    def __del__(self):
        #        if self.status and self.textbuf:
        #            for text in self.textbuf:
        #                message('DATA_IO: '+text)
        if hasattr(self,'open') and self.open:
            self.f.close()
            self.open = 0

    def __init__(self, host, **kwargs):
        port = kwargs.get('port', None)
        store_host = kwargs.get('store_host', None)
        store_port = kwargs.get('store_port', None)
        debug = kwargs.get('debug', 0)
        timeout = kwargs.get('timeout', None)
        data_path = kwargs.get('data_path', '')
        user_id = kwargs.get('user_id', '')
        sleep = kwargs.get('sleep', 30.0)
        dstid = kwargs.get('dstid', '')
        secure = kwargs.get('secure', True)
        certfile = kwargs.get('certfile', '')
        standard = kwargs.get('standard', False)
        looptime = kwargs.get('looptime', 1.0)
        logfile = kwargs.get('logfile', '')
        username = kwargs.get('username', '')
        password = kwargs.get('password', '')
        accessfile = kwargs.get('accessfile', '')
        cookie = kwargs.get('cookie', {})
        silent = kwargs.get('silent', False)
        # Use standard (i.e. defined by more important persons) HTTP methods
        self.machine_name = socket.gethostname()
        self.keepalive = True
        self.silent = silent
        self.standard = standard
        self.globalname = ''
        self.globalnames = []
        self.textbuf = []
        if dstid:
            self.dstid = dstid
        else:
            self.dstid = '%s' % (uuid.uuid4())
        self.version = __version__.split()[1]
        self.open = 0
        self.result = 0
        self.host_init = host
        if type(host) == type(()):
            self.host = host[0]
            self.port = host[1]
        elif port:
            self.host = host
            self.port = int(port)
        else:
            self.host, port = host.split(':')
            self.port = int(port)
        self.original_host = self.host
        self.allhosts = []
        for h in self.original_host.split(','):
            self.allhosts += socket.gethostbyname_ex(h)[2]
        self.host2 = ''
        self.port2 = 0
        self.timeout = timeout
        self.store_port = self.port
        self.store_host = self.host
        if store_port:
            self.store_port = int(store_port)
            if store_host:
                self.store_host = store_host
        elif store_host:
            hp = store_host.split(':')
            if len(hp) > 1:
                self.store_port = int(hp[1])
        self.f_extra = None
        self.server_id = ''
        self.server_caps = ''
        self.status = 0
        self.debug = debug
        self.autoclose = True
        self.buffer = ''
        self.buffer_length = 0
        self.read_buffer_size = 16 * 1024
        self.write_buffer_size = 16 * 1024
        self.action = "NONE"
        self.bcount = 0
        self.getpath = None
        self.cmd = None
        self.content_length = None
        self.content_type = ''
        if data_path and os.path.isdir(data_path):
            self.data_path = data_path
        else:
            self.data_path = None
        self.myprint(255, '__init__: self.data_path = %s' % (self.data_path))
        self.storecheck = False
        self.storekey = None
        if user_id:
            self.user_id = user_id
        elif 'database_user' in Env:
            self.user_id = Env['database_user']
        else:
            try :
                import pwd
                self.user_id = pwd.getpwuid(os.getuid())[0]
            except:
                self.user_id = '?'
        self.machine_id = socket.getfqdn()
        self.chksum = False
        self.check_md5sum = None
        self.check_sha1 = None
        self.sleep = sleep
        self.certfile = certfile
        if certfile:
            self.secure = True
        else:
            self.certfile = None
            self.secure = secure
        self.secure2 = self.secure
        self.secure3 = None
        self.store_secure = self.secure
        self.sendheader = {}
        self.recvheader = {}
        self.nextsend = False
        self.response = None
        self.sslcontext = None
        self.conn = None
        self.f = None
        self.url = None
        self.handle_handle = None
        self.username = username
        self.password = password
        self.authorization = ''
        self.looptime = looptime
        self.logfile = logfile
        self.client_cookie = {}
        if cookie:
            cookie['secure'] = True
            self.cookie = cookie.copy()
        try:
            self.sslcontext = ssl._create_unverified_context()
        except:
            self.sslcontext = None
            # Just to get the behaviour of older python versions

    def _set_data_path(self, data_path=None):
        if not data_path and 'data_path' in Env and Env['data_path']:
            data_path = Env['data_path']
        if data_path and os.path.isdir(data_path):
            self.data_path = data_path

    def _show(self):

        current_time = time.strftime('%B %d %H:%M:%S', time.localtime())

        print('%s %s _show: self.version             : %s' % (current_time, self.machine_name, self.version))
        print('%s %s _show: self.open                : %d' % (current_time, self.machine_name, self.open))
        print('%s %s _show: self.result              : %d' % (current_time, self.machine_name, self.result))
        print('%s %s _show: self.host                : %s' % (current_time, self.machine_name, self.host))
        print('%s %s _show: self.port                : %d' % (current_time, self.machine_name, self.port))
        print('%s %s _show: self.secure              : %d' % (current_time, self.machine_name, self.secure))
        print('%s %s _show: self.host2               : %s' % (current_time, self.machine_name, self.host2))
        print('%s %s _show: self.port2               : %d' % (current_time, self.machine_name, self.port2))
        print('%s %s _show: self.secure2             : %d' % (current_time, self.machine_name, self.secure2))
        print('%s %s _show: self.timeout             : %f' % (current_time, self.machine_name, self.timeout))
        print('%s %s _show: self.store_host          : %s' % (current_time, self.machine_name, self.store_host))
        print('%s %s _show: self.store_port          : %d' % (current_time, self.machine_name, self.store_port))
        print('%s %s _show: self.store_secure        : %d' % (current_time, self.machine_name, self.store_secure))
        print('%s %s _show: self.f_extra             : %d' % (current_time, self.machine_name, self.f_extra))
        print('%s %s _show: self.server_id           : %s' % (current_time, self.machine_name, self.server_id))
        print('%s %s _show: self.server_caps         : %s' % (current_time, self.machine_name, self.server_caps))
        print('%s %s _show: self.status              : %d' % (current_time, self.machine_name, self.status))
        print('%s %s _show: self.debug               : %d' % (current_time, self.machine_name, self.debug))
        print('%s %s _show: self.autoclose           : %d' % (current_time, self.machine_name, self.autoclose))
        print('%s %s _show: self.buffer              : %s' % (current_time, self.machine_name, self.buffer))
        print('%s %s _show: self.buffer_length       : %d' % (current_time, self.machine_name, self.buffer_length))
        print('%s %s _show: self.read_buffer_size    : %d' % (current_time, self.machine_name, self.read_buffer_size))
        print('%s %s _show: self.write_buffer_size   : %d' % (current_time, self.machine_name, self.write_buffer_size))
        print('%s %s _show: self.recvheader          : %s' % (current_time, self.machine_name, self.recvheader))
        print('%s %s _show: self.sendheader          : %s' % (current_time, self.machine_name, self.removesecure()))
        print('%s %s _show: self.action              : %s' % (current_time, self.machine_name, self.action))
        print('%s %s _show: self.bcount              : %d' % (current_time, self.machine_name, self.bcount))
        print('%s %s _show: self.getpath             : %s' % (current_time, self.machine_name, self.getpath))
        print('%s %s _show: self.content_length      : %d' % (current_time, self.machine_name, self.content_length))
        print('%s %s _show: self.data_path           : %s' % (current_time, self.machine_name, self.data_path))
        print('%s %s _show: self.user_id             : %s' % (current_time, self.machine_name, self.user_id))
        print('%s %s _show: self.machine_id          : %s' % (current_time, self.machine_name, self.machine_id))

    def _connect(self, host, port, secure):

        self.myprint(255, '_connect: %d %d %d %s %s' % (
            self.open, self.result, self.status, self.action, self.dstid))
        self.keepalive = self.keepalive and (host == self._host and port == self._port and secure == self._secure)
        self.bcount = 0
        self.buffer = ''
        self.buffer_length = 0
        self.result = 0
        self.status = 0
        self.recvheader = {}
        self.response = None
        securetry = False
        if self.action not in list(MapAction):
            raise Exception('%s %s _connect: no such action %s' % (
                time.strftime('%B %d %H:%M:%S', time.localtime()), self.machine_name, self.action))
        if secure:
            securetry = True
            if not self.keepalive:
                if self.sslcontext:
                    self.conn = HTTPSConnection(host, port, cert_file=self.certfile, timeout=self.timeout, context=self.sslcontext)
                else:
                    self.conn = HTTPSConnection(host, port, cert_file=self.certfile, timeout=self.timeout)
                self.myprint(255, '_connect: self.conn = %s' % (self.conn))
            try:
                if self.standard:
                    self.conn.request('POST', self.url, headers=self.sendheader)
                else:
                    self.conn.request(MapAction[self.action], self.url, headers=self.sendheader)
            except Exception as e:
                self.myprint(255, '_connect: error in secure request to %s:%d %s' % (host, port, e))
                if self.conn and hasattr(self.conn,'close'):
                    self.conn.close()
                self._host = ''
                self._port = 0
                secure = False
                self.keepalive = False
        self.secure3 = secure
        if not secure:
            if not self.keepalive:
                self.conn = HTTPConnection(host, port, timeout=self.timeout)
                self.myprint(255, '_connect: self.conn = %s' % (self.conn))
            try:
                if self.standard:
                    self.conn.request('POST', self.url, headers=self.sendheader)
                else:
                    self.conn.request(MapAction[self.action], self.url, headers=self.sendheader)
            except Exception as e:
                self.result = 1
                self.myprint(255, '_connect: error in request to %s:%d %s' % (host, port, e))
                if self.conn and hasattr(self.conn,'close'):
                    self.conn.close()
                self._host = ''
                self._port = 0
                self.keepalive = False
        if not secure and self.result and not securetry:
            securetry = True
            if not self.keepalive:
                if self.sslcontext:
                    self.conn = HTTPSConnection(host, port, cert_file=self.certfile, timeout=self.timeout, context=self.sslcontext)
                else:
                    self.conn = HTTPSConnection(host, port, cert_file=self.certfile, timeout=self.timeout)
                self.myprint(255, '_connect: self.conn = %s' % (self.conn))
            try:
                self.secure3 = secure = True
                if self.standard:
                    self.conn.request('POST', self.url, headers=self.sendheader)
                else:
                    self.conn.request(MapAction[self.action], self.url, headers=self.sendheader)
            except Exception as e:
                self.myprint(255, '_connect: error in secure request to %s:%d %s' % (host, port, e))
                if self.conn and hasattr(self.conn,'close'):
                    self.conn.close()
                self._host = ''
                self._port = 0
                self.result = 1
                self.keepalive = False
        if not self.result:
            if not self.keepalive:
                self._host = host
                self._port = port
                self._secure = secure
            nextsendwas = self.nextsend
            self.myprint(255, '_connect: sendheader = %s, chksum = %s, nextsend = %s' % (self.removesecure(), self.chksum, self.nextsend))
            if self.nextsend:
                self.nextsend = False
                rcount = 0
                try:
                    if self.chksum:
                        self.check_md5sum = hashlib.md5()
                    data = self.f.read(self.write_buffer_size)
                    while data:
                        self.bcount += len(data)
                        if self.chksum:
                            self.check_md5sum.update(data)
                        rcount += 1
                        while data:
                            sent = self.conn.sock.send(data)
                            data = data[sent:]
                        data = self.f.read(self.write_buffer_size)
                    self.f.close()
                    self.open = 0
                    if self.chksum:
                        self.check_md5sum = self.check_md5sum.hexdigest()
                        self.chksum = False
                except Exception as e:
                    self.myprint(255, '_connect: rcount = %(rcount)d, exception = %(e)s' % vars())
                    self.result = 1
            try:
                self.response = self.conn.getresponse()
                self.keepalive = not self.response.will_close
            except Exception as e:
                if self.response and hasattr(self.response, 'close'):
                    self.response.close()
                if self.conn and hasattr(self.conn, 'close'):
                    self.conn.close()
                self.myprint(0, '_connect: error in response from %s:%d (%s)' % (host, port, e))
                self.nextsend= nextsendwas
                self.result = 1
                self._host = ''
                self._port = 0


    def _respond(self):
        def respond_200_get():
            if self.open == 3:
                self.myprint(1, '_respond: writing headers for original client')
                self.handle_handle.send_response(200)
                if self.content_type:
                    self.handle_handle.send_header("Content-Type", self.content_type)
                if self.content_length:
                    self.handle_handle.send_header("Content-Length", self.content_length)
                if self.client_cookie:
                    expires = ''
                    if 'expires' in self.cookie:
                        expires = self.cookie['expires']
                    for k,v in self.client_cookie.items():
                        if k not in ['expires']:
                            cookie_string = '%s=%s;expires=%s;' % (k,v,expires)
                            self.handle_handle.send_header("Set-Cookie", cookie_string)
                self.handle_handle.end_headers()
                self.open = 1
            data = self.response.read(self.read_buffer_size)
            self.myprint(64, '__respond: initially got %d bytes' % (len(data)))
            while not self.result and data:
                if self.content_length and (self.bcount + len(data)) > self.content_length:
                    # this should never occur, since self.response.read takes automatically care of this
                    self.myprint(64, '_respond: got %d, needed %d!' % (self.bcount, self.content_length))
                    self.result = -2
                    break
                if self.open:
                    try:
                        self.f.write(data)
                    except Exception as e:
                        if not self.f_extra:
                            self.result = -1
                        self.open = 0
                        self.myprint(255, '_respond: Exception "%s:' % (e))
                        try:
                            self.myprint(255, '_respond: '+traceback.format_exc())
                        except:
                            self.myprint(255, '_respond: No traceback possible!')
                        self.myprint(255, '_respond: Connection with client broken!')
                if self.f_extra:
                    self.f_extra.write(data)
                self.bcount += len(data)
                self.myprint(128, '_respond: writing : %d' % len(data))
                if self.buffer_length:
                    self.buffer = self.buffer + data
                data = self.response.read(self.read_buffer_size)
                if data == None:
                    self.myprint(128, '_respond: got None!')
                    self.result = -2
                elif len(data):
                    self.myprint(128, '_respond: got %d bytes!' % (len(data)))
                else:
                    self.myprint(128, '_respond: zero bytes!')
                    if not self.result and self.content_length and self.bcount < self.content_length:
                        self.myprint(64, '_respond: got %d, needed %d!' % (self.bcount, self.content_length))
                        self.result = -2
            if not self.open and self.f_extra and not self.result:
                self.result = -1
            if self.response and hasattr(self.response, 'close'):
                self.response.close()

        get_actions = ["GETLOCALSTATS", "GETGROUPSTATS", "GETTOTALSTATS", "LOCATE", "LOCATEFILE", "LOCATELOCAL",
                       "LOCATEREMOTE", "MD5SUM", "PING", "SHA1SUM", "SIZE", "STAT", "DSSTESTGET", "DSSTESTCONNECTION",
                       "DSSTESTNETWORK", "DSSMAKELOCAL", "DSSMAKELOCALASY", "DSSINIT", "DSSINITFORCE", "DSSGETTICKET",
                       "DELETE",]
        self.myprint(255, '_respond: %d %d %d %s %s' % (self.open, self.result, self.status, self.action, self.dstid))
        if self.result:
            if self.conn and hasattr(self.conn, 'close'):
                self.conn.close()
            return
        self.status = self.response.status
        self.recvheader = {}
        for k, v in dict(self.response.getheaders()).items():
            self.recvheader[k.lower()] = v
        self.reason = self.response.reason
        self.myprint(255, '_respond: recvheader = %s' %self.recvheader)
        self.myprint(255, '_respond: status = %d' % self.status)
        self.myprint(255, '_respond: reason = %s' % self.reason)
        if 'content-type' in self.recvheader:
            self.content_type = self.recvheader['content-type']
        if 'content-length' in self.recvheader:
            self.content_length = int(self.recvheader['content-length'])
        else:
            self.content_length = None
        if 'set-cookie' in self.recvheader:
            cookie_items = []
            for t_res in self.response.getheaders():
                if len(t_res)==2:
                    if t_res[0].lower()=='set-cookie':
                        cookie_item = t_res[1].replace(";,",";").split(";")
                        cookie_items.extend(cookie_item)
            for item in cookie_items:
                if item:
                    item_p = item.split("=")
                    if len(item_p)==2:
                        self.cookie[item_p[0].strip()] = item_p[1].strip()
                    elif len(item_p)==1 and item_p[0]:
                        self.cookie[item_p[0].strip()]
        if self.status == 200:
            self.result = 0
            if self.action in get_actions:
                if self.content_length == None:
                    raise Exception('server did not specify "Content-Length"!')
                self.buffer_length = self.content_length
                self.buffer = self.response.read(self.buffer_length)
                while len(self.buffer) < self.content_length:
                    self.buffer += self.response.read(self.buffer_length - len(self.buffer))
                if type(b'') != type(''):
                    self.buffer = str(self.buffer, "utf-8")
                if self.response and hasattr(self.response, 'close'):
                    self.response.close()
            elif self.action in ["STORE", "DSSSTORE"]:
                self.nextsend = True
                if 'storecheck' in self.recvheader and 'storekey' in self.recvheader:
                    self.storecheck = self.recvheader['storecheck'] == 'OK'
                    self.storekey = self.recvheader['storekey']
                    self.chksum = True
                self.response.fp.close()
            elif self.action in ["GET", "GETANY", "GETEXACT", "GETLOCAL", "GETLOG", "GETREMOTE", "DSSGET"]:
                if 'content-length' not in self.recvheader:
                    self.myprint(255, '_respond: no content-length in recvheader')
                    self.result = -2
                else:
                    respond_200_get()
            elif self.action in ["HEAD", "HEADLOCAL"]:
                self.result = 0
                #self.response.close()
        elif self.status == 201:
            self.open = 2
        elif self.status == 204:
            self.result = 0
            if self.action in ["STORE", "STORED", "DSSSTORE", "DSSSTORED"]:
                self.open = 2
                if 'datapath' in self.recvheader and 'storekey' in self.recvheader:
                    self.storecheck = True
                    self.storekey = self.recvheader['storekey']
                    datapath = os.path.join(self.data_path, self.recvheader['datapath'])
                    self.check_md5sum = hashlib.md5()
                    self.check_sha1 = hashlib.sha1()
                    fdatapath = open(datapath, 'ab')
                    if not fdatapath:
                        self.result = -1
                    if not self.result:
                        data = self.f.read(self.write_buffer_size)
                        while data:
                            self.bcount += len(data)
                            self.check_md5sum.update(data)
                            self.check_sha1.update(data)
                            fdatapath.write(data)
                            data = self.f.read(self.write_buffer_size)
                        fdatapath.close()
                    self.check_md5sum = self.check_md5sum.hexdigest()
                    self.check_sha1 = self.check_sha1.hexdigest()
                    self.open = 1
            elif 'link-name' in self.recvheader:
                linkname = os.path.join(self.data_path, 'xdata', self.recvheader['link-name'])
                localname = self.f.name
                self.f.close()
                self.f = None
                self.open = 0
                os.remove(localname)
                os.symlink(linkname, localname)
        elif self.status in [301, 302, 303, 307]:
            if 'location' in self.recvheader:
                if self.status in [301, 302, 307]:
                    self.result = 2
                elif self.status in [303]:
                    self.result = 3
                redirhost = urlparse(self.recvheader['location'])
                self.myprint(255, '_respond: redirhost = %s status =  %d' % (redirhost, self.status))
                h, p = redirhost[1].split(':')
                self.host2 = h
                if p == '':
                    self.port2 = 80
                else:
                    self.port2 = int(p)
                if redirhost[0] == 'https':
                    self.secure2 = True
                else:
                    self.secure2 = False
                if self.status == 301:
                    self.store_port = self.port2
                    self.store_host = self.host2
                if self.status == 303:
                    inext = ''
                    ouext = ''
                    self.cmd = None
                    for ext in Compressed_Exts:
                        if ext and redirhost[2].endswith(ext):
                            inext = ext
                        if ext and self.getpath.endswith(ext):
                            ouext = ext
                    self.getpath = url2pathname(redirhost[2])
                    if inext and not ouext:
                        self.cmd = Decompressors[inext]
                    elif not inext and ouext:
                        self.cmd = Compressors[ouext]
                    elif inext and ouext:
                        self.cmd = Decompressors[inext] + '| ' + Compressors[ouext]
                    self.myprint(255, '_respond: cmd = %s getpath = %s' % (self.cmd, self.getpath))
            else:
                self.result = 1
            self.myprint(255, '_respond: result = %d status = %d' % (self.result, self.status))
        elif self.status in [400, 404, 501]:
            self.result = 1
        elif self.status == 503:
            self.result = 1
            self.myprint(0, '_respond: Server too busy to handle request! [dstid = %s]' % (self.dstid))
            self.response.fp.close()
            sleeptime = 60.0
            if 'sleep-time' in self.recvheader['sleep-time']:
                time.sleep(float(self.recvheader['sleep-time']))
            return
        else:
            self.result = 1
            self.myprint(255, '_respond: result = %d status = %d' % (self.result, self.status))
#        self.response.fp.close()
#        if self.response and hasattr(self.response, 'close'): self.response.close()
#        if self.conn and hasattr(self.conn, 'close'): self.conn.close()
        if self.open == 2 or self.nextsend:
            self.myprint(255, '_respond: self.open = %s self.nextsend = %s' % (self.open, self.nextsend))
        elif self.open:
            if not self.autoclose:
                self.open = 0
            elif not self.result or self.cmd:
                self.f.close()
                self.open = 0


    def _setup(self, action, path, **kw):
        '''
        sets up the connection string and connection
        '''
        host = kw.get('host', None)
        port = kw.get('port', None)
        secure = kw.get('secure', None)
        query = kw.get('query', None)
        fileuri = kw.get('fileURI', '')
        jobid = kw.get('jobid', '')
        use_data_path = kw.get('use_data_path', True)
        defaulthp = self.host == None and self.port == None
        if not host:
            host = self.host
        if not port:
            port = self.port
        self.secure3 = None
        if not secure:
            secure = self.secure
        self.myprint(255, '_setup: host:port = %s:%d' % (host, port))
        self.action = action
        if action in ["STORE","DSSSTORE"]:
            head, path = os.path.split(path)
        if action != "DELETE" and os.path.isabs(path):
            path = path[len(os.path.sep):]
        if action.startswith("GET"):
            self.getpath = path
        rest = ''
        self.chksum = False
        self.sendheader = {}
        if kw:
            for k, v in kw.items():
                if k not in ['host', 'port', 'secure', 'query', 'use_data_path']:
                    if type(v) == type(b''):
                        v = v.decode()
                    self.sendheader[k] = '%s' % (v)
        self.sendheader['Author'] = 'K.G. Begeman'
        self.sendheader['Client'] = 'httplib'
        self.sendheader['Client-Version'] = '%s' % (self.version)
        self.sendheader['DSTID'] = '%s' % (self.dstid)
        if self.recvheader and 'ProxyHost' in self.recvheader:
            hp_r = self.recvheader['ProxyHost'].split(':')
            if len(hp_r) == 2:
                h = hp_r[0]
                p = int(hp_r[1])
#            elif len(hp_r)==1:
#                h=hp_r[0]
#                p=int(80)
            else:
                h = hp_r[0]
                p = int(80)
            self.sendheader['Host'] = '%s:%d' % (h, p)
            host = h
            port = p
        else:
            if self.host and not self.host[0].isdigit():
                self.sendheader['Host'] = '%s:%d' % (self.host, port)
            else:
                self.sendheader['Host'] = '%s:%d' % (socket.getfqdn(host), port)
        self.sendheader['TimeStamp'] = '%s' % (time.strftime('%Y-%m-%dT%H:%M:%S'))
        self.sendheader['Action'] = action
        self.sendheader['pragma'] = action
#        print('DataIO cookie:',self.cookie)
        nocookie = True
        if self.cookie and 'server' in self.cookie and self.cookie['server']==self.host_init and action not in ['DSSINIT','DSSINITFORCE']:
            cookie_string = ";".join(["{0}={1}".format(k, v) for k, v in self.cookie.items()])
            self.sendheader['Cookie'] = '%s' % (cookie_string)
            nocookie = False
        if nocookie and self.username and self.password:
            self.sendheader['Authorization'] = 'Basic %s' % (base64.b64encode(b"%s:%s" % (self.username.encode('utf-8'), self.password.encode('utf-8'))).decode('utf-8'))
        if self.standard:
            queryaction = urlencode({'ACTION':action})
            if query:
                rest = '?%s&%s' % (queryaction, query)
            else:
                rest = '?%s' % (queryaction)
        elif query:
            rest = '?%s' % (query)
        if action in ["STORE", "DSSSTORE"]:
            if self.nextsend:
                self.chksum = True
                self.sendheader['RECEIVE'] = 'OK'
            else:
                self.sendheader['RECEIVE'] = 'NOT OK'
            self.sendheader['StoreCheck'] = 'OK'
        if action in ["STORE", "DSSSTORE"] and self.open:
            if self.sendheader['RECEIVE'] == 'OK':
                self.content_length = os.fstat(self.f.fileno())[6]
                self.sendheader['Content-Length'] = '%d' % (self.content_length)
            else:
                self.sendheader['Content-Length'] = '0'
        else:
            self.content_length = 0
        if self.data_path and use_data_path:
            self.sendheader['Data-Path'] = '%s' % (self.data_path)
        if action in ["STORED", "DSSSTORED"] and self.storekey:
            self.nextsend = False
            self.sendheader['StoreKey'] = '%s' % (self.storekey)
            # if self.check_md5sum:
            self.sendheader['MD5SUM'] = '%s' % (self.check_md5sum)
            self.sendheader['SHA1'] = '%s' % (self.check_sha1)
            self.sendheader['BCOUNT'] = '%s' % (self.bcount)
        if self.user_id:
            self.sendheader['User-ID'] = '%s' % (self.user_id)
        if self.machine_id:
            self.sendheader['Machine-ID'] = '%s' % (self.machine_id)
        if fileuri:
            self.sendheader['URI'] = '%s' % (fileuri)
        if action == "DSSGETLOG" and jobid:
            self.sendheader['jobid'] = '%s' % (jobid)
        self.url = '/%s%s' % (path, rest)
        self.keepalive = self.keepalive and (self._host and self._port) and defaulthp
        if not self.keepalive:
            hosts = list(set(socket.gethostbyname_ex(host)[2]))
            # get hosts and remove duplicates
            self.myprint(255, '_setup: hosts = %s' % hosts)
            if len(hosts) > 1:
                hosts.sort()
                l = len(hosts)
                shift = random.randrange(0, l)
                hs = [hosts[(shift+i)%l] for i in range(l)]
                hosts = hs
            for h in hosts:
                self.status = 503
                while self.status == 503:
                    self._connect(h, port, secure)
                    if not self.result:
                        self._respond()
                    else:
                        break
                    #if self.status == 503: time.sleep(60.0)
                if self.result in [0, 2, 3]:
                    break
        else:
            self._connect(self._host, self._port, self._secure)
            if not self.result:
                self._respond()


    def delete(self, path='', savepath=None, fd=None):
        '''
        delete removes a file from a server, i.e. it moves the file to the
        ddata directory on the servers disk. The file must exist on the
        contacted server, the path must be returned from a locate call.

        path    = name of the file as returned by locate.
        host    = optional host name where the file resides.
        port    = optional port number of the server where the file resides.
        '''
        def deleteError():
            """
            print out an error
            """
            print_recvheader = self.recvheader
            print_sendheader = self.removesecure()
            raise IOError("%s %s delete: Error deleting file on %s:%d [DSTID=%s], internal error %s, recvheader=%s, sendheader=%s" % (
                time.strftime('%B %d %H:%M:%S', time.localtime()), self.machine_name, self._host, self._port, self.dstid, self.error_message, print_recvheader, print_sendheader))

        self._setup("DELETE", path, host=self.host, port=self.port)
        r = ''
        if self.result:
            deleteError()
        elif self.buffer_length:
            r = self.buffer[:self.buffer_length]
            return True
        else:
            r = ''
            deleteError()
        return False



    def getlog(self, path='', defaultkey='', host=None, port=None, gpghomedir=None):
        '''
        getlog retrieves the log file from the server.

        path    = name of the file the logdata will be store in.
        host    = optional host name where the file resides.
        port    = optional port number of the server where the file resides.
        '''

        text = []
        r = gpgencrypt(['GETLOG'], defaultkey, fout=None, lout=text, gpghomedir=gpghomedir)
        if r:
            return False
        self.autoclose = True
        self.f = open(path + '_INCOMPLETE', "wb")
        if self.f:
            self.open = 1
            ptext = python_to_ascii(text)
            self._setup("GETLOG", path, host=host, port=port, Validation=ptext, use_data_path=False)
            if self.open:
                self.f.close()
                self.open = 0
            if self.result:
                if os.path.exists(path + '_INCOMPLETE'):
                    os.remove(path + '_INCOMPLETE')
            else:
                if os.path.exists(path + '_INCOMPLETE'):
                    os.rename(path + '_INCOMPLETE', path)
                return True
        return False

    def restart(self, defaultkey='', host=None, port=None, gpghomedir=None):
        text = []
        r = gpgencrypt(['RESTART'], defaultkey, fout=None, lout=text, gpghomedir=gpghomedir)
        if r:
            return False
        ptext = python_to_ascii(text)
        self._setup("RESTART", "restart", host=host, port=port, Validation=ptext)
        if self.result:
            r = False
        else:
            r = True
        return r

    def md5sum(self, path='', host=None, port=None):
        '''
        md5sum calculates the md5 check sum of a file. The file must exist on the
        contacted server, the path must be returned from a locate call.

        path    = name of the file as returned by locate.
        host    = optional host name where the file resides.
        port    = optional port number of the server where the file resides.
        '''

        self.open = 0
        self._setup("MD5SUM", path, host=host, port=port)
        if self.result:
            r = None
        elif self.buffer_length:
            r = self.buffer[:self.buffer_length]
        else:
            r = ''
        return r

    def sha1sum(self, path='', host=None, port=None):
        '''
        md5sum calculates the sha1 check sum of a file. The file must exist on the
        contacted server, the path must be returned from a locate call.

        path    = name of the file as returned by locate.
        host    = optional host name where the file resides.
        port    = optional port number of the server where the file resides.
        '''

        self.open = 0
        self._setup("SHA1SUM", path, host=host, port=port)
        if self.result:
            r = None
        elif self.buffer_length:
            r = self.buffer[:self.buffer_length]
        else:
            r = ''
        return r

    def size(self, path='', host=None, port=None):
        '''
        size calculates the size of a file. The file must exist on the
        contacted server, the path must be returned from a locate call.

        path    = name of the file as returned by locate.
        host    = optional host name where the file resides.
        port    = optional port number of the server where the file resides.
        '''

        self.open = 0
        self._setup("SIZE", path, host=host, port=port)
        if self.result:
            r = None
        elif self.buffer_length:
            r = self.buffer[:self.buffer_length]
        else:
            r = ''
        return r

    def stat(self, path='', host=None, port=None):
        '''
        stat returns the stat tuple a file. The file must exist on the
        contacted server, the path must be returned from a locate call.

        path    = name of the file as returned by locate.
        host    = optional host name where the file resides.
        port    = optional port number of the server where the file resides.
        '''

        self.open = 0
        self._setup("STAT", path, host=host, port=port)
        if self.result:
            r = None
        elif self.buffer_length:
            r = pickle.loads(url2pathname(self.buffer[:self.buffer_length]))
        else:
            r = ()
        return r

    def getstats(self, mode='LOCAL'):
        '''
        get local stats
        '''
        self.open = 0
        path = 'dummy'
        if mode in ['GLOBAL', 'TOTAL']:
            self._setup("GETTOTALSTATS", path, host=self.host, port=self.port)
        elif mode == 'GROUP':
            self._setup("GETGROUPSTATS", path, host=self.host, port=self.port)
        else:
            self._setup("GETLOCALSTATS", path, host=self.host, port=self.port)
        if self.result:
            r = None
        elif self.buffer_length:
            r = self.buffer[:self.buffer_length].split('<>')
        else:
            r = []
        return r

    def _locateit(self, path, local=False, remote=False):

        self.open = 0
        if local and remote:
            self._setup("LOCATE", path, host=self.host, port=self.port)
        elif not local and not remote:
            self._setup("LOCATEFILE", path, host=self.host, port=self.port)
        elif local and not remote:
            self._setup("LOCATELOCAL", path, host=self.host, port=self.port)
        elif not local and remote:
            self._setup("LOCATEREMOTE", path, host=self.host, port=self.port)
        if self.result:
            if self.status == 404:
                r = []
            else:
                r = None
        elif self.buffer_length:
            r = self.buffer[:self.buffer_length].split('<>')
        else:
            r = []
        return r

    def locate(self, path=''):
        '''
        locate locates a file, i.e. returns the url of the server
        where the specified file resides. All data servers are probed
        for the file.

        path    = name of the file
        '''

        return self._locateit(path, local=True, remote=True)

    def locatefile(self, path=''):
        '''
        locatelocal locates a file, i.e. returns the url of the server
        where the specified file resides. Only the addressed dataserver
        is probed.

        path    = name of the file
        '''

        return self._locateit(path, local=False, remote=False)

    def locatelocal(self, path=''):
        '''
        locatelocal locates a file, i.e. returns the url of the server
        where the specified file resides. Only the local dataservers
        are probed.

        path    = name of the file
        '''

        return self._locateit(path, local=True, remote=False)

    def locateremote(self, path=''):
        '''
        locateremote locates a file, i.e. returns the url of the server
        where the specified file resides. Only remote dataservers are
        probed.

        path    = name of the file
        '''

        return self._locateit(path, local=False, remote=True)

    def testfile(self, path=''):
        '''
        testfile tests whether a file exists on the server

        path    = name of the file
        '''
        self.open = 0
        self._setup("TESTFILE", path, host=self.host, port=self.port)
        if self.result == 0 and self.status == 204:
            return True
        else:
            return False

    def testcache(self):
        '''
        testcache tests whether the server is allowed to cache files
        '''
        self.open = 0
        self._setup("TESTCACHE", 'testcache', host=self.host, port=self.port)
        if self.result == 0:
            return True
        else:
            return False

    def teststore(self):
        '''
        teststore tests whether the server is allowed to store files
        '''
        self.open = 0
        self._setup("TESTSTORE", 'teststore', host=self.host, port=self.port)
        if self.result == 0 and self.status == 204:
            return True
        else:
            return False

    def _getit(self, **kwargs):
        '''
        _getit handles the retrieving of files from local or remote servers

        path    = name of the file
        local   = local server (True) or only remote (False)
        remote  = remote server (True) or local server (False)
        handle  = handle to the DataRequestHandler
        extra   = extra fd to write to
        query   = extra url query
        savepath= name of file where to store the retrieved data [name of originalfile]
        exact   = exact location of file is given/wanted
        '''
        path = kwargs.get('path', None)
        fd = kwargs.get('fd', None)
        local = kwargs.get('local', False)
        remote = kwargs.get('remote', True)
        exact = kwargs.get('exact', False)
        handle = kwargs.get('handle', None)
        extra = kwargs.get('extra', None)
        raise_exception = kwargs.get('raise_exception', False)
        query = kwargs.get('query', None)
        savepath = kwargs.get('savepath', None)

#        print("path:",path)
        kw = {}

        for kwkey, kwvalue in kwargs.items():
            if kwkey not in ['path']:
                kw[kwkey] = kwvalue

        results = []
        if type(path) == type([]):
            paths = path
        else:
            paths = [path]
        for thispath in paths:
            if exact:
                action = "GETEXACT"
            elif local:
                if remote:
                    if handle or fd or query:
                        action = "GET"
                    else:
                        action = "GETANY"
                else:
                    action = "GETLOCAL"
            else:
                action = "GETREMOTE"
            action="DSSGET"
            use_data_path = False
            if extra:
                self.f_extra = extra
            if handle:
                self.autoclose = False
                self.f = handle.wfile
                self.handle_handle = handle
                self.open = 3
                self._setup(action, thispath, **kw)
                self.myprint(255, '_getit: result = %d' % self.result)
                while self.result > 1 and not exact:
                    self.open = 3
                    self._setup(action, thispath, **kw)
                    self.myprint(255, '_getit: result = %d' % self.result)
                self.handle_handle = None
                self.open = 0
                lpath = None
            else:
                if fd:
                    self.autoclose = False
                    if hasattr(fd, 'name'):
                        lpath = fd.name
                    else:
                        lpath = None
                    self.f = fd
                else:
                    self.autoclose = True
                    if savepath:
                        lpath = savepath
                    else:
                        head, tail = os.path.split(thispath)
                        if tail == '':
                            lpath = head
                        else:
                            lpath = tail
                    if not os.path.exists(lpath):
                        try:
                            self.f = open(lpath + '_INCOMPLETE', "wb")
                            self.myprint(255, '_getit: OPEN ' + lpath + '_INCOMPLETE')
                            if not extra:
                                use_data_path = True
                        except Exception as e:
                            raise IOError("%s %s _getit: Error opening file on %s:%d [DSTID=%s], file %s, internal error %s " % (
                                time.strftime('%B %d %H:%M:%S', time.localtime()), self.machine_name, self._host, self._port, self.dstid, lpath+'_INCOMPLETE', str(e)))
                    else:
                        self.f = None
                if self.f:
                    self.open = 1
                    self._setup(action, thispath, **kw)
                    self.myprint(255, '_getit: _setup result = %d' % self.result)
                    if self.result == 0 and self.status == 204 and use_data_path:
                        self.autoclose = True
                    self.myprint(255, '_getit: result = %d' % self.result)
                    while self.result > 1 and not exact:
                        if self.open:
                            self.f.seek(0)
                            self.f.truncate()
                        elif self.autoclose and lpath:
                            if self.result == 3:
                                self.cmd = subprocess.Popen(shlex.split(self.cmd), stdin=subprocess.PIPE, stdout=open(lpath + '_INCOMPLETE', "wb"))
                                self.f = self.cmd.stdin
                                self.myprint(255, '_getit: POPEN %s > %s' % (self.cmd, lpath + '_INCOMPLETE'))
                            else:
                                try:
                                    self.f = open(lpath + '_INCOMPLETE', "wb")
                                except Exception as e:
                                    raise IOError("%s %s _getit: Error opening file on %s:%d [DSTID=%s], file %s, internal error %s " % (
                                      time.strftime('%B %d %H:%M:%S', time.localtime()), self.machine_name, self._host, self._port, self.dstid, lpath+'_INCOMPLETE', str(e)))
                        self.open = 1
                        if self.result == 3:
                            self._setup("GET", self.getpath, **kw)
                        else:
                            self._setup(action, thispath, **kw)
                        self.myprint(255, '_getit: result = %d' % self.result)
                else:
                    self.open = 0
                    self.result = 0
                if self.result:
#                    print(self.result, lpath)
                    self._clear(path=lpath)
                    if raise_exception:
                        raise IOError("%s %s _getit: Error retrieving remote file %s from %s:%d [DSTID=%s]" % (
                            time.strftime('%B %d %H:%M:%S', time.localtime()), self.machine_name, thispath, self._host, self._port, self.dstid))
            if self.open:
                self.f.close()
                self.open = 0
            if self.cmd:
                if hasattr(self.cmd, 'wait'):
                    retcode = self.cmd.wait()
                    if not self.result:
                        self.result = retcode
                self.cmd = None
            if self.result:
                if self.autoclose and lpath and os.path.exists(lpath + '_INCOMPLETE'):
                    self.myprint(255, '_getit: removing "%s"' % (lpath + '_INCOMPLETE'))
                    os.remove(lpath + '_INCOMPLETE')
                self.autoclose = True
                results.append(False)
            else:
                if self.autoclose and lpath and os.path.exists(lpath + '_INCOMPLETE'):
                    self.myprint(255, '_getit: renaming "%s"' % (lpath + '_INCOMPLETE'))
                    os.rename(lpath + '_INCOMPLETE', lpath)
                self.autoclose = True
                results.append(True)
        if len(paths) == 1:
            return results[0]
        return results

    def head(self, path=None, query=None):
        self._setup("HEAD", path, host=self.host, port=self.port, query=query)
        if self.result == 2:
            self._setup("HEAD", path, host=self.host2, port=self.port2, secure=self.secure, query=query)
        if self.result == 0:
            return self.recvheader
        else:
            return None

    def headlocal(self, path=None, query=None):
        self._setup("HEADLOCAL", path, host=self.host, port=self.port, query=query)
        if self.result == 0:
            return self.recvheader
        else:
            return None

    def get(self, **kwargs):
        '''
        get obtains the file from a remote server (see _getit)
        '''
        path = kwargs.get('path', None)
        fd = kwargs.get('fd', None)
        handle = kwargs.get('handle', None)
        extra = kwargs.get('extra', None)
        raise_exception = kwargs.get('raise_exception', True)
        query = kwargs.get('query', None)
        savepath = kwargs.get('savepath', None)
        client_cookie = kwargs.get('client_cookie', {})
        if client_cookie:
            self.client_cookie = client_cookie.copy()
        return self._getit(path=path, fd=fd, local=True, remote=True, exact=False, handle=handle, extra=extra, raise_exception=raise_exception, query=query, savepath=savepath)

    def getlocal(self, **kwargs):
        '''
        getlocal obtains the file from a local server (see _getit)
        '''
        path = kwargs.get('path', None)
        fd = kwargs.get('fd', None)
        handle = kwargs.get('handle', None)
        extra = kwargs.get('extra', None)
        raise_exception = kwargs.get('raise_exception', False)
        query = kwargs.get('query', None)
        savepath = kwargs.get('savepath', None)
        return self._getit(path=path, fd=fd, local=True, remote=False, handle=handle, extra=extra, raise_exception=raise_exception, query=query, savepath=savepath)

    def getremote(self, **kwargs):
        '''
        getlocal obtains the file from a local server (see _getit)
        '''
        path = kwargs.get('path', None)
        fd = kwargs.get('fd', None)
        handle = kwargs.get('handle', None)
        extra = kwargs.get('extra', None)
        raise_exception = kwargs.get('raise_exception', False)
        query = kwargs.get('query', None)
        savepath = kwargs.get('savepath', None)
        return self._getit(path=path, fd=fd, remote=False, handle=handle, extra=extra, raise_exception=raise_exception, query=query, savepath=savepath)

    def getexact(self, **kwargs):
        '''
        getlocal obtains the file from a local server (see _getit)
        '''
        path = kwargs.get('path', None)
        fd = kwargs.get('fd', None)
        handle = kwargs.get('handle', None)
        extra = kwargs.get('extra', None)
        raise_exception = kwargs.get('raise_exception', False)
        query = kwargs.get('query', None)
        savepath = kwargs.get('savepath', None)
        return self._getit(path=path, fd=fd, remote=False, exact=True, handle=handle, extra=extra, raise_exception=raise_exception, query=query, savepath=savepath)

    def register(self, path='', validation=''):
        '''
        register gets a dataserver to register a file which is already
        in one of the dataserver directories.

        path    = path to the file (w.r.t. the working directory)
        '''
        self.open = 0
        self._setup("REGISTER", path, host=self.host, port=self.port, Validation=validation)
        if self.result == 0 and self.status == 200:
            return True
        else:
            return False

    def release(self, validation=''):
        '''
        release gets a dataserver to release the port the server is listening on
        '''
        self.open = 0
        self._setup("RELEASE", '/dummy', host=self.host, port=self.port, Validation=validation)
        if self.result == 0 and self.status == 200:
            return True
        else:
            return False

    def takeover(self, validation='', newport='', certfile=''):
        '''
        takeover gets a dataserver to take over the port the current server is listening on
        '''
        if not certfile:
            certfile = self.certfile
        self.open = 0
        query = ''
        if certfile:
            query = urlencode({'NEWPORT': newport, 'CERTFILE': certfile})
        else:
            query = urlencode({'NEWPPORT': newport})
        self._setup("TAKEOVER", '/dummy', host=self.host, port=self.port, Validation=validation, Newport=newport, certfile=certfile)
        if self.result == 0 and self.status == 200:
            return True
        else:
            return False


    def cachefile(self, path=''):
        '''
        cachefile requests a caching server to cache a file

        path    = name of the file
        '''
        self.open = 0
        self._setup("CACHEFILE", path, host=self.host, port=self.port)
        if self.result == 0 and self.status == 204:
            return True
        else:
            return False


    def mirrorput(self, path='', port=8000, directory=''):
        '''
        mirrorput make the data server retrieve file path to its sdata directory

        path        = path to local file
        port        = port local ds listens on
        directory   = change the directory where the file should be mirrored
        '''
        fs = os.stat(path)
        query = urlencode({'INFO': pickle.dumps((fs[stat.ST_ATIME], fs[stat.ST_MTIME], port, directory), protocol=2)})
        self._setup("MIRRORSTORE", path, query=query)
        if self.result:
            self.buffer_length = 0
            return False
        else:
            self.buffer_length = 0
            return True

    def getcaps(self):
        '''
        Get the capability string from server.
        '''
        if self.server_id == '' and self.server_caps == '':
            self.ping()
        return self.server_caps

    def getid(self):
        '''
        Get the server id.
        '''
        if self.server_id == '' and self.server_caps == '':
            self.ping()
        return self.server_id

    def ping(self):
        '''
        See if there is a server running out there and get the server info.
        '''
        curtime = time.time()
        self._setup("PING", 'ping', host=self.host, port=self.port)
        if not self.result:
            self.server_ping_time = time.time() - curtime
        if self.result:
            self.server_id = ''
            self.server_caps = ''
            self.server_ping_time = 0.0
            self.buffer_length = 0
            return False
        else:
            self.server_id = ''
            self.server_caps = ''
            self.buffer_length = 0
            split_buffer = self.buffer.split()
            if len(split_buffer) >= 1:
                self.server_id = split_buffer[0]
            if len(split_buffer) >= 2:
                self.server_caps = split_buffer[1]
            if len(split_buffer) < 1:
                self.result = 1
                return False
            else:
                return True

    def _clear(self, path=''):
        '''
        Clean up after problems with retrieving.
        '''
        if self.open:
            self.f.close()
        self.open = 0
        if path and os.path.exists(path):
            os.remove(path)
        return self.result

    def checksum(self, path=''):
        '''
        checksum locates a file and returns for each result the path, host, port and checksum
        '''
        r = []
        ir = self.locate(path)
        for i in ir:
            d = dataserver_result_to_dict(i)
            if d['path'] != '?':
                if 'md5sum' in d.keys():
                    r.append((d['ip'], d['port'], d['path'], d['md5sum']))
                else:
                    r.append((d['ip'], d['port'], d['path'], self.md5sum(d['path'], d['ip'], int(d['port']))))
        return r

    def dssinit(self):
        """ Initialize localpassword
        """
        def testError():
            """
            print out an error
            """
            print_recvheader = self.recvheader
            print_sendheader = self.removesecure()
            raise IOError("%s %s dssinit: Error testing connection to %s:%d [DSTID=%s], internal error %s, recvheader=%s, sendheader=%s" % (
                time.strftime('%B %d %H:%M:%S', time.localtime()), self.machine_name, self._host, self._port, self.dstid, self.error_message, print_recvheader, print_sendheader))

        self.open = 0
        self._setup("DSSINIT", 'dssinit', host=self.host, port=self.port)
        r = ''
        if self.result:
            testError()
        elif self.buffer_length:
            r = self.buffer[:self.buffer_length]
        elif 'set-cookie' in self.recvheader:
            return True
        else:
            r = ''
            testError()
        return False

    def dssinitforce(self):
        """ Initialize localpassword
        """
        def testError():
            """
            print out an error
            """
            print_recvheader = self.recvheader
            print_sendheader = self.removesecure()
            raise IOError("%s %s dssinitforce: Error testing connection to %s:%d [DSTID=%s], internal error %s, recvheader=%s, sendheader=%s" % (
                time.strftime('%B %d %H:%M:%S', time.localtime()), self.machine_name, self._host, self._port, self.dstid, self.error_message, print_recvheader, print_sendheader))

        self.open = 0
        self._setup("DSSINITFORCE", 'dssinitforce', host=self.host, port=self.port)
        r = ''
        if self.result:
            testError()
        elif self.buffer_length:
            r = self.buffer[:self.buffer_length]
        elif 'set-cookie' in self.recvheader:
            return True
        else:
            r = ''
            testError()
        return False

    def dssgetticket(self):
        """ Initialize localpassword
        """
        def testError():
            """
            print out an error
            """
            print_recvheader = self.recvheader
            print_sendheader = self.removesecure()
            raise IOError("%s %s dssgetticket: Error testing connection to %s:%d [DSTID=%s], internal error %s, recvheader=%s, sendheader=%s" % (
                time.strftime('%B %d %H:%M:%S', time.localtime()), self.machine_name, self._host, self._port, self.dstid, self.error_message, print_recvheader, print_sendheader))

        self.open = 0
        self._setup("DSSGETTICKET", 'dssgetticket', host=self.host, port=self.port)
        r = ''
        if self.result:
            testError()
        elif self.buffer_length:
            r = self.buffer[:self.buffer_length]
        elif 'set-cookie' in self.recvheader:
            return True
        else:
            r = ''
            testError()
        return False




    def dsstestget(self):
        '''
        dsstestget returns 1 kb string
        '''
        def testError():
            """
            print out an error
            """
            print_recvheader = self.recvheader
            print_sendheader = self.removesecure()
            raise IOError("%s %s dsstestget: Error testing connection to %s:%d [DSTID=%s], internal error %s, recvheader=%s, sendheader=%s" % (
                time.strftime('%B %d %H:%M:%S', time.localtime()), self.machine_name, self._host, self._port, self.dstid, self.error_message, print_recvheader, print_sendheader))

        self.open = 0
        self._setup("DSSTESTGET", 'dsstestget', host=self.host, port=self.port)
        r = ''
        if self.result:
            testError()
        elif self.buffer_length:
            r = self.buffer[:self.buffer_length]
        else:
            r = ''
            testError()
        if len(r) == 1024:
            return True
        return False

    def dsstestconnection(self):
        '''
        dsstestnetwork returns dictionary of time required to connect to DSS servers
        '''
        def testError():
            """
            print out an error
            """
            print_recvheader = self.recvheader
            print_sendheader = self.removesecure()
            raise IOError("%s %s dsstestconnection: Error testing connection to %s:%d [DSTID=%s], internal error %s, recvheader=%s, sendheader=%s" % (
                time.strftime('%B %d %H:%M:%S', time.localtime()), self.machine_name, self._host, self._port, self.dstid, self.error_message, print_recvheader, print_sendheader))
        self.open = 0
        self._setup("DSSTESTCONNECTION", 'dsstestconnection', host=self.host, port=self.port)
        r = ''
        if self.buffer_length and not self.result:
            r = self.buffer[:self.buffer_length]
        else:
            testError()
        return r

    def dsstestnetwork(self):
        '''
        dsstestnetwork returns dictionary of time required to exchange 1 kb string between DSS servers
        '''
        def testError():
            """
            print out an error
            """
            print_recvheader = self.recvheader
            print_sendheader = self.removesecure()
            raise IOError("%s %s dsstestnetwork: Error testing connection to %s:%d [DSTID=%s], internal error %s, recvheader=%s, sendheader=%s" % (
                time.strftime('%B %d %H:%M:%S', time.localtime()), self.machine_name, self._host, self._port, self.dstid, self.error_message, print_recvheader, print_sendheader))
        self.open = 0
        self._setup("DSSTESTNETWORK", 'dsstestnetwork', host=self.host, port=self.port)
        r = ''
        if self.buffer_length and not self.result:
            r = self.buffer[:self.buffer_length]
        else:
            testError()
        return r

    def makelocal(self, path='', savepath=None, fd=None):
        '''
        cachefile requests a caching server to cache a file

        path    = name of the file
        '''

        def cacheError():
            """
            publish error
            """
            print_recvheader = self.recvheader
            print_sendheader = self.removesecure()
            raise IOError("%s %s makelocal: Error storing file %s on %s:%d [DSTID=%s], internal error %s, recvheader=%s, sendheader=%s" % (
                time.strftime('%B %d %H:%M:%S', time.localtime()), self.machine_name, path, self._host, self._port, self.dstid, self.error_message, print_recvheader, print_sendheader))

        def jobstatuscycle():
            """
            cycle to check status of job
            """
            cycle_counter = 0
            return_code = False
            cycle_break = False
            while True:
                time.sleep(self.looptime)
                self._setup("DSSGETLOG", '', host=self.host, port=self.port, jobid=self.jobid)
                if self.result == 0 and self.status == 200:
                    if 'jobstatus' in self.recvheader:
                        self.jobstatus = self.recvheader['jobstatus']
                        if self.jobstatus == 'RUNNING':
                            cycle_counter += 1
                        elif self.jobstatus == 'FINISHED':
                            return_code = True
                            cycle_break = True
                        elif self.jobstatus == 'FAILED':
                            if 'jobmessage' in self.recvheader:
                                self.jobmsg = self.recvheader['jobmessage']
                                self.error_message = self.jobmsg
                            return_code = False
                            cycle_break = True
                        else:
                            self.error_message = 'Unknown job status %s' % (self.jobstatus)
                            return_code = False
                            cycle_break = True
                    else:
                        self.error_message = 'No jobstatus in returned message'
                        return_code = False
                        cycle_break = True
                else:
                    return_code = False
                    cycle_break = True
                if cycle_break:
                    return return_code

        return_code = False
        fileuri = ''
        if path.find("://") > -1:
            fileuri = path
            path = path.split("/")[-1]
        self.open = 0
        self._setup("DSSMAKELOCAL", path, host=self.host, port=self.port, fileuri=fileuri)
        if self.result:
            cacheError()
            return_code = False
        if self.result == 0 and self.status == 200:
            if 'jobstatus' in self.recvheader and 'jobid' in self.recvheader:
                self.jobstatus = self.recvheader['jobstatus']
                self.jobid = self.recvheader['jobid']
                if self.jobstatus == 'FINISHED':
                    return_code = True
                elif self.jobstatus == 'FAILED':
                    if 'jobmessage' in self.recvheader:
                        self.jobmsg = self.recvheader['jobmessage']
                        self.error_message = self.jobmsg
                    cacheError()
                    return_code = False
                elif self.jobstatus == 'RUNNING':
                    return_code = jobstatuscycle()
                    if not return_code:
                        cacheError()
                else:
                    self.error_message = 'Unknown job status %s' % (self.jobstatus)
                    cacheError()
                    return_code = False
            else:
                self.error_message = 'No jobstatus or jobid in returned header'
                cacheError()
                return_code = False
        else:
            cacheError()
            return_code = False
        return return_code

    def makelocalasy(self, path='', savepath=None, username='', password='', fd=None):
        '''
        makelocalasy requests a caching server to cache a file

        path    = names of the file separated by ;
        '''

        def cacheError():
            """
            Report error during caching
            """
            print_recvheader = self.recvheader
            print_sendheader = self.removesecure()
            raise IOError("%s %s makelocalasy: Error storing file %s on %s:%d [DSTID=%s], internal error %s, recvheader=%s, sendheader=%s" % (
                time.strftime('%B %d %H:%M:%S', time.localtime()), self.machine_name, path, self._host, self._port, self.dstid, self.error_message, print_recvheader, print_sendheader))

        fileuri = None
        if path.find("://") > -1:
            fileuri = path
            path = path.split("/")[-1]

        self.open = 0
        self._setup("DSSMAKELOCALASY", path, host=self.host, port=self.port, fileURI=fileuri)
        if self.result == 0 and self.status == 200 and self.buffer_length:
            r = self.buffer[:self.buffer_length]
            return r
        else:
            cacheError()
            return ''

    def put(self, path='', savepath=None, fd=None):
        '''
        put stores a file on a local dataserver

        path    = path to local file
        '''
        def putError():
            """
            report error for put
            """
            print_recvheader = self.recvheader
            print_sendheader = self.removesecure()
            raise IOError("%s %s put: Error storing file %s on %s:%d [DSTID=%s], internal error %s, recvheader=%s, sendheader=%s" % (
                time.strftime('%B %d %H:%M:%S', time.localtime()), self.machine_name, path, self._host, self._port, self.dstid, self.error_message, print_recvheader, print_sendheader))

        def jobstatuscycle():
            """
            cycle for checking job status
            """
            cycle_counter = 0
            return_code = False
            cycle_break = False
            while True:
                time.sleep(self.looptime)
                self._setup("DSSGETLOG", '', host=self.host, port=self.port, jobid=self.jobid)
                if self.result == 0 and self.status == 200:
                    if 'jobstatus' in self.recvheader:
                        self.jobstatus = self.recvheader['jobstatus']
                        if self.jobstatus == 'FINISHED':
                            return_code = True
                            cycle_break = True
                        elif self.jobstatus == 'FAILED':
                            if 'jobmessage' in self.recvheader:
                                self.jobmsg = self.recvheader['jobmessage']
                            self.error_message = self.jobmsg
                            return_code = False
                            cycle_break = True
                        elif self.jobstatus == 'RUNNING':
                            cycle_counter += 1
                        else:
                            self.error_message = 'Unknown job status %s' % (self.jobstatus)
                            return_code = False
                            cycle_break = True
                    else:
                        self.error_message = 'No jobstatus in response'
                        return_code = False
                        cycle_break = True
                else:
                    self.error_message = 'error returned'
                    return_code = False
                    cycle_break = True
                if cycle_break:
                    return return_code
            return return_code

        return_code = True
        if path.find("://") > -1:
            path = path.split("/")[-1]
        if savepath is None or len(savepath) == 0:
            savepath = path
        if not os.path.exists(savepath):
            raise IOError("%s %s put: Error storing non-existent local file: %s" % (
                time.strftime('%B %d %H:%M:%S', time.localtime()), self.machine_name, path))
        else:
            self.f = open(savepath, "rb")
            self.open = 1
            self._setup("DSSSTORE", path, host=self.store_host, port=self.store_port, use_data_path=self.data_path)
            if self.result == 2:
                self.store_host = self.host2
                self.store_port = self.port2
                self.store_secure = self.secure2
                if not self.open:
                    self.f = open(savepath, "rb")
                    self.open = 1
                self._setup("DSSSTORE", path, host=self.store_host, port=self.store_port,
                            secure=self.store_secure, use_data_path=self.data_path)
            if not self.result and self.nextsend:
                self._setup("DSSSTORE", path, host=self.store_host, port=self.store_port,
                            secure=self.store_secure, use_data_path=False)
            if not self.result and self.storecheck:
                # (self.status == 204 or self.storecheck):
                self._setup("DSSSTORED", path, host=self._host, port=self._port)
                if self.result:
                    message('put: error executing DSSSTORED [result=%d]' % (self.result))
                    putError()
                    return_code = False
                else:
                    if 'jobstatus' in self.recvheader and 'jobid' in self.recvheader:
                        self.jobstatus = self.recvheader['jobstatus']
                        self.jobid = self.recvheader['jobid']
                        if self.jobstatus == 'FINISHED':
                            return_code = True
                        elif self.jobstatus == 'FAILED':
                            if 'jobmessage' in self.recvheader:
                                self.jobmsg = self.recvheader['jobmessage']
                            putError()
                            return_code = False
                        elif self.jobstatus == 'RUNNING':
                            return_code = jobstatuscycle()
                            if not return_code:
                                putError()
                        else:
                            self.error_message = 'Unknown job status %s' % (self.jobstatus)
                            putError()
                            return_code = False
                    else:
                        self.error_message = 'No jobstatus or jobid in response'
                        putError()
                        return_code = False

            elif self.result:
                putError()
                return_code = False
        return return_code