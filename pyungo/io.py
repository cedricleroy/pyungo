

class _BaseInputOutput:
    def __init__(self, name, type_=None, unit=None, description=None):
        self._name = name
        self._type = type_
        self._unit = unit
        self._description = description

    @property
    def name(self):
        return self._name


class Input(_BaseInputOutput):
    pass


class Output(_BaseInputOutput):
    pass
