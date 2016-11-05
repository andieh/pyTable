import platform
import struct
                
if platform.system() == "Windows":
    from ctypes import windll, create_string_buffer
else:
    import fcntl, termios

import sys

from textwrap import TextWrapper

class AlignmentItemsInequalCols(Exception): pass
class HeaderItemsInequalCols(Exception): pass
class RowItemsInequalCols(Exception): pass
class NotEnoughDataError(Exception): pass


def print_all(data, start_pad="", each_level_pad="", max_width=80, depth=1):
    
    tw = TextWrapper(
        initial_indent=start_pad,
        subsequent_indent=start_pad + each_level_pad*depth,
        break_long_words=False,
        break_on_hyphens=False, 
        width=max_width-len(start_pad + each_level_pad*depth)-30 
    )
    
    func = lambda d: print_all(d, each_level_pad, depth=depth+1)
    
    out = ""
    
    # for closing ] and }, remove one pad
    pad = (each_level_pad * depth)[:-1]
    
    # out template
    out_tmpl = "{l} {t} {r}"
    
    # make the magic
    if isinstance(data, (str, unicode)):
        out = data
    elif isinstance(data, (float, int, long)):
        out = str(data)
    elif isinstance(data, (tuple, list, set)):
        
        out = ", ".join(map(func, data))
        if depth == 1:
            out = tw.fill(out)
        out = out_tmpl.format(l="[", t=out, r="]")
         
    elif isinstance(data, dict):
        out_list = []
        for k, v in data.items():
            out_list += [func(k) + ": " + func(v)]
        out += ", ".join(out_list)
        if depth == 1:
            out = tw.fill(out)
        out = out_tmpl.format(l="{", t=out, r="}")
        
    elif isinstance(data, bool):
        out = "True" if data else "False"
    else:
        out = "unknown type: {} data: {}".format(type(data), data)
    return out 
        



