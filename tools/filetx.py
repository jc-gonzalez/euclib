#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filetx.py

Module for defining class Tx to transmit files in different ways
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

import shutil
import asyncssh, asyncio

import pytest

from pprint import pprint

from enum import Enum

import logging
logger = logging.getLogger()

#----------------------------------------------------------------------

VERSION = '0.0.1'

__author__     = "J C Gonzalez"
__version__    = VERSION
__license__    = "LGPL 3.0"
__status__     = "Development"
__copyright__  = "Copyright (C) 2015-2019 by Euclid SOC Team @ ESAC / ESA"
__email__      = "jcgonzalez@sciops.esa.int"
__date__       = "June 2019"
__maintainer__ = "J C Gonzalez"
#__url__       = ""

#----------------------------------------------------------------------

def dumpArgs(args):
    for k,v in args:
        print('{} := {}'.format(k,v))

class TxMode(Enum):
    """
    Mode to transfer files
    """
    MOVE         = 'move'
    MOVE_ORIG    = 'move_orig'
    LINK         = 'link'
    COPY         = 'copy'
    REMOTE_COPY  = 'remote-copy'
    REMOTE_MOVE  = 'remote-move'

class Tx:
    """
    Class to perform a transfer of a file
    """
    def __init__(self):
        """
        Initialization of Tx class
        """
        self.file_full = None
        self.to_dir = None
        self.hostname = None
        self.uname = None
        self.passwd = None

    def file(self, pth):
        """
        Set file to transfer
        :param pth: Full file path
        :return: -
        """
        self.file_full = pth
        return self

    def toDir(self, pth):
        """
        Set target directory
        :param pth: File path
        :return: -
        """
        self.to_dir = pth
        return self

    def host(self, h):
        """
        Set host name (for remote connections)
        :param h: the host name
        :return: -
        """
        self.hostname = h
        return self

    def user(self, u):
        """
        Set username (for remote connections)
        :param u: the user name
        :return: -
        """
        self.uname = u
        return self

    def pwd(self, pw):
        """
        Set user password (for remote connections)
        :param pw: the user password
        :return: -
        """
        self.passwd = pw
        return self

    def move(self):
        """
        Move the file
        :return: -
        """
        return self.go(mode=TxMode.MOVE)

    def move_and_set(self):
        """
        Move the file, and set as the new source
        :return: -
        """
        return self.go(mode=TxMode.MOVE_ORIG)

    def copy(self):
        """
        Copy the file
        :return: -
        """
        return self.go(mode=TxMode.COPY)

    def link(self):
        """
        Link the file
        :return: -
        """
        return self.go(mode=TxMode.LINK)

    def remote_move(self):
        """
        Move the file through scp to a remote host
        :return: -
        """
        return self.go(mode=TxMode.REMOTE_MOVE)

    def remote_copy(self):
        """
        Copy the file with scp to a remote host
        :return: -
        """
        return self.go(mode=TxMode.REMOTE_COPY)

    async def async_copy(self, hname, uname, pwd, from_file, to_file, is_move):
        """
        Copy/Move file with scp
        :param hname: Host name
        :param uname: User name
        :param pwd: Password
        :param from_file: Original file
        :param to_file: Remote file name
        :param is_move: True, if the transfer is a move
        :return: -
        """
        pprint(locals())

        async with asyncssh.connect(hname, username=uname, password=pwd) as conn:
            await asyncssh.scp(from_file, (conn, to_file + '.part'))
            result = await conn.run('mv {0}.part {0}'.format(to_file), check=True)
        if is_move:
            os.unlink(from_file)

    def go(self, mode=TxMode.MOVE):
        """
        Make the relocation
        :param mode: The way to perform the relocation
        :return:
        """
        if mode == TxMode.COPY:

            new_file = os.path.join(self.to_dir, os.path.basename(self.file_full))
            logger.debug('{} ==COPY==> {}'.format(self.file_full, new_file))
            shutil.copy(self.file_full, new_file + '.part')
            shutil.move(new_file + '.part', new_file)

        elif mode == TxMode.MOVE or mode == TxMode.MOVE_ORIG:

            new_file = os.path.join(self.to_dir, os.path.basename(self.file_full))
            logger.debug('{} ==MOVE==> {}'.format(self.file_full, new_file))
            shutil.move(self.file_full, new_file + '.part')
            shutil.move(new_file + '.part', new_file)

            if mode == TxMode.MOVE_ORIG:
                self.file_full = new_file

        elif mode == TxMode.LINK:

            new_file = os.path.join(self.to_dir, os.path.basename(self.file_full))
            logger.debug('{} ==LINK==> {}'.format(self.file_full, new_file))
            os.link(self.file_full, new_file)

        elif mode == TxMode.REMOTE_COPY or mode == TxMode.REMOTE_MOVE:

            new_file = os.path.join(self.to_dir, os.path.basename(self.file_full))
            loop = asyncio.get_event_loop()
            try:
                loop.run_until_complete(self.async_copy(hname=self.hostname,
                                                        uname=self.uname, pwd=self.passwd,
                                                        from_file=self.file_full, to_file=new_file,
                                                        is_move=(mode == TxMode.REMOTE_MOVE)))
            except (OSError, asyncssh.Error) as exc:
                logger.error('SSH connection failed: ' + str(exc))

        else:

            logger.error('Transfer mode not known!')

        return self

