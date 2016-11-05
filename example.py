#!env python2

from table import Table
from random import randint as rand

t = Table(6, width="fit", align=">>>>>>", fmt="d|d|d|d|d|d")   # fixed width, 3 columns
t.set_header("$$ Amount", "Cookies", "No.1", "No.2", "No.3", "No.4")
for i in xrange(13):
	for x in xrange(6):
		t << rand(0, 999999)
print t

print
print "Try different styles easily:"
print
t.header_sep = "-"
t.tbl_style = "closed"
t.line = "-"
t.spacer = " | "
print t
print
print
t.set_col_format(2, ".4e")
t.set_col_format(3, "15,.5f")
t.set_col_format(4, "010d")
t.header_sep = "="
t.width_method = "full"
print t


# -----------------------------------------------------------------------------
print
t = Table(header=("DATE", "PRICE", "STATUS", "DESC"), tbl_style="open",
  line="-", header_sep="=", spacer=" |  ", width="fit", align="^>^<")
t << ("May 21th", 1235.32, "green", "fancy stuff")
t << ("June 1st", 68213.4, "red", "expensive beans")
t << ("July 4th", 329024.3, "yellow", "yellow shiny food")
print t
print
