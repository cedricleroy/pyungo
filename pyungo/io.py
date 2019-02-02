

class Input(object):

    def __init__(self, name, meta=None, contract=None):
        self._name = name
        self._meta = meta if meta is not None else {}
        self.value = None
        self.is_arg = False
        self.is_kwarg = False
        self._contract = None
        self.is_constant = False
        if contract:
            try:
                from contracts.main import parse_contract_string
            except ImportError:
                raise ImportError('pycontracts is needed to use contracts')
            self._contract = parse_contract_string(contract)

    def __repr__(self):
        return '<{} value={} is_arg: {} is_kwarg: {}>'.format(
            self._name, self.value, self.is_arg, self.is_kwarg
        )

    @property
    def name(self):
        return self._name

    @property
    def contract(self):
        return self._contract

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

    def check_contract(self):
        self._contract.check(self.value)
