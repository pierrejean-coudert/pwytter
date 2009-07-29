# $Id: tinpy.py,v 1.11 2006/04/10 03:36:17 urago Exp $

"""
Tiny Python Template (tinpy)

This is simple and tiny template framework module. It's speedy processing.
It provides extract variables, reference dictionary
and sequencial variable loop.
Import tinpy module and call a function,
so it became generate document with template.
"""

import string
import re
from StringIO import StringIO

class TemplateParser:
    "Template parser."

    def __init__(self):
        # Template syntax pattern. e.g. "[%var foobar%]"
        self.tppattern = re.compile('(\[%.*?%\])', re.DOTALL)
        self.lineno = 1
        self.chunk = ''

    def set_processhandler(self, handler):
        self.handler = handler

    def parse(self, source):
        "Parsing source. source is string"
        for chunk in self.tppattern.split(source):    
            self.lineno = self.lineno + chunk.count('\n')
            self.chunk = chunk
            if self.tppattern.match(chunk):
                apply(self.handler.handle, chunk[2:-2].split())
                continue
            try: self.handler.handle_data(chunk)
            except: pass
        if hasattr(self.handler, 'end_document'):
            self.handler.end_document()

class ProcessingHandler:
    "Parser processing handler."
    
    def __init__(self):
        self.template = TemplateManager(Template())
        self.in_comment = 0

    def op_comment(self, arg):
        if arg == 'begin':
            self.in_comment = 1
        elif arg == 'end':
            self.in_comment = 0
        else:
            raise SyntaxError, "invalid syntax: comment %s" % str(arg)

    def op_stag(self, *args):
        if len(args) != 0:
            raise SyntaxError, \
                  "invalid syntax: %s" % string.join(list(args))
        self.template.write('[%%')

    def op_etag(self, *args):
        if len(args) != 0:
            raise SyntaxError, \
                  "invalid syntax: %s" % string.join(list(args))
        self.template.write('%%]')

    def op_var(self, *args):
        if len(args) != 1:
            raise SyntaxError, \
                  "invalid syntax: args: %s" % string.join(list(args))
        self.template.write('%%(%s)s' % args[0])
         
    def op_for(self, *args):         
        args = list(args)
        try:
            in_index = args.index('in')
            vars = [token.strip() for token in ''.join(args[:in_index]).split(',')]
            if len(vars) == 1:
                vars = vars[0]
            srclist = ''.join(args[in_index+1:])
        except Exception, e:
            raise SyntaxError, "invalid syntax: '%s' %s" % (string.join(list(args)), e)
        self.template.forblock_begin(vars, srclist)

    def op_done(self):
        self.template.forblock_end()

    def op_if(self, *args):
        if len(args) != 1:
            raise SyntaxError, \
                  "invalid syntax: args: %s" % string.join(list(args))
        self.template.ifblock_begin(args[0])

    def op_endif(self):
        self.template.ifblock_end()

    def handle_data(self, chunk):        
        if self.in_comment == 1:
            return
        self.template.write(chunk.replace('%', '%%'))
        
    def end_document(self):
        self.template.end_document()

    def handle(self, op, *tokens):
        # Comment out process.
        if op == 'comment':
            self.op_comment(string.join(tokens))
            return
        if self.in_comment:
            return

        # Handle operation.
        apply(getattr(self, 'op_' + op), tokens)

class Template:
    "Template object."

    def __init__(self):
        self.nodelist = []
        self.initdescriptor()

    def initdescriptor(self):
        self.__descriptor = StringIO()

    def write(self, s):
        self.__descriptor.write(s)

    def getvalue(self):
        return self.__descriptor.getvalue()

class ForBlock(Template):
    "For block object."

    def __init__(self, parent, seqvarnames, seqname):
        Template.__init__(self)
        self.parent = parent

        self.seqvarnames = seqvarnames
        self.seqname = seqname

class IfBlock(Template):
    "For block object."

    def __init__(self, parent, varname):
        Template.__init__(self)
        self.parent = parent

        self.varname = varname

