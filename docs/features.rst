.. features:

********
Features
********

Sanity Check
############

**pyungo** will raise an error in the following situations:

* Circular dependencies: The Graph need to be finite and cannot form a loop.
* All inputs needed to run a graph are not provided.
* Input collision: An input name provided as data in the graph has a conflict with at least
  of the output name.
* Duplicated outputs: Several nodes are giving output(s) that have the same name.


Add a node explicitely
######################

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
concurently when possible, using multiprocess module. This package is not automatically
installed with pyungo, and will need to be installed manually if parallelism is used. We can
specify the pool size when instantiating the Graph. This will set the maximum number of processes
that will be launched. If 3 nodes can run in parallel and just 2 processes are used, **pyungo**
will run calculation on the first 2 nodes first and will run the last one as soon as a process
will be free.

Instantiating a Graph with a pool of 5 processes for running calculations in parralel:

::

    graph = Graph(parallel=True, pool_size=5)

_Note:_ Running functions in parallel has a cost. Python will spend time creating / deleting
new processes. Parallelism is recommended when at least 2 concurrent nodes have heavy
calculations which takes a significant amount of time.

Args, Kwargs, Constants
#######################

If a function registred in a Node contains ``args`` or ``kwargs``, it is possible to define which
data will be passed to them:

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

Then, only ``a`` and ``b`` will be needed when calling ``graph.calculate``

``Input`` and ``Output`` objects
################################

Inputs and outputs can be defined directly with their names, or with ``Input`` / ``Output``
objects. This come in handy when there is extra behavior to be attached to an input /
output (e.g. ``Contracts``).

::

    from pyungo.io import Input, Output

    graph.add_node(
        my_function,
        inputs=[Input(name='a'), Input(name='b')],
        outputs=[Output(name='g')]
    )

Contracts
#########

Sometimes we want to make sure a value meet specific criteria before moving forward.
**pyungo** uses ``pycontracts`` for attaching contracts to inputs or outputs.

::

    from pyungo.io import Input, Output

    graph.add_node(
        my_function,
        inputs=[Input(name='a', contract='>0'), Input(name='b', contract='float')],
        outputs=[Output(name='g', contract='float')]
    )
