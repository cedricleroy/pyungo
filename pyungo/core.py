from functools import reduce
from copy import deepcopy
import logging
import numpy as np

LOGGER = logging.getLogger(__name__)
HANDLER = logging.StreamHandler()
LOGGER.addHandler(HANDLER)


class PyungoError(Exception):
    pass


def topological_sort(data):
    for key in data:
        data[key] = set(data[key])
    for k, v in data.items():
        v.discard(k)  # ignore self dependencies
    extra_items_in_deps = reduce(set.union, data.values()) - set(data.keys())
    data.update({item: set() for item in extra_items_in_deps})
    while True:
        ordered = set(item for item, dep in data.items() if not dep)
        if not ordered:
            break
        yield sorted(ordered)
        data = {item: (dep - ordered) for item, dep in data.items()
                if item not in ordered}
    if data:
        raise PyungoError('A cyclic dependency exists amongst {}'.format(data))


class Node:
    ID = 0

    def __init__(self, fct, input_names, output_names, args=None, kwargs=None):
        Node.ID += 1
        self._id = str(Node.ID)
        self._fct = fct
        self._input_names = input_names
        self._args = args if args else []
        self._kwargs = kwargs if kwargs else []
        self._output_names = output_names

    def __repr__(self):
        return 'Node({}, <{}>, {}, {})'.format(
            self._id, self._fct.__name__,
            self._input_names, self._output_names
        )

    def __call__(self, args, **kwargs):
        return self._fct(*args, **kwargs)

    @property
    def id(self):
        return self._id

    @property
    def input_names(self):
        input_names = self._input_names
        input_names.extend(self._args)
        input_names.extend(self._kwargs)
        return input_names

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def output_names(self):
        return self._output_names

    @property
    def fct_name(self):
        return self._fct.__name__


class Graph:
    def __init__(self):
        self._nodes = []
        self._data = None

    @property
    def data(self):
        return self._data

    @property
    def sim_inputs(self):
        inputs = []
        for node in self._nodes:
            inputs.extend(node.input_names)
        return inputs

    @property
    def sim_outputs(self):
        outputs = []
        for node in self._nodes:
            outputs.extend(node.output_names)
        return outputs

    @property
    def dag(self):
        """ return the ordered nodes graph """
        ordered_nodes = []
        for node_ids in topological_sort(self._dependencies()):
            nodes = [self._get_node(node_id) for node_id in node_ids]
            ordered_nodes.append(nodes)
        return ordered_nodes

    def _register(self, f, **kwargs):
        input_names = kwargs.get('inputs')
        args_names = kwargs.get('args')
        kwargs_names = kwargs.get('kwargs')
        output_names = kwargs.get('outputs')
        self._create_node(
            f, input_names, output_names, args_names, kwargs_names
        )

    def register(self, **kwargs):
        def decorator(f):
            self._register(f, **kwargs)
            return f
        return decorator

    def add_node(self, function, **kwargs):
        self._register(function, **kwargs)

    def _create_node(self, fct, input_names, output_names, args_names, kwargs_names):
        node = Node(fct, input_names, output_names, args_names, kwargs_names)
        # assume that we cannot have two nodes with the same output names
        for n in self._nodes:
            for out_name in n.output_names:
                if out_name in node.output_names:
                    msg = '{} output already exist'.format(out_name)
                    raise PyungoError(msg)
        self._nodes.append(node)

    def _dependencies(self):
        dep = {}
        for node in self._nodes:
            d = dep.setdefault(node.id, [])
            for inp in node.input_names:
                for node2 in self._nodes:
                    if inp in node2.output_names:
                        d.append(node2.id)
        return dep

    def _get_node(self, id_):
        for node in self._nodes:
            if node.id == id_:
                return node

    def _check_inputs(self, data):
        data_inputs = set(data.keys())
        diff = data_inputs - (data_inputs - set(self.sim_outputs))
        if diff:
            msg = 'The following inputs are already used in the model: {}'.format(list(diff))
            raise PyungoError(msg)
        inputs_to_provide = set(self.sim_inputs) - set(self.sim_outputs)
        diff = inputs_to_provide - data_inputs
        if diff:
            msg = 'The following inputs are needed: {}'.format(list(diff))
            raise PyungoError(msg)
        diff = data_inputs - inputs_to_provide
        if diff:
            msg = 'The following inputs are not used by the model: {}'.format(list(diff))
            LOGGER.warning(msg)

    def calculate(self, data):
        self._data = deepcopy(data)
        self._check_inputs(data)
        dep = self._dependencies()
        sorted_dep = topological_sort(dep)
        for items in sorted_dep:
            for item in items:
                node = self._get_node(item)
                args = [i_name for i_name in node.input_names if i_name not in node.kwargs]
                data_to_pass = []
                for arg in args:
                    data_to_pass.append(self._data[arg])
                kwargs_to_pass = {}
                for kwarg in node.kwargs:
                    kwargs_to_pass[kwarg] = self._data[kwarg]
                res = node(data_to_pass, **kwargs_to_pass)
                try:
                    iter(res)
                    # Remove single dimensional entries from the shape of array
                    res = np.squeeze(res)
                except TypeError:
                    # Not iterable: keep it as it is
                    pass
                # Save the returned values according to # of expected outputs
                if len(node.output_names) > 1:
                    for i, name in enumerate(node.output_names):
                        self._data[name] = np.squeeze(res[i])
                else:
                    self._data[node.output_names[0]] = np.squeeze(res)
        try:
            if len(res) == 1:
                return res[0]
        except TypeError:
            pass
        return res
