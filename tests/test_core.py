import pytest

from pyungo.core import Graph, PyungoError
from pyungo.io import Input, Output


def test_simple():
    graph = Graph()

    @graph.register(inputs=['a', 'b'], outputs=['c'])
    def f_my_function(a, b):
        return a + b

    @graph.register(inputs=['d', 'a'], outputs=['e'])
    def f_my_function3(d, a):
        return d - a

    @graph.register(inputs=['c'], outputs=['d'])
    def f_my_function2(c):
        return c / 10.

    res = graph.calculate(data={'a': 2, 'b': 3})
    assert res == -1.5
    assert graph.data['e'] == -1.5

    # make sure it is indepodent
    res = graph.calculate(data={'a': 2, 'b': 3})
    assert res == -1.5
    assert graph.data['e'] == -1.5


def test_simple_without_decorator():
    graph = Graph()

    def f_my_function(a, b):
        return a + b

    def f_my_function3(d, a):
        return d - a

    def f_my_function2(c):
        return c / 10.

    graph.add_node(f_my_function, inputs=['a', 'b'], outputs=['c'])
    graph.add_node(f_my_function3, inputs=['d', 'a'], outputs=['e'])
    graph.add_node(f_my_function2, inputs=['c'], outputs=['d'])

    res = graph.calculate(data={'a': 2, 'b': 3})

    assert res == -1.5
    assert graph.data['e'] == -1.5


def test_simple_parralel():
    """ TODO: We could mock and make sure things are called correctly """

    graph = Graph(parallel=True)

    def f_my_function(a, b):
        return a + b

    def f_my_function3(d, a):
        return d - a

    def f_my_function2(c):
        return c / 10.

    graph.add_node(f_my_function, inputs=['a', 'b'], outputs=['c'])
    graph.add_node(f_my_function3, inputs=['d', 'a'], outputs=['e'])
    graph.add_node(f_my_function2, inputs=['c'], outputs=['d'])
    graph.add_node(f_my_function2, inputs=['c'], outputs=['f'])
    graph.add_node(f_my_function2, inputs=['c'], outputs=['g'])

    res = graph.calculate(data={'a': 2, 'b': 3})

    assert res == -1.5


def test_multiple_outputs():
    graph = Graph()

    @graph.register(inputs=['a', 'b'], outputs=['c', 'd'])
    def f_my_function(a, b):
        return a + b, 2 * b

    @graph.register(inputs=['c', 'd'], outputs=['e'])
    def f_my_function2(c, d):
        return c + d

    res = graph.calculate(data={'a': 2, 'b': 3})

    assert res == 11
    assert graph.data['e'] == 11


def test_same_output_names():
    graph = Graph()

    @graph.register(inputs=['a', 'b'], outputs=['c'])
    def f_my_function(a, b):
        return a + b

    with pytest.raises(PyungoError) as err:
        @graph.register(inputs=['c'], outputs=['c'])
        def f_my_function2(c):
            return c / 10
    
    assert 'c output already exist' in str(err.value)


def test_missing_input():
    graph = Graph()

    @graph.register(inputs=['a', 'b'], outputs=['c'])
    def f_my_function(a, b):
        return a + b

    with pytest.raises(PyungoError) as err:
        graph.calculate(data={'a': 6})
    
    assert "The following inputs are needed: ['b']" in str(err.value)


def test_inputs_not_used():
    graph = Graph()

    @graph.register(inputs=['a', 'b'], outputs=['c'])
    def f_my_function(a, b):
        return a + b

    with pytest.raises(PyungoError) as err:
        graph.calculate(data={'a': 6, 'b': 4, 'e': 7})
    
    assert "The following inputs are not used by the model: ['e']" in str(err.value)


def test_inputs_collision():
    graph = Graph()

    @graph.register(inputs=['a', 'b'], outputs=['c'])
    def f_my_function(a, b):
        return a + b

    with pytest.raises(PyungoError) as err:
        graph.calculate(data={'a': 6, 'b': 4, 'c': 7})
    
    assert "The following inputs are already used in the model: ['c']" in str(err.value)


def test_circular_dependency():
    graph = Graph()

    @graph.register(inputs=['a', 'b', 'd'], outputs=['c'])
    def f_my_function(a, b):
        return a + b

    @graph.register(inputs=['c'], outputs=['d'])
    def f_my_function2(c):
        return c / 2.

    with pytest.raises(PyungoError) as err:
        graph.calculate(data={'a': 6, 'b': 4})

    assert "A cyclic dependency exists amongst" in str(err.value)


def test_iterable_on_single_output():
    graph = Graph()

    @graph.register(inputs=['a', 'b'], outputs=['c'])
    def f_my_function(a, b):
        return list(range(a)) + [b]

    res = graph.calculate(data={'a': 2, 'b': 3})

    assert res == [0, 1, 3]
    assert graph.data['c'] == [0, 1, 3]


