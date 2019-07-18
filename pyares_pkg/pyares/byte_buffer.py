# TODO now only forward translation (put), do we need backwards translation as well?


class ByteBuffer:
    """
    Bytebuffer of flexible size
    """

    def __init__(self):
        self.__size = None
        self.__bytebuffer = bytearray()

    def __put(self, b):
        self.__bytebuffer.extend(b)

    def put_int(self, i):
        """
        Adding an integer to the bytebuffer.
        Adds 3 bytes.
        :param i: Integer
        """
        self.__put(i.to_bytes(3, 'big'))

    def put_long(self, l):
        """
        Adding a 'Long' to the bytebuffer.
        Adds 8 bytes.
        (Python doesn't truly deal with longs, so give an integer with the same maxsize as a long.)
        :param l: Integer 'Long'
        """
        self.__put(l.to_bytes(8, 'big'))

    def get_bytebuffer(self):
        """
        Return the bytebuffer (type bytearray())
        :return: bytearray() bytebuffer
        """
        return bytes(self.__bytebuffer)

    def get_length(self):
        return len(self.__bytebuffer)
