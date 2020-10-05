import functools
from pysmt.smtlib.parser import SmtLib20Parser, SmtLibScript, SmtLibCommand



class SmtLib20ParserPlus(SmtLib20Parser):
    """
    An extended parser for SMTLIB with support for datatypes (`declare-datatypes` command)
    """
    def __init__(self, *a):
        SmtLib20Parser.__init__(self, *a)

        self.commands['declare-datatypes'] = self._cmd_declare_datatypes

    def _cmd_declare_datatypes(self, current, tokens):
        """(declare-datatypes (<param>*) ((<name> (<ctor> (<arg> <type>)*)*)*))"""

        self.consume_opening(tokens, current)

        params = []
        cur = tokens.consume()
        while cur != ')':
            params.append(cur)
            cur = tokens.consume()

        defs = []
        self.consume_opening(tokens, current)
        cur = tokens.consume()
        while cur != ')':
            defs.append(self._subcmd_datatype(current, tokens))
            cur = tokens.consume()

        self.consume_closing(tokens, current)

        return SmtLibCommand(current, [params, defs])

    def _subcmd_datatype(self, current, tokens):
        """(<name> (<ctor> (<arg> <type>)*)*)"""
        name = self.parse_atom(tokens, current)
        type_ = self.env.type_manager.Type(name)
        self.cache.bind(name, type_)

        ctors = []
        cur = tokens.consume()
        while cur != ')':
            ctor = self.parse_atom(tokens, current)
            namedparams = self.parse_named_params_inline(tokens, current)  # also consumes the final ')'
            ctor_type = self.env.type_manager.FunctionType(type_, [t for (_,t) in namedparams])
            v = self._get_var(ctor, ctor_type)
            ctors.append((v, namedparams))
            self._declare_accessors(type_, namedparams)
            if namedparams: v = functools.partial(self._function_call_helper, v)
            self.cache.bind(ctor, v)
            cur = tokens.consume()

        return (type_, ctors)

    def _declare_accessors(self, datatype, namedparams):
        for (name, type_) in namedparams:
            accessor_type = self.env.type_manager.FunctionType(type_, [datatype])
            v = self._get_var(name, accessor_type)
            self.cache.bind(name, functools.partial(self._function_call_helper, v))

    def parse_named_params_inline(self, tokens, command):
        """Parses a list of names and type from the tokens"""
        current = tokens.consume(command)
        res = []
        while current != ")":
            vname = self.parse_atom(tokens, command)
            typename = self.parse_type(tokens, command)
            res.append((vname, typename))
            self.consume_closing(tokens, command)
            current = tokens.consume(command)
        return res