def test_multiple_outputs_with_iterable():
    graph = Graph()

    @graph.register(inputs=['a', 'b'], outputs=['c', 'd'])
    def f_my_function(a, b):
        return list(range(a)) + [b], b * 10

    res = graph.calculate(data={'a': 2, 'b': 3})

    assert isinstance(res, tuple) is True
    assert graph.data['c'] == [0, 1, 3]
    assert graph.data['d'] == 30
    assert res[0] == [0, 1, 3]
    assert res[1] == 30


def test_args_kwargs():
    graph = Graph()

    @graph.register(
        inputs=['a', 'b'],
        args=['c'],
        kwargs=['d'],
        outputs=['e']
    )
    def f_my_function(a, b, *args, **kwargs):
        return a + b + args[0] + kwargs['d']

    res = graph.calculate(data={'a': 2, 'b': 3, 'c': 4, 'd': 5})

    assert res == 14
    assert graph.data['e'] == 14


def test_dag_pretty_print():
    graph = Graph()

    @graph.register(inputs=['a', 'b'], outputs=['c'])
    def f_my_function(a, b):
        return a + b

    @graph.register(inputs=['d', 'a'], outputs=['e'])
    def f_my_function3(d, a):
        return d - a

    @graph.register(inputs=['c'], outputs=['d'])
    def f_my_function2(c):
        return c / 10.

    expected = ['f_my_function', 'f_my_function2', 'f_my_function3']
    dag = graph.dag
    for i, fct_name in enumerate(expected):
        assert dag[i][0].fct_name == fct_name


def test_missing_inputs():

    graph = Graph(parallel=True)

    def f_my_function(a, b):
        return a + b

    with pytest.raises(PyungoError) as err:
        graph.add_node(f_my_function, outputs=['c'])
    assert "Missing inputs parameter" in str(err.value)

    with pytest.raises(PyungoError) as err:
        graph.add_node(f_my_function, inputs=['a', 'b'])
    assert "Missing outputs parameter" in str(err.value)


def test_passing_data_to_node_definition():

    graph = Graph()

    @graph.register(inputs=['a', {'b': 2}], outputs=['c'])
    def f_my_function(a, b):
        return a + b

    res = graph.calculate(data={'a': 5})
    assert res == 7


def test_wrong_input_type():

    graph = Graph()

    with pytest.raises(PyungoError) as err:
        @graph.register(inputs=['a', {'b'}], outputs=['c'])
        def f_my_function(a, b):
            return a + b

    assert "inputs need to be of type Input, str or dict" in str(err.value)


def test_empty_input_dict():

    graph = Graph()

    with pytest.raises(PyungoError) as err:
        @graph.register(inputs=['a', {}], outputs=['c'])
        def f_my_function(a, b):
            return a + b

    assert "dict inputs should have only one key and cannot be empty" in str(err.value)


def test_multiple_keys_input_dict():

    graph = Graph()

    with pytest.raises(PyungoError) as err:
        @graph.register(inputs=['a', {'b': 1, 'c': 2}], outputs=['c'])
        def f_my_function(a, b):
            return a + b

    assert "dict inputs should have only one key and cannot be empty" in str(err.value)


def test_Input_type_input():
    graph = Graph()

    @graph.register(
        inputs=[Input(name='a'), 'b'],
        outputs=['c']
    )
    def f_my_function(a, b):
        return a + b

    res = graph.calculate(data={'a': 2, 'b': 3})

    assert res == 5


def test_contract_inputs():

    from contracts import ContractNotRespected

    graph = Graph()

    @graph.register(
        inputs=[Input(name='a', contract='int,>0'), 'b'],
        outputs=['c']
    )
    def f_my_function(a, b):
        return a + b

    res = graph.calculate(data={'a': 2, 'b': 3})
    assert res == 5
    res = graph.calculate(data={'a': 2, 'b': 3})
    assert res == 5

    with pytest.raises(ContractNotRespected) as err:
        res = graph.calculate(data={'a': -2, 'b': 3})

    assert "Condition -2 > 0 not respected" in str(err.value)


def test_contract_outputs():

    from contracts import ContractNotRespected

    graph = Graph()

    @graph.register(
        inputs=['a', 'b'],
        outputs=[Output('c', contract='int,>0')]
    )
    def f_my_function(a, b):
        return a + b

    res = graph.calculate(data={'a': 2, 'b': 3})
    assert res == 5

    with pytest.raises(ContractNotRespected) as err:
        res = graph.calculate(data={'a': -4, 'b': 3})

    assert "Condition -1 > 0 not respected" in str(err.value)
