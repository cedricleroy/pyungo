""" Input / Output module

Inputs / Outputs objects used to represent functions inputs / outputs
"""


class _IO(object):
    """ IO Base class for inputs and outputs

    Args:
        name (str): The variable name of the input / output
        meta (dict): Not used yet
        contract (str): Optional contract rule used by pycontracts
    """

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
        """ When setting a value, we check the contract when applicable """
        if self._contract:
            self._contract.check(x)
        self._value = x


class Input(_IO):
    """ Object representing a function input

    Args:
        name (str): The variable name of the input / output
        meta (dict): Not used yet
        contract (str): Optional contract rule used by pycontracts
    """

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
        """ Alternate constructor for inputs that are constant

        Args:
            name (str): The variable name of the input / output
            value: The defined constant value, can be anything
            meta (dict): Not used yet
        """
        me = cls(name, meta)
        me.value = value
        me.is_constant = True
        return me

    @classmethod
    def arg(cls, name, meta=None):
        """ Alternate constructor for args

        Args:
            name (str): The variable name of the input / output
            meta (dict): Not used yet
        """
        me = cls(name, meta)
        me.is_arg = True
        return me

    @classmethod
    def kwarg(cls, name, meta=None):
        """ Alternate constructor for kwargs

        Args:
            name (str): The variable name of the input / output
            meta (dict): Not used yet
        """
        me = cls(name, meta)
        me.is_kwarg = True
        return me


class Output(_IO):
    """ Object representing a function output

    Args:
        name (str): The variable name of the input / output
        meta (dict): Not used yet
        contract (str): Optional contract rule used by pycontracts
    """

    def __repr__(self):
        return '<{} value={}>'.format(
            self._name, self.value
        )