## TESTS

class TestTx:

    @pytest.fixture
    def tx(self):
        yield Tx()

    @pytest.fixture
    def the_file(self):
        yield __file__

    @pytest.fixture
    def to_folder(self):
        yield os.getenv('HOME', '/tmp')

    @pytest.fixture
    def to_host(self):
        yield 'eucdev.n1data.lan'

    @pytest.fixture
    def the_user(self):
        yield 'eucops'

    @pytest.fixture
    def the_pwd(self):
        yield 'eu314clid'

    def md5(self, fname):
        import hashlib
        hash_md5 = hashlib.md5()
        with open(fname, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def test_specify_file(self, tx, the_file):
        assert tx.file(the_file) == tx
        assert tx.file_full == the_file

    def test_specify_folder(self, tx, to_folder):
        assert tx.toDir(to_folder) == tx
        assert tx.to_dir == to_folder

    def test_specify_host(self, tx, to_host):
        assert tx.host(to_host) == tx
        assert tx.hostname == to_host

    def test_specify_user(self, tx, the_user):
        assert tx.user(the_user) == tx
        assert tx.uname == the_user

    def test_specify_pwd(self, tx, the_pwd):
        assert tx.pwd(the_pwd) == tx
        assert tx.passwd == the_pwd

    def test_copy_and_move_and_link(self, tx, the_file, to_folder):
        bname = os.path.basename(the_file)
        mv_dir = os.path.join(to_folder, 'mv.dir')
        ln_dir = os.path.join(to_folder, 'ln.dir')
        try:
            for d in [mv_dir, ln_dir]:
                if os.path.exists(d):
                    shutil.rmtree(d, ignore_errors=True)
                os.mkdir(d)
        except:
            pass

        assert tx.file(the_file).toDir(to_folder).copy() == tx
        new_file = os.path.join(to_folder, bname)
        assert self.md5(the_file) == self.md5(new_file)

        assert tx.file(new_file).toDir(mv_dir).move() == tx
        new_file2 = os.path.join(mv_dir, bname)
        assert self.md5(the_file) == self.md5(new_file2)

        assert tx.file(new_file2).toDir(ln_dir).link() == tx
        new_file3 = os.path.join(ln_dir, bname)
        assert self.md5(new_file2) == self.md5(new_file3)

        for d in [mv_dir, ln_dir]:
            if os.path.exists(d):
                shutil.rmtree(d, ignore_errors=True)


def main():
    pytest.main()


if __name__ == '__main__':
    main()
