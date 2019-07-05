import socket
import subprocess
import sys


def gpgencrypt(lines, defaultkey, fout=None, lout=[], gpghomedir=None):
    '''
    gpgencrypt encrypts lines with defaultkey and writes them to
    file object fout. lines should NOT contain newlines!
    '''
    if gpghomedir == None:
        pcmd = subprocess.Popen('gpg                          --output - --default-key "%(defaultkey)s" --clearsign' % vars(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    else:
        pcmd = subprocess.Popen('gpg --homedir %(gpghomedir)s --output - --default-key "%(defaultkey)s" --clearsign' % vars(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if sys.version_info.major > 2:
        (outtext, errtext) = pcmd.communicate(input=str.encode('\n'.join(lines)))
        outtext = outtext.decode()
        errtext = errtext.decode()
    else:
        (outtext, errtext) = pcmd.communicate(input='\n'.join(lines))
    returncode = pcmd.returncode
    if returncode == None:
        machine_name = socket.gethostname()
        #print('%s %s gpgencrypt: kill child!' % (time.strftime('%B %d %H:%M:%S', time.localtime()), machine_name))
        pcmd.kill()
        returncode = -255
    elif returncode:
        if errtext:
            machine_name = socket.gethostname()
            #print('%s %s gpgencrypt: %s' % (time.strftime('%B %d %H:%M:%S', time.localtime()), machine_name, errtext))
    elif fout:
        fout.write(outtext)
    else:
        returncode = None
        for l in outtext.split('\n'):
            lout.append(l+'\n')
    return returncode


def gpgdecrypt(fin=None, lin=[], gpghomedir=None):
    '''
    gpgdecrypt decrypts the encrypted lines read from file object
    fin. It returns a list of strings without newlines!
    '''
    r = []
    if fin:
        buf = ''.join(fin.readlines())
    else:
        buf = ''.join(lin)
    if gpghomedir == None:
        pcmd = subprocess.Popen('gpg                          --output - --decrypt' % vars(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    else:
        pcmd = subprocess.Popen('gpg --homedir %(gpghomedir)s --output - --decrypt' % vars(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if sys.version_info.major > 2:
        (outtext, errtext) = pcmd.communicate(input=str.encode(buf))
        outtext = outtext.decode()
        errtext = errtext.decode()
    else:
        (outtext, errtext) = pcmd.communicate(input=buf)
    returncode = pcmd.returncode
    if pcmd.returncode == None:
        machine_name = socket.gethostname()
        #print('%s %s gpgdecrypt: kill child!' % (time.strftime('%B %d %H:%M:%S', time.localtime()), machine_name))
        pcmd.kill()
        returncode = -255
    elif returncode:
        if errtext:
            machine_name = socket.gethostname()
            #print('%s %s gpgdecrypt: %s' % (time.strftime('%B %d %H:%M:%S', time.localtime()), machine_name, errtext))
    else:
        r = outtext.split()
    return r