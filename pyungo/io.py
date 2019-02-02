

class Input(object):

    def __init__(self, name, meta=None):
        self._name = name
        self._meta = meta if meta is not None else {}
        self.value = None
        self.is_arg = False
        self.is_kwarg = False

    def __repr__(self):
        return '<{} value={} is_arg: {} is_kwarg: {}>'.format(
            self._name, self.value, self.is_arg, self.is_kwarg
        )

    @property
    def name(self):
        return self._name

    @classmethod
    def constant(cls, name, value, meta=None):
        me = cls(name, meta)
        me.value = value
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
