import io
from utils import read_until


class SpoofSerial:
    msg = "Test\r\n"
    def __init__(self,*args,**kwargs):
        self.args = args
        self.kwargs = kwargs

        self.buffer = io.BytesIO(self.msg)
    def read(self,nBytes=1):
        tmp = self.buffer.read(nBytes)
        if tmp == "":
            self.buffer = io.BytesIO(self.msg)
            return self.read(nBytes)
    def read_until(self,pattern,size=None):
        return read_until(self.buffer,pattern,size)

class GPSSpoofSerial(SpoofSerial):
    msg = "$GPMRC,,V,\r\n$GPGSA,,\r\n"
    def setValues(self,lat,lon,elevation):
        pass
class ALTSpoofSerial(SpoofSerial):
    msg = "\x13as\x33\xca\xcb\xcc\xcdJUNKJUNK\x07P\x04fzsdJUNKJUNK\xea\xeb\xec\xed"
