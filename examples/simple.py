import os
import sys

PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PATH)

from pyungo.core import Graph
from pprint import pprint


if __name__ == '__main__':
    graph = Graph()

    @graph.register()
    def f_my_function(a, b):
        c = a + b
        return c

    @graph.register(inputs=['d', 'a'], outputs=['e'])
    def f_my_function3(d, a):
        e = d - a
        return e

    @graph.register(outputs=['d'])
    def f_my_function2(c):
        return c / 10.

    res = graph.calculate(data={'a': 2, 'b': 3})
    print(res)
