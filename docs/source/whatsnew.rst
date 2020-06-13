.. whatsnew:

**********
What's New
**********

These are new features and improvements notes for each release.

v0.9.0 (June 13, 2020)
======================

* Drop support / compatibility for Python 2.7.
* inputs / outputs names are now optional.::

    @graph.register()
    def f_my_function(a, b):
        c = a + b
        return c

* Additional argument to ``Graph`` to prevent inputs deepcopy (`@Tosa95 <https://github.com/Tosa95>`_).
  This is useful when having large inputs when the ``deepcopy`` might be slow, but remove inputs 
  immutability.

v0.8.1 (October 27, 2019)
=========================

* Allow optional input data for kwargs (`@veronicaguo <https://github.com/veronicaguo>`_)

v0.8.0 (March 17, 2019)
=======================

* Can pass list of ``Input`` / ``Output`` to ``Graph``.

* Names mapping.

* Inputs validation with JSON Schema.

* Some misc. refactoring and styling.

v0.7.0 (February 10, 2019)
==========================

* Refactoring, and introduction of ``Input`` and ``Output`` objects.

* Contracts feature.::

    graph.add_node(
        my_function,
        inputs=[Input(name='a', contract='>0'), Input(name='b', contract='float')],
        outputs=[Output(name='g', contract='float')]
    )

* Nodes IDs refactoring (now uses uuid).

* Run topological sort only when needed.

* Everything accessible from `pyungo` __init__ (`@nelsontodd <https://github.com/nelsontodd>`_)

* Docstrings / Sphinx doc / GitHub page


v0.6.0 (July 6, 2018)
=====================

* Fix "false parallelism" implementation. This require an optional dependency (`multiprocess`
  module) which is more friendly to work with stateful objects and multiprocessing.

* Ability to pass predefined inputs at the node definition::

    @graph.register(inputs=['a', {'b': 2}], outputs=['c'])
    def f_my_function(a, b):
        return a + b


v0.5.0 (April 3, 2018)
======================

* Nodes can be run in parallel using Python multiprocessing module::

    graph = Graph(parallel=True, pool_size=3)

* `inputs` and `outputs` parameters are mandatory and will raise an explicit error when missing.

* Add a longer test using `pvlib`


v0.4.0 (March 23, 2018)
=======================

* Fix single output when dealing with iterables. Previously, returning one output
  with an iterable was resulting in taking the first element.

* Args and kwargs can be used in functions::

    @graph.register(
            inputs=['a', 'b'],
            args=['c'],
            kwargs=['d'],
            outputs=['e']
        )
    def f_my_function(a, b, *args, **kwargs):
        return a + b + args[0] + kwargs['d']

* Can create a Node without using the decorator::

    graph.add_node(f_my_function, inputs=['a', 'b'], outputs=['c'])

* DAG pretty print (`graph.dag`)


v0.3.0 (March 18, 2018)
=======================

First version in pypi
