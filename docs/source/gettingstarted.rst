.. gettingstarted:

***************
Getting Started
***************

**pyungo** is a lightweight library to link a set of dependent functions together,
and execute them in an ordered manner.

**pyungo** is built around **Graphs** and **Nodes** used in a
`DAG <https://en.wikipedia.org/wiki/Directed_acyclic_graph>`_ (Directed Acyclic Graph).
A :class:`~pyungo.core.Node` represent a function being run with a defined set of inputs
and returning one or several outputs. A :class:`~pyungo.core.Graph` is a collection of
**Nodes** where data can flow in an logical manner, the output of one node serving as
input of another.

Simple example
##############

::

    graph = Graph()

    @graph.register(inputs=['d', 'a'], outputs=['e'])
    def f_my_function_2(d, a):
        return d - a

    @graph.register(inputs=['c'], outputs=['d'])
    def f_my_function_1(c):
        return c / 10.

    @graph.register(inputs=['a', 'b'], outputs=['c'])
    def f_my_function_3(a, b):
        return a + b

    res = graph.calculate(data={'a': 2, 'b': 3})
    print(res)


**pyungo** is registering the functions at import time. It then resolve the DAG and figure out
the sequence at which the functions have to be run per their inputs / outputs. In this case,
it will be function 3 then 1 and finally 2.

The ordered :class:`~pyungo.core.Graph` is run with calculate, with the given data. It returns
the output of the last function being run (``e``), but all intermediate results are also
available in the graph instance.

The result will be `(a + b) / 10 - a = -1.5`
