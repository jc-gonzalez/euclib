import os
import time
from urllib.parse import urlencode

from dss.dataio import DataIO
from dss.dssserver_client import message, fetch_file_from_dataserver


class Storage(DataIO):
    """
    interface for compatibility with DataObject
    """

    def retrieve(self, data_object):
        message('Retrieving %s' % data_object.pathname)
        begin = time.time()
        if hasattr(data_object, 'subimage'):
            x1, y1, x2, y2 = data_object.subimage
            fhi = str(x2)+','+str(y2)
            flo = str(x1)+','+str(y1)
            query = urlencode({'FHI':fhi, 'FLO':flo})
            # old code query = 'RANGE2=%(x2)d,%(y2)d&RANGE1=%(x1)d,%(y1)d' % vars()
            filename = os.path.join(data_object.filepath, data_object.filename)
            fetch_file_from_dataserver(filename, query=query, savepath=data_object.pathname)
        else:
            self._set_data_path()
            self.get(path=data_object.pathname)
        end = time.time()
        total = end-begin
        if data_object.exists():
            if total >= 0.005:
                size = os.path.getsize(data_object.pathname)/2**10
                message('Retrieved %s[%dkB] in %.2f seconds (%.2fkBps)' % (data_object.pathname, size, total, size/total))
            else:
                message('Retrieved %s' % data_object.pathname)

    def store(self, data_object):
        message('Storing %s' % data_object.pathname)
        begin = time.time()
        self._set_data_path()
        self.put(path=data_object.pathname)
        data_object.set_stored()
        end = time.time()
        total = end-begin
        if data_object.exists():
            if total >= 0.005:
                size = os.path.getsize(data_object.pathname)/2**10
                message('Stored %s[%dkB] in %.2f seconds (%.2fkBps)' % (data_object.pathname, size, total, size/total))
            else:
                message('Stored %s' % data_object.pathname)

    @staticmethod
    def object_to_commit(self, data_object):
        return data_object