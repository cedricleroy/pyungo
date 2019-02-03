

class _IO(object):

    def __init__(self, name, meta=None, contract=None):
        self._name = name
        self._meta = meta if meta is not None else {}
        self._value = None
        self._contract = None
        if contract:
            try:
                from contracts.main import parse_contract_string
            except ImportError:
                raise ImportError('pycontracts is needed to use contracts')
            self._contract = parse_contract_string(contract)

    @property
    def name(self):
        return self._name

    @property
    def contract(self):
        return self._contract

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, x):
        if self._contract:
            self._contract.check(x)
        self._value = x


class Input(_IO):

    def __init__(self, name, meta=None, contract=None):
        super(Input, self).__init__(name, meta, contract)
        self.is_arg = False
        self.is_kwarg = False
        self.is_constant = False

    def __repr__(self):
        return '<{} value={} is_arg: {} is_kwarg: {}>'.format(
            self._name, self.value, self.is_arg, self.is_kwarg
        )

    @classmethod
    def constant(cls, name, value, meta=None):
        me = cls(name, meta)
        me.value = value
        me.is_constant = True
        return me

    @classmethod
    def arg(cls, name, meta=None):
        me = cls(name, meta)
        me.is_arg = True
        return me

    @classmethod
    def kwarg(cls, name, meta=None):
        me = cls(name, meta)
        me.is_kwarg = True
        return me


class Output(_IO):

    def __repr__(self):
        return '<{} value={}>'.format(
            self._name, self.value
        )
