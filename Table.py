import fcntl, termios, struct
import sys

class Table:
    def __init__(self, cols, align=None, fmt=None, width=None, spacer="|", line="-"):
        self.cols = cols
        self.spacer = spacer
        self.lineChar = line
        if width is None:
            self.autoWidth = True
            self.updateSize()
        else:
            self.width = width
            self.autoWidth = False
            self.columnWidth = (self.width-(self.cols+1)) / self.cols

        if align is not None:
            self.align = [x for x in align]
            if len(self.align) != self.cols:
                print "alignment does not match column count!"
                sys.exit(1)
        else:
            self.align = ["<"] * self.cols

        if fmt is not None:
            self.convert = False
            self.fmt = fmt.split("|")
        else:
            self.convert = True
            self.fmt = ["s"] * self.cols

    def getConsoleSize(self):
        h, w, hp, wp = struct.unpack("HHHH", 
            fcntl.ioctl(0, termios.TIOCGWINSZ, 
                struct.pack("HHHH", 0, 0, 0, 0)
            )
        )
        return {"height": h, "width": w-2}


    def updateSize(self):
        if self.autoWidth:
            size = self.getConsoleSize()
            self.width = size["width"]
            self.columnWidth = (self.width - (self.cols+1) ) / self.cols

    def line(self, symbol=None):
        if symbol is None:
            symbol = self.lineChar
        print symbol*self.width

    def setHeader(self, *args):
        if len(args) != self.cols:
            print "argument count does not match column count!"
            sys.exit(1)

        self.updateSize()
        self.line()

        s = self.spacer
        s += self.spacer.join("{:{a}{w}s}".format(v, a=a, w=self.columnWidth) for a,v in zip(self.align, args))
        nicer = self.width - len(s) - 1
        if nicer <= 0:
            nicer = ""
        else:
            nicer = " " * nicer

        print s + nicer + self.spacer
        self.line("+")

    def add(self, *args):
        if len(args) != self.cols:
            print "argument count does not match column count!"
            sys.exit(1)

        fmt = []
        values = []
        for f, v in zip(self.fmt, args):
            fmt.append("s")
            
            if v is None:
                values.append("")
                continue

            if self.convert:
                values.append(str(v))
                continue

            values.append("{:{f}}".format(v, f=f))

        s = self.spacer
        s += self.spacer.join("{:{a}{w}{f}}".format(v, a=a, f=f, w=self.columnWidth) for f,a,v in zip(fmt, self.align, values))
        nicer = self.width - len(s) - 1
        if nicer <= 0:
            nicer = ""
        else:
            nicer = " " * nicer

        print s + nicer + self.spacer
        self.line()

       time.sleep(1)
