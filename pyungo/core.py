""" Main module containing Graph / Node classes """

import uuid
from copy import deepcopy
import datetime as dt
from functools import reduce
import logging

from pyungo.io import Input, Output


logging.basicConfig()
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


try:
    from multiprocess import Pool
except ImportError:
    msg = 'multiprocess is not installed and needed for parralelism'
    LOGGER.warning(msg)


class PyungoError(Exception):
    """ pyungo custom exception """
    pass


def topological_sort(data):
    """ Topological sort algorithm

    Args:
        data (dict): dictionnary representing dependencies
            Example: {'a': ['b', 'c']} node id 'a' depends on
            node id 'b' and 'c'

    Returns:
        ordered (list): list of list of node ids
            Example: [['a'], ['b', 'c'], ['d']]
            The sequence is representing the order to be run.
            The nested lists are node ids that can be run in parallel

    Raises:
        PyungoError: In case a cyclic dependency exists
    """
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
    """ Node object (aka vertex in graph theory)

    Args:
        fct (function): The Python function attached to the node
        inputs (list): List of inputs (which can be `Input`, `str` or `dict`)
        outputs (list): List of outputs (`Output` or `str`)
        args (list): Optional list of args
        kwargs (list): Optional list of kwargs

    Raises:
        PyungoError: In case inputs have the wrong type
    """

    def __init__(self, fct, inputs, outputs, args=None, kwargs=None):
        self._id = str(uuid.uuid4())
        self._fct = fct
        self._inputs = []
        self._process_inputs(inputs)
        self._args = args if args else []
        self._process_inputs(self._args, is_arg=True)
        self._kwargs = kwargs if kwargs else []
        self._process_inputs(self._kwargs, is_kwarg=True)
        self._outputs = []
        self._process_outputs(outputs)

    def __repr__(self):
        return 'Node({}, <{}>, {}, {})'.format(
            self._id, self._fct.__name__,
            self.input_names, self.output_names
        )

    def __call__(self, *args, **kwargs):
        """ run the function attached to the node, and store the result """
        t1 = dt.datetime.utcnow()
        res = self._fct(*args, **kwargs)
        t2 = dt.datetime.utcnow()
        LOGGER.info('Ran {} in {}'.format(self, t2-t1))
        # save results to outputs
        if len(self._outputs) == 1:
            self._outputs[0].value = res
        else:
            for i, out in enumerate(self._outputs):
                out.value = res[i]
        return res

    @property
    def id(self):
        """ return the unique id of the node """
        return self._id

    @property
    def input_names(self):
        """ return a list of all input names """
        input_names = [i.name for i in self._inputs]
        return input_names

    @property
    def input_names_without_constants(self):
        """ return list of input names, when inputs are not constants """
        input_names = [i.name for i in self._inputs if not i.is_constant]
        return input_names

    @property
    def kwargs(self):
        """ return the list of kwargs """
        return self._kwargs

    @property
    def output_names(self):
        """ return a list of output names """
        return [o.name for o in self._outputs]

    @property
    def fct_name(self):
        """ return the function name """
        return self._fct.__name__

    def _process_inputs(self, inputs, is_arg=False, is_kwarg=False):
        """ converter data passed to Input objects and store them """
        for input_ in inputs:
            if isinstance(input_, Input):
                new_input = input_
            elif isinstance(input_, str):
                if is_arg:
                    new_input = Input.arg(input_)
                elif is_kwarg:
                    new_input = Input.kwarg(input_)
                else:
                    new_input = Input(input_)
            elif isinstance(input_, dict):
                if len(input_) != 1:
                    msg = 'dict inputs should have only one key and cannot be empty'
                    raise PyungoError(msg)
                key = next(iter(input_))
                value = input_[key]
                new_input = Input.constant(key, value)
            else:
                msg = 'inputs need to be of type Input, str or dict'
                raise PyungoError(msg)
            self._inputs.append(new_input)

    def _process_outputs(self, outputs):
        """ converter data passed to Output objects and store them """
        for output in outputs:
            if isinstance(output, Output):
                new_output = output
            elif isinstance(output, str):
                new_output = Output(output)
            self._outputs.append(new_output)

    def set_value_to_input(self, input_name, value):
        """ set a value to the targeted input name

        Args:
            input_name (str): Name of the input
            value: value to be assigned to the input

        Raises:
            PyungoError: In case the input name is unknown
        """
        for input_ in self._inputs:
            if input_.name == input_name:
                input_.value = value
                return
        msg = 'input "{}" does not exist in this node'.format(input_name)
        raise PyungoError(msg)

    def run_with_loaded_inputs(self):
        """ Run the node with the attached function and loaded input values """
        args = [i.value for i in self._inputs if not i.is_arg and not i.is_kwarg]
        args.extend([i.value for i in self._inputs if i.is_arg])
        kwargs = {i.name: i.value for i in self._inputs if i.is_kwarg}
        return self(*args, **kwargs)


