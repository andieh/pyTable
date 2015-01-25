import sys

from Table import *

if __name__ == "__main__":
    table = Table(3)
    table.setHeader("erster", "zweiter", "dritter")
    table.add("eintrag", "eintrag", "2.3")
    table.add("eintrag", "eintrag", 2.3)
    
    print
    table2 = Table(3, align="<^>", fmt="s|+0.2f|010d")
    table2.setHeader("was", "erster", "zweiter")
    table2.add("blubb", 2.3, 1)
    table2.add("blubbohne", None, 33)
    
    print
    table3 = Table(2, width=30, align="^^", spacer="#", line="#")
    table3.setHeader("erster", "zweiter")
    table3.add("zwei", 3)
    table3.add(1,2)
    table3.add(None,2333)
    table3.add(0.3,0.3)