class DictEnhanceAccessor:
    "Variable dictionary enhance interface."

    p = re.compile('^(?P<var>[a-zA-Z_][a-zA-Z0-9_]*)(?P<modifier>(\[.+?\])+)$')
    d = re.compile('(\[[a-zA-Z_][a-zA-Z0-9_]*\])')

    def __init__(self, strict, dic={}):
        self.strict = strict
        self.dic = dic

    def __getitem__(self, key):
        m = self.p.match(key)
        if not m: return self.dic.get(key, '') # Normal key.
        val = self.dic.get(m.group('var'), '')
        buf = StringIO()
        for mo in self.d.split(m.group('modifier')):
            if self.d.match(mo):
                buf.write("['%s']" % self.dic[mo[1:-1]])
            else:
                buf.write(mo)
        try:
            return eval('val'+ buf.getvalue(), # code
                        {'__builtins__':{}}, # globals is restricted.
                        {'val':val}) # locals is only 'val'
        except Exception, e:
            if self.strict: raise#Remove the following to reraise correctly: Exception, e
        return  ''

    def __setitem__(self, key, val):
        self.dic[key] = val

    def __repr__(self):
        return str(self.dic)

class VariableStack:
    "Variable data stack."

    def __init__(self, variables=None):
        self.stack = []
        if variables:
            self.push(variables)

    def __getitem__(self, num):
        return self.stack[num]

    def __repr__(self):
        return str(self.stack)

    def pop(self):
        return self.stack.pop(0)
    
    def push(self, data):
        self.stack.insert(0, data)

    def find(self, varname):
        value = None
        for variables in self.stack:
            if variables.has_key(varname):
                value = variables[varname]
                break
        return value

    def normalize(self):
        mapitem = {}
        for variables in self.stack:
            for key in variables.keys():
                if not mapitem.has_key(key):
                    mapitem[key] = variables[key]
        return mapitem

class TemplateManager:
    "Template management object."

    def __init__(self, template):
        self.template = template
        self.currentnode = self.template

    def __pprint(self, nodelist):
        from types import StringType
        for node in nodelist:
            if type(node) == StringType:
                print node
            else:
                print node, 'for %s in %s' % (node.seqvarnames, node.seqname)
                self.__pprint(node.nodelist)
                print '<end of block>'

    def pprint(self):
        self.__pprint(self.template.nodelist)

    def write(self, s):
        self.currentnode.write(s)

    def __crop_chunk(self, node):
        node.nodelist.append(node.getvalue())
        node.initdescriptor()

    def __append_child(self, node, child):
        node.nodelist.append(child)

    def ifblock_begin(self, varname):
        self.__crop_chunk(self.currentnode)
        ifblock = IfBlock(self.currentnode, varname)
        self.__append_child(self.currentnode, ifblock)
        self.currentnode = ifblock

    def ifblock_end(self):
        self.__crop_chunk(self.currentnode)
        self.currentnode = self.currentnode.parent

    def forblock_begin(self, seqvarnames, seqname):
        self.__crop_chunk(self.currentnode)
        forblock = ForBlock(self.currentnode, seqvarnames, seqname)
        self.__append_child(self.currentnode, forblock)
        self.currentnode = forblock

    def forblock_end(self):
        self.__crop_chunk(self.currentnode)
        self.currentnode = self.currentnode.parent

    def end_document(self):
        self.__crop_chunk(self.currentnode)

class TemplateRenderer:
    "Template renderer."

    def __init__(self, template, variable, strict):
        self.varstack = VariableStack(variable)
        self.template = template
        self.strict = strict
        self.__buffer = StringIO()

    def render(self):
        self.__build(self.template.nodelist)
        return self.__buffer.getvalue()

    def __build(self, nodelist):
        for node in nodelist:
            varmap = DictEnhanceAccessor(self.strict, self.varstack.normalize())
            if isinstance(node, IfBlock):
                if varmap[node.varname]:
                    self.__build(node.nodelist)
            elif isinstance(node, ForBlock):                
                for var in varmap[node.seqname]:
                    if type(node.seqvarnames) == str:
                        self.varstack.push({node.seqvarnames: var})
                    else:
                        self.varstack.push(dict(zip(node.seqvarnames, var)))
                    self.__build(node.nodelist)
                    self.varstack.pop()
            else:
                self.__buffer.write(node % varmap)
                
class ParseError(Exception):
    'Parse error'

def compile(template):
    "Compile from template characters."

    tpl = TemplateParser()
    hn = ProcessingHandler()
    tpl.set_processhandler(hn)    
    try:
        tpl.parse(template)
    except SyntaxError, e:
        raise SyntaxError, "line %d, in '%s' %s" % (
            tpl.lineno, tpl.chunk, e)
    return hn.template.template

def build(template, vardict=None, strict=False, **kw):
    "Building document from template and variables."

    if vardict == None: vardict = {}
    for key in kw.keys():
        vardict[key] = kw[key]
    if not isinstance(template, Template):
        template = compile(template)
    return TemplateRenderer(template, vardict, strict).render()