class Graph:
    """ Graph object, collection of related nodes

    Args:
        parallel (bool): Parallelism flag
        pool_size (int): Size of the pool in case parallelism is enabled

    Raises:
        ImportError will raise in case parallelism is chosen and `multiprocess`
            not installed
    """
    def __init__(self, parallel=False, pool_size=2):
        self._nodes = {}
        self._data = None
        self._parallel = parallel
        self._pool_size = pool_size
        self._sorted_dep = None
        if parallel:
            try:
                import multiprocess
            except ImportError:
                msg = 'multiprocess package is needed for parralelism'
                raise ImportError(msg)

    @property
    def data(self):
        """ return the data of the graph (inputs + outputs) """
        return self._data

    @property
    def sim_inputs(self):
        """ return input names of every nodes """
        inputs = []
        for node in self._nodes.values():
            inputs.extend(node.input_names_without_constants)
        return inputs

    @property
    def sim_outputs(self):
        """ return output names of every nodes """
        outputs = []
        for node in self._nodes.values():
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

    @staticmethod
    def run_node(node):
        """ run the node

        Args:
            node (Node): The node to run

        Returns:
            results (tuple): node id, node output values
        """
        return (node.id, node.run_with_loaded_inputs())

    def _register(self, f, **kwargs):
        """ check if all needed inputs are there and create a new node """
        input_names = kwargs.get('inputs')
        if not input_names:
            raise PyungoError('Missing inputs parameter')
        output_names = kwargs.get('outputs')
        if not output_names:
            raise PyungoError('Missing outputs parameters')
        args_names = kwargs.get('args')
        kwargs_names = kwargs.get('kwargs')
        self._create_node(
            f, input_names, output_names, args_names, kwargs_names
        )

    def register(self, **kwargs):
        """ register decorator """
        def decorator(f):
            self._register(f, **kwargs)
            return f
        return decorator

    def add_node(self, function, **kwargs):
        """ explicit method to add a node to the graph

        Args:
            function (function): Python function attached to the node
            inputs (list): List of inputs (Input, str, or dict)
            outputs (list): List of outputs (Output or str)
            args (list): List of optional args
            kwargs (list): List of optional kwargs
        """
        self._register(function, **kwargs)

    def _create_node(self, fct, input_names, output_names, args_names, kwargs_names):
        """ create a save the node to the graph """
        node = Node(fct, input_names, output_names, args_names, kwargs_names)
        # assume that we cannot have two nodes with the same output names
        for n in self._nodes.values():
            for out_name in n.output_names:
                if out_name in node.output_names:
                    msg = '{} output already exist'.format(out_name)
                    raise PyungoError(msg)
        self._nodes[node.id] = node

    def _dependencies(self):
        """ return dependencies among the nodes """
        dep = {}
        for node in self._nodes.values():
            d = dep.setdefault(node.id, [])
            for inp in node.input_names:
                for node2 in self._nodes.values():
                    if inp in node2.output_names:
                        d.append(node2.id)
        return dep

    def _get_node(self, id_):
        """ get a node from its id """
        return self._nodes[id_]

    def _check_inputs(self, data):
        """ make sure data inputs provided are good enough """
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
            raise PyungoError(msg)

    def _topological_sort(self):
        """ run topological sort algorithm """
        self._sorted_dep = list(topological_sort(self._dependencies()))

    def calculate(self, data):
        """ run graph calculations """
        t1 = dt.datetime.utcnow()
        LOGGER.info('Starting calculation...')
        self._data = deepcopy(data)
        self._check_inputs(data)
        if not self._sorted_dep:
            self._topological_sort()
        for items in self._sorted_dep:
            # loading node with inputs
            for item in items:
                node = self._get_node(item)
                args = [i_name for i_name in node.input_names_without_constants]
                for arg in args:
                    node.set_value_to_input(arg, self._data[arg])
            # running nodes
            if self._parallel:
                pool = Pool(self._pool_size)
                results = pool.map(
                    Graph.run_node,
                    [self._get_node(i) for i in items]
                )
                pool.close()
                pool.join()
                results = {k: v for k, v in results}
            else:
                results = {}
                for item in items:
                    node = self._get_node(item)
                    res = node.run_with_loaded_inputs()
                    results[node.id] = res
            # save results
            for item in items:
                node = self._get_node(item)
                res = results[node.id]
                if len(node.output_names) == 1:
                    self._data[node.output_names[0]] = res
                else:
                    for i, out in enumerate(node.output_names):
                        self._data[out] = res[i]
        t2 = dt.datetime.utcnow()
        LOGGER.info('Calculation finished in {}'.format(t2-t1))
        return res
