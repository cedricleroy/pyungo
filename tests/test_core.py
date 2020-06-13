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


def test_simple_parallel():
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


def test_provide_inputs_outputs():
    inputs = [Input('a'), Input('b')]
    outputs = [Output('c')]

    graph = Graph(inputs=inputs, outputs=outputs)

    @graph.register(
        inputs=['a', 'b'],
        outputs=['c']
    )
    def f_my_function(a, b):
        return a + b

    res = graph.calculate(data={'a': 2, 'b': 3})
    assert res == 5


def test_provide_inputs_outputs_already_defined():
    inputs = [Input('a'), Input('b')]
    outputs = [Output('c')]

    graph = Graph(inputs=inputs, outputs=outputs)

    with pytest.raises(TypeError) as err:
        @graph.register(
            inputs=['a', 'b'],
            outputs=[Output('c')]
        )
        def f_my_function(a, b):
            return a + b

    msg = "You cannot use Input / Output in a Node if already defined"
    assert msg in str(err.value)


def test_map():
    graph = Graph()

    @graph.register(
        inputs=[Input('a', map='q'), Input('b', map='w')],
        outputs=[Output('c', map='e')]
    )
    def f_my_function(a, b):
        return a + b

    res = graph.calculate(data={'q': 2, 'w': 3})
    assert res == 5
    assert graph.data['e'] == 5


def test_schema():
    from jsonschema import ValidationError

    schema = {
        "type": "object",
        "properties": {
            "a": {"type": "number"},
            "b": {"type": "number"}
        }
    }

    graph = Graph(schema=schema)

    @graph.register(
        inputs=['a', 'b'],
        outputs=['c']
    )
    def f_my_function(a, b):
        return a + b

    with pytest.raises(ValidationError) as err:
        graph.calculate(data={'a': 1, 'b': '2'})

    msg = "'2' is not of type 'number'"
    assert msg in str(err.value)

    res = graph.calculate(data={'a': 1, 'b': 2})
    assert res == 3


def test_optional_kwargs():
    graph = Graph()

    @graph.register(inputs=['a'], kwargs=['b'], outputs=['c'])
    def f(a, b=2):
        return a + b

    res = graph.calculate(data={'a': 1})

    assert res == 3
    assert graph.data['c'] == 3


def test_no_explicit_inputs_outputs_simple():
    graph = Graph()

    @graph.register()
    def f(a, b):
        c = a + b
        return c

    res = graph.calculate(data={'a': 1, 'b': 2})

    assert res == 3
    assert graph.data['c'] == 3


def test_no_explicit_inputs_outputs_tuple():
    graph = Graph()

    @graph.register()
    def f(a, b, c, d):
        e = a + b
        f = c - d
        return e, f

    res = graph.calculate(data={'a': 1, 'b': 2, 'c': 3, 'd': 4})

    assert res == (3, -1)
    assert graph.data['e'] == 3
    assert graph.data['f'] == -1


def test_no_explicit_inputs_outputs_bad_return():
    graph = Graph()

    with pytest.raises(PyungoError) as err:
        @graph.register()
        def f(a, b):
            return a + b

    expected = ('Variable name or Tuple of variable '
                'names are expected, got BinOp')
    assert str(err.value) == expected


def test_no_deepcopy_doesnt_copy():
    graph = Graph(do_deepcopy=False)

    @graph.register()
    def f(c, e):
        c['a'] += 1
        f = c['a'] + e
        return f

    d = {'a': 1}
    res = graph.calculate(data={'c': d, 'e': 2})
    assert res == 4
    res = graph.calculate(data={'c': d, 'e': 2})
    assert res == 5


def test_no_side_effects_if_deepcopy_enabled():
    graph = Graph(do_deepcopy=True)

    @graph.register()
    def f(c, e):
        c['a'] += 1
        f = c['a'] + e
        return f

    d = {'a': 1}
    res = graph.calculate(data={'c': d, 'e': 2})
    assert res == 4
    res = graph.calculate(data={'c': d, 'e': 2})
    assert res == 4


def test_no_side_effects_if_deepcopy_is_left_at_default():
    graph = Graph()

    @graph.register()
    def f(c, e):
        c['a'] += 1
        f = c['a'] + e
        return f

    d = {'a': 1}
    res = graph.calculate(data={'c': d, 'e': 2})
    assert res == 4
    res = graph.calculate(data={'c': d, 'e': 2})
    assert res == 4
