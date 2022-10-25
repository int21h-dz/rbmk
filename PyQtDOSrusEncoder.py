# -*- coding: utf-8 -*-
#!/usr/bin/env python
from PyQt4 import QtGui, QtCore
import sys, codecs

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s


def setup_console(sys_enc="utf-8"):
    reload(sys)
    try:
        # для win32 вызываем системную библиотечную функцию
        if sys.platform.startswith("win"):
            import ctypes
            enc = "cp%d" % ctypes.windll.kernel32.GetOEMCP() #TODO: проверить на win64/python64
        else:
        # для Linux всё, кажется, есть и так
            enc = (sys.stdout.encoding if sys.stdout.isatty() else
                        sys.stderr.encoding if sys.stderr.isatty() else
                            sys.getfilesystemencoding() or sys_enc)

            # кодировка для sys
        sys.setdefaultencoding(sys_enc)

            # переопределяем стандартные потоки вывода, если они не перенаправлены
        if sys.stdout.isatty() and sys.stdout.encoding != enc:
                sys.stdout = codecs.getwriter(enc)(sys.stdout, 'replace')

        if sys.stderr.isatty() and sys.stderr.encoding != enc:
                sys.stderr = codecs.getwriter(enc)(sys.stderr, 'replace')

    except:
        pass # Ошибка? Всё равно какая - работаем по-старому...

class IBM866FileDecoder():
    def __init__(self,TROYKAfin):
        for mib in QtCore.QTextCodec.availableMibs():
            codec = QtCore.QTextCodec.codecForMib(mib)
            if codec_name(codec).upper() == 'IBM866':
                break
        encodedData = self.open(TROYKAfin)
        data = QtCore.QTextStream(encodedData)
        data.setAutoDetectUnicode(False)
        data.setCodec(codec)
        self.decodedStr = data.readAll()
        encodedData.close()
        return decodedStr

    def open(self, fileName):
        if fileName:
            inFile = QtCore.QFile(fileName)
            if not inFile.open(QtCore.QFile.ReadOnly):
                QtGui.QMessageBox.warning(self, "Codecs",
                        "Cannot read file %s:\n%s" % (fileName, inFile.errorString()))
                return
        return inFile #.readAll()

def main():
    pass

if __name__ == '__main__':
    main()
