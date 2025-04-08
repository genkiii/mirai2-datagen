'''Amoeba(Nelson) data
'''

import struct
import pprint
import sys
import datetime
import json


class AmCarrier:

    def __init__(self, f):
        (dataId, fileSize, one, _, _, progLen) = struct.unpack('!6l', f.read(24))
        assert one == 1
        progLen -= 13
        ip = struct.unpack('4B', f.read(4))
        assert struct.unpack('!l', f.read(4)) == (1,)
        prog = f.read(progLen).decode()
        assert struct.unpack('5B', f.read(5)) == (0,) * 5
        self.dataId = dataId
        self.fileSize = fileSize
        self.prog = prog
        print('  data id:', self.dataId, file=sys.stderr)
        print('file size:', self.fileSize, file=sys.stderr)
        print('  program:', self.prog, file=sys.stderr)


class AmData:

    def __init__(self, f, carrier=True, verbose=True):
        self.f = f
        if carrier:
            self.carrier = AmCarrier(self.f)
        self.getHeader(verbose)

    def getHeader(self, verbose=True):
        h = self.f.read(1)
        # assert len(h) == 1
        if len(h) == 0:
            raise EOFError()
        while b := self.f.read(1):
            h += b
            if b == b'\x1a':
                break
        assert h[:3] == b'WN\n'
        assert h[-3:] == b'\n\x04\x1a'
        self.header = dict([l.split('=') for l in h[3:-3].decode().split('\n')])
        if verbose:
            print('\x1b[31m' + json.dumps(self.header, indent=2) + '\x1b[0m', file=sys.stderr)

    def __getitem__(self, key):
        return self.header[key]

    def tofile(self, filepath):
        with open(filepath, 'wb') as f:
            f.write(self.f.read())

    @property
    def filename(self):
        return self['header_comment']
    
    @property
    def time(self):
        return datetime.datetime.strptime(self['announced'], '%Y/%m/%d %H:%M:%S GMT')