class Table:
    """
    cols:             Number of columns
    
    align:            Provide the alignment constraints inside the cell
    
    fmt:              Python string formatting definition for each column
                      - either using an iterable and/or also
                      - you can simply pass a string formats delimited by "|"
                      
    
    width:            'fixed'  -> implicitly, if an integer is provided 
                                  for width [1...N]
                      'full'   -> scale the output to the full available
                                  console space
                      'fit'    -> scale the output so that it will be good
                                  to understand but not as much space needed
                
                                 
    tbl_style:        'closed' -> puts spacer/lines all around the table
                      'open'   -> omits the outer spacer/lines 
    
    spacer:           [0...N] chars, which will be used for the vertical
                      separators 
    
    line:             [0...1] chars, which will be used as the generic
                      row/horizontal separator
    
    header_sep:       [0...1] chars, which will be used to separate header
                      from table body
                      
    header:           provide a list of header cell contents:
                      ["foo",..., "bar"]
    
    rows:             provide a list of lists to feed data into the table:
                      [ ["a","b","c"], my_iterable, ..., ["1", "2", "3"]
                      
    data:             higher-lvl simplistic direct data interface, simply pass
                      a class, a dict, deep, complex and it will try to generate
                      some table-based visualization from it
    
    empty_behavior:   'inform' -> show a message
                      'error'  -> throws an exception
                      'silent' -> don't react at all
                      
    empty_msg:        what to show, if empty_behavior is set to 'inform'
    
    title:            specify a title to be rendered at the top of the table
    
    title_filler:     [0...1] char, which will be used to fill the empty
                      space around the title
    """
    
    # these serve as defaults, thus class-members, but for a project with
    # differing needs, simply modify the inital ones through the class(-members)
    # (i.e., Table.def_line ="#").
    def_spacer = "   "
    def_line = ""
    def_header_sep = ""
    def_width_method = "fit"
    def_table_style = "open"
    def_align = "<"
    def_fmt = "!s"
    def_none_repr = "n/a"
    def_empty_behavior = "inform"
    def_empty_msg = "-- no data added --"
    
    def __init__(self, cols=None, width=None,
                 tbl_style=None, align=None, fmt=None, 
                 spacer=None, line=None, header_sep=None, 
                 header=None, rows=None, data=None, 
                 empty_behavior=None, empty_msg=None,
                 title=None, title_filler=None):
        
        # column count (may be omitted, 
        # if another arg implicitly defines it, i.e., header/rows/align/fmt)
        self.cols = cols
        assert any(x is not None for x in
                   [cols, header, rows, align, fmt, data])
        
        # this is a most primitive approach, set the cols-no. until ctor-ends
        if self.cols is None:
            self.cols = len(header or []) or len(rows or []) or \
                        len(align or []) or len(fmt or []) or len(data or[])
        
        # table drawing style
        self.table_style = tbl_style or self.def_table_style
        
        # table title
        self.title = title
        self.title_filler = title_filler or ""
        
        # spacers
        self.spacer = spacer or self.def_spacer
        self.line = line or self.def_line
        self.header_sep = header_sep or self.def_header_sep
        
        # width properties
        if isinstance(width, (int, long)):
            self.width = width
            self.width_method = "fixed"
        else:
            self.width = 0
            self.width_method = width or self.def_width_method
            
        self.content_width = []
        self.column_width = []

        # cell alignments
        if align is not None:
            self.align = [x for x in align]
            if len(self.align) != self.cols:
                raise AlignmentItemsInequalCols(self.align)
        else:
            self.align = [self.def_align] * self.cols

        # cell formatting
        if fmt is not None:
            # either split from string with delim "|"
            if isinstance(fmt, (str, unicode)):
                self.fmt = fmt.split("|")
            # or directly provide fmt as tuple/iterable
            else: 
                self.fmt = fmt
        # default fallback
        else:
            self.fmt = [self.def_fmt] * self.cols

        # empty behavior
        self.empty_behavior = empty_behavior or self.def_empty_behavior
        self.empty_msg = empty_msg or self.def_empty_msg
        
        # header and row data
        self.header_data = None
        self.data_rows = []
        self.raw_data_rows = None
        
        if data is not None:
            # first let's assume dict-of-(same-)dicts, typical table
            # headers first:
            headers = ["name"] + data[iter(data).next()].keys()
            self.cols = len(headers)
            
            contents = []
            for k, v in data.items():
                contents.append(v)
                contents[-1].update(name=k)
            self.set_header(*headers)
            for item in contents:
                self.add_data_assoc(item)
            
        
        else:
            # directly pass header-data
            if header is not None:
                self.set_header(*header)
            # directly pass row-data
            if rows is not None:
                for row in rows:
                    self << row

        # anyone may set 'self.cols' somehow, but only until here!         
        assert self.cols is not None and self.cols != 0            
            
    def rows_iter(self):
        """Iterate over all rows"""
        if self.header_data is not None:
            yield self.header_data
        for row in self.data_rows:
            yield row

    def render_row(self, *args):
        """Render the table body"""
        s = ""
        if self.table_style == "closed":
            s += self.spacer
        
        s += self.spacer.join(
            "{:{a}{w}}".format(v, a=a, w=self.content_width[i]) \
               for i, (a, v) in enumerate(zip(self.align, args))
        )
           
        if self.table_style == "closed":
            s += self.spacer

        return s        
            
    def render_header(self):
        """Render the header row"""
        if len(self.header_data) != self.cols:
            raise HeaderItemsInequalCols(
                str((self.cols, self.header_data)))
        
        s = ""

        if self.table_style == "closed":
            s += self.spacer
        
        
        if len(self.header_data) != len(self.content_width):
            no_data = reduce(lambda a, b:a+b, [len(d) for d in self.data_rows], 0)
            raise NotEnoughDataError("#headers (x): {} #content (y): {} => x % y = {} => :(". \
                format(len(self.header_data), no_data, no_data % len(self.header_data)))
            
        s += self.spacer.join(
            "{:{a}{w}s}".format(v, a=a, w=self.content_width[i]) \
                for i, (a, v) in enumerate(zip(self.align, self.header_data)))
        
        if self.table_style == "closed":
            s += self.spacer
            
        return s             
    def render_line(self, symbol=None):
        """Render a horizontal full width line using 'symbol' or default"""
        char = symbol or self.line
         
        if char:
            return char * self.width
        return ""

    def render(self):
        """Render table and output it (currently via print)"""
        
        out = []

        self.apply_formatting()
        self.update_size()

        if self.title is not None:
            
            avail_space = (self.width - len(self.title))
            pad_num = (avail_space // len(self.spacer)) // 2
            pad = self.spacer * pad_num
            out += ["{:{fill}^{w}}".format(
                self.title, w=self.width, fill=self.title_filler)
            ]
            
        if self.table_style == "closed":
            out += [self.render_line()]
            
        if self.header_data:
            out += [self.render_header()]
            
        out += [self.render_line(self.header_sep)]
        
        # handle empty data-set
        if len(self.data_rows) == 0:
            if self.empty_behavior == "inform":
                out += ["{:^{w}}".format(self.empty_msg, w=self.width)]
            elif self.empty_behavior == "error":
                raise NotEnoughDataError(str(self.data_rows))
        # regular table-body generation
        else:  
            for i, row in enumerate(self.data_rows):
                out += [self.render_row(*row)]
                if i + 1 != len(self.data_rows):
                    out += [self.render_line()]
            
        if self.table_style == "closed":
            out += [self.render_line()]
        
        return "\n".join(filter(lambda x: x not in ["", [""], ("", )], out))
        #return "\n".join(out)
    
    def __repr__(self):
        """Pass the object to print, will render it"""
        return self.render()
    
    @classmethod   
    def get_console_size(cls):
        """Get console size: windows & linux (posix) supported"""
        # windows
        if platform.system() == "Windows":
            h = windll.kernel32.GetStdHandle(-12)
            csbi = create_string_buffer(22)
            ret = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
            
            h, w = 25, 80
            if ret:
                (bufx, bufy, curx, cury, wattr,
                 left, top, right, bottom, maxx, maxy) = \
                    struct.unpack("hhhhHhhhhhh", csbi.raw)
                h = bottom - top + 1
                w = right - left + 1
        # linux (posix)
        else:    
            h, w, hp, wp = struct.unpack("HHHH", 
                fcntl.ioctl(0, termios.TIOCGWINSZ, 
                    struct.pack("HHHH", 0, 0, 0, 0)
                )
            )
        return {"height": h, "width": w-2}


    def update_size(self):
        """Calculate the table width"""

        self.column_width = []
        self.content_width = []
        
        # take the full console width for the table
        if self.width_method == "full":
            size = self.get_console_size()
            self.width = size["width"] 
            for i in range(self.cols):
                w = self.width / self.cols
                self.content_width.append(w)
                self.column_width.append(w + len(self.spacer))
                i = 0
                while sum(self.column_width) > self.width:
                    self.column_width[i] -= 1
                    self.content_width[i] -= 1
                    i = (i + 1) % len(self.column_width)
            
        # find a nice fit for the shown data
        if self.width_method == "fit":
            for i, col in enumerate(zip(*self.rows_iter())):
                w = max(len(cell) for cell in col) 
                self.content_width.append(w)
                self.column_width.append(w + len(self.spacer)) 
            
        # fixed width
        if self.width_method == "fixed":
            for i in range(self.cols):
                w = self.width / self.cols
                self.content_width.append(w)
                self.column_width.append(w + len(self.spacer))
         
        # tuning for table styles
        if self.table_style == "closed":
            self.column_width[0] += len(self.spacer)
        else:
            self.column_width[-1] -= len(self.spacer)
            
        self.width = sum(self.column_width)

    
    def set_header(self, *args, **kwargs):
        """Save header content"""
        if len(args) > 0 and len(kwargs) == 0:
            self.header_data = args
        elif len(args) == 0 and len(kwargs) > 0:
            self.header_data = kwargs.keys()
    
    def add_data_item(self, item):
        """
        Insert a single item,
        - either append to an existing list, or
        - create a new one and put the single item there
        """
        if len(self.data_rows) > 0 and len(self.data_rows[-1]) < self.cols:
            self.data_rows[-1].append(item)
        else:
            self.data_rows.append([item])
            
    def add_data_list(self, row):
        """Add a full data list representing a full row"""
        # add full row (arbitrary list/tuple and so on) of values
        self.data_rows.append(list(row))
        
    def add_data_assoc(self, assoc, force_no_header=False, adapt_header=True):
        """
        Use data from associative container to view it.
        - if no header is in place, the keys() will be used for them, as
          long as 'force_no_header' is 'False'
        - the 'assoc' can have more and/or less members than header forces,
          as either there will be a 'None' or it will remain simply unused
        - 'adapt_header' on the other side, simply diffs both headers and keys
          to then add all keys from the assoc data-struct.
        """

        # populate header with keys, if nothing is there
        if self.header_data is None and not force_no_header:
            self.set_header(sorted(assoc.keys()))        
        
        if adapt_header:
            diff =  set(assoc.keys()) - set(self.header_data)
            if len(diff) > 0:
                self.set_header(self.header_data + [x for x in diff])
                
        
        # add a dict, i.e., map as row
        # simply try to get() all vals, None is fallback anyways -> nice
        self.data_rows.append([assoc.get(k) for k in self.header_data])
     
    def add(self, *args):
        """Save/append data to a table-row, apply formatting, keep original"""
        self.add_data_list(row=args)
                  
    def __lshift__(self, args):
        """
        Alternative fancy data input facility:
        - passing a tuple -> len(tuple) == self.cols
        - passing one after another -> tab << cell1 << cell2 ...
        - an associative container is also fine
        """
        if isinstance(args, (tuple, list)):
            self.add_data_list(row=args)
        elif isinstance(args, dict):
            self.add_data_assoc(args)
        else:            
            self.add_data_item(item=args)
        return self


    def add_horiz_line(self):
        """TODO -> add horizontal separator line choosen by user where/when"""
        pass
    def add_data_multicol(self, item, merge_col_num):
        """TODO -> add 'item' and merge cols"""
        pass
    
    def set_title(self, title_text, filler=None):
        """Save the table title to be later rendered at the top of the table"""
        self.title = title_text
        self.title_filler = filler or self.title_filler
        
    
    def set_col_format(self, col_idx, fmt):
        """Change formatting for a specfic 'col_idx'"""
        self.fmt[col_idx] = fmt        

    def apply_formatting(self):
        """
        Apply the formatting on all cells.
        TODO: what happens on "full" width mode and right alignment!?        
        """
        
        if self.raw_data_rows is None:
            self.raw_data_rows = self.data_rows[:]
        else:
            self.data_rows = self.raw_data_rows[:]
        
        # apply format
        new_data = []
        for row in self.data_rows:
            
            new_row = []
            for col_idx, (fmt, cell) in enumerate(zip(self.fmt, row)):

                if cell is None:
                    new_row.append(self.def_none_repr)
                    continue
            
                if "!" in fmt:
                    new_row.append(("{" + fmt + "}").format(cell))
                else:
                    new_row.append("{:{f}}".format(cell, f=fmt))
            
            new_data.append(new_row[:])
        
        self.data_rows = new_data
            
        