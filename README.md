**pyTable**
===========

Convinient class for (auto-)printing/layouting arbitrary data into pretty (ascii-)tables. 

Get your data out **fast and pretty with ease**.

Features:
---------

* Higher customization possibilities for column, row separators
* Further cell formatting options and flexibility 
* 3 different *width-modes* available now: 
  * **fixed** = apply any given width to each column
  * **full** = automatically use the full console width [linux & win32 compatible]) 
  * **fit** = automatically expand the table as needed to fit to the cell contents
* Apply custom header to content separator
* Different possibilities to handle empty data input sets
* Set a table title and on-demand filling of space right and left of the title 
* Different table-styles:
  * **open** = no outer borders/separators all side/bottom/top cells have one side "open"
  * **close** = table is "framed", thus closed by the respective separator(s)
* Data input methods:
  * Automated handling of arbitrary data (also mixed lists/dicts)
  * Convenient << operator to "push" data(-sets)
  * Non-automated ``add_data_item()``, ``add_data_list()``, ``add_data_assoc()``
* Full *Win32* and *Linux* compatibility
* Lazy-evaluated

Example:
--------

Simply feed your arbitrary data into an Table() instance:

    from table import Table
    from random import randint as rand
    
    print
    t = Table(header=("DATE", "PRICE", "STATUS", "DESC"), tbl_style="open",
      line="-", header_sep="=", spacer=" |  ", width="fit", align="^>^<")
    t << ("May 21th", 1235.32, "green", "fancy stuff")
    t << ("June 1st", 68213.4, "red", "expensive beans")
    t << ("July 4th", 329024.3, "yellow", "yellow shiny food")
    print t

will lead to:

      DATE   |     PRICE |  STATUS |  DESC
    ===================================================
    May 21th |   1235.32 |  green  |  fancy stuff
    ---------------------------------------------------
    June 1st |   68213.4 |   red   |  expensive beans
    ---------------------------------------------------
    July 4th |  329024.3 |  yellow |  yellow shiny food
    
See [examples.py](https://github.com/andieh/pyTable/blob/master/examples.py) for more.

  
