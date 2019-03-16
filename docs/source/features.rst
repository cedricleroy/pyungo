.. features:

********
Features
********

Sanity Check
############

**pyungo** will raise an error in the following situations:

* Circular dependencies: The :class:`~pyungo.core.Graph` need to be finite and cannot form a loop.
* All inputs needed to run a :class:`~pyungo.core.Graph` are not provided.
* Input collision: An input name provided as data in the :class:`~pyungo.core.Graph` has a
  conflict with at least of the output name.
* Duplicated outputs: Several nodes are giving output(s) that have the same name.


Add a :class:`~pyungo.core.Node` explicitely
############################################

While the simple example register nodes at import time with a decorator, it is possible to
explicitely add a node a runtime. Here is the same example:

::

    from formulas import f_my_function_1, f_my_function_2, f_my_function_3

    graph = Graph()

    graph.add_node(f_my_function_1, inputs=['d', 'a'], outputs=['e'])
    graph.add_node(f_my_function_2, inputs=['c'], outputs=['d'])
    graph.add_node(f_my_function_3, inputs=['a', 'b'], outputs=['c'])

    res = graph.calculate(data={'a': 2, 'b': 3})
    print(res)


Parallelism
###########

When resolving the dag, **pyungo** figure out nodes that can be run in parallel.
When creating a graph, we can specify the option ``parallel=True`` for running calculations
concurently when possible, using `multiprocess <https://pypi.org/project/multiprocess/>`_
module. This package is not automatically installed with **pyungo**, and will need to be
installed manually if parallelism is used. We can specify the pool size when instantiating
the :class:`~pyungo.core.Node`. This will set the maximum number of processes that will be
launched. If 3 nodes can run in parallel and just 2 processes are used, **pyungo** will run
calculation on the first 2 nodes first and will run the last one as soon as a process
will be free.

Instantiating a :class:`~pyungo.core.Graph` with a pool of 5 processes for running
calculations in parralel:

::

    graph = Graph(parallel=True, pool_size=5)

.. note::
  Running functions in parallel has a cost. Python will spend time creating / deleting
  new processes. Parallelism is recommended when at least 2 concurrent nodes have heavy
  calculations which takes a significant amount of time.

Args, Kwargs, Constants
#######################

If a function registred in a :class:`~pyungo.core.Node` contains ``args`` or ``kwargs``,
it is possible to define which data will be passed to them:

::

    graph.add_node(
        my_function,
        inputs=['a', 'b'],
        args=['c', 'd'],
        kwargs=['e', 'f'],
        outputs=['g']
    )

Sometimes, we want one of the input to be defined as a constant:

::

    @graph.register(inputs=['a', {'b': 2}], outputs=['c'])
    def f_my_function(a, b):
        return a + b

Then, only ``a`` and ``b`` will be needed when calling :class:`~pyungo.core.Graph.calculate`.

:class:`~pyungo.io.Input` and :class:`~pyungo.io.Output` objects
################################################################

Inputs and outputs can be defined directly with their names, or with :class:`~pyungo.io.Input`
/ :class:`~pyungo.io.Output` objects. This come in handy when there is extra behavior to be
attached to an input / output (e.g. ``Contracts``).

::

    from pyungo.io import Input, Output

    graph.add_node(
        my_function,
        inputs=[Input(name='a'), Input(name='b')],
        outputs=[Output(name='g')]
    )

Often, inputs are used multiple times across the nodes. In those cases, it is better to define
inputs only once (with their special features if any). It is possible to pass a list of 
:class:`~pyungo.io.Input` / :class:`~pyungo.io.Output` objects a :class:`~pyungo.core.Graph`:

::

    from pyungo.io import Input, Output

    inputs = [Input(name='a'), Input(name='b')]
    outputs = [Output(name='c'), Output(name='d')]

    graph = Graph(inputs, outputs)

    graph.add_node(
        my_function,
        inputs=['a', 'b'],
        outputs=['c']
    )

    graph.add_node(
        my_other_function,
        inputs=['c', 'b'],
        outputs=['d']
    )

.. note::
   If inputs / outputs are explicitely provided to a graph, inputs / outputs defined
   in the nodes can only be strings.

Contracts
#########

Sometimes we want to make sure a value meet specific criteria before moving forward.
**pyungo** uses `pycontracts <https://andreacensi.github.io/contracts/>`_ for attaching
contracts to inputs or outputs.

::

    from pyungo.io import Input, Output

    graph.add_node(
        my_function,
        inputs=[Input(name='a', contract='>0'), Input(name='b', contract='float')],
        outputs=[Output(name='g', contract='float')]
    )

Name mapping
############

Often, the name of the data we get are different from the ones used in the functions / models /
formulas. pyungo makes things easy providing a mapping feature. Here is an example:

::

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
