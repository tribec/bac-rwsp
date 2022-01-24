"""
MIT License

Copyright (c) 2022 Tristan Becker

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import collections
from itertools import product
from gurobipy import Model, GRB, quicksum
import math


class PlanningCycle:
    """
    Helper class in computing the number of planning cycles in a stint.
    """
    def __init__(self, start_day, num_days):
        self.start_day = start_day
        self.num_days = num_days
        self.weeks = 0 
        if self.start_day == 0:
            self.weeks += 1

    def next(self):
        if self.start_day == self.num_days - 1:
            self.start_day = 0
            self.weeks += 1
        else:
            self.start_day += 1
        return self.start_day


def get_num_planning_cycles(first_day_of_block, last_day_of_block, days_off, 
                            num_days, len_block):
    """
    Compute number of planning cycles in a stint.
    """
    day_before_next_block = (last_day_of_block + days_off) % num_days
    next_start = PlanningCycle(first_day_of_block, num_days)
    counter = 1
    next_start.next()
    while next_start.start_day != last_day_of_block or counter < len_block - 1:
        next_start.next()
        counter += 1
    next_start.next()
    while next_start.start_day != day_before_next_block:
        next_start.next()

    return next_start.weeks


def subcyclecuts(model, where):
    """
    Callback for adding connecting cuts.
    """
    if model._run_data.EMPLOYEE_OBJ and where == GRB.Callback.MIPSOL:
        try:
            bound = model.cbGet(GRB.Callback.MIPNODE_OBJBND)
        except:
            bound = model.cbGet(GRB.Callback.MIPSOL_OBJBND)

        if (bound - round(bound)) > 0.01 and bound != math.ceil(bound):
            model.cbLazy(model._empl_obj >= math.ceil(bound))

    if where == GRB.Callback.MIPSOL:
        vals = model.cbGetSolution(model._v)
        edges = [(i, j) for i, j in model._v.keys() if vals[i, j] > 0.5]
        st = get_segments(list(edges))
        if len(st) > 1:
            # Constraints (5)
            model.cbLazy(quicksum(model._v[k] for k in edges) 
                         <= sum(vals[k] for k in edges) - 1)


def get_segments(edges):
    """
    Separation Procedure (Figure 6)
    """
    segments = []

    while edges:
        partial = set(edges[0])
        partial_edges = [edges[0]]
        del edges[0]

        changed = True
        while changed:
            changed = False
            for i, j in edges:
                if i in partial or j in partial:
                    partial.add(i)
                    partial.add(j)
                    partial_edges.append((i, j))
                    edges.remove((i, j))
                    changed = True
                    break
        segments.append(partial_edges)

    return segments


class cycledict(dict):
    """
    Dictionary with cyclic indexing
    """
    def __init__(self, *args):
        super().__init__
        self.keys = [i for i in args]

    def __getitem__(self, key):
        if not isinstance(key, tuple):
            return dict.__getitem__(self, key % self.keys[0])
        else:
            key = [i for i in key]
            for idx, i in enumerate(key):
                if i < 0:
                    key[idx] = self.keys[idx] + i
                else:
                    key[idx] = i % self.keys[idx]
            return dict.__getitem__(self, tuple(key))

    def __setitem__(self, key, value):
        if not isinstance(key, tuple):
            super(cycledict, self).__setitem__(key % self.keys[0], value)
        else:
            key = [i for i in key]
            for idx, i in enumerate(key):
                if i < 0:
                    key[idx] = self.keys[idx] + i
                else:
                    key[idx] = i % self.keys[idx]
            super(cycledict, self).__setitem__(tuple(key), value)


class ShiftModel(Model):
    """
    gurobipy Model with cyclic decision variables
    """
    def __init__(self, *args):
        super().__init__(*args)
    
    def addCyclicVars(self, *indices, lb=0, ub=GRB.INFINITY, 
                      vtype=GRB.CONTINUOUS, name="C"):
        
        var = cycledict(*indices)
        
        for key in product(*[range(i) for i in indices]):
            var[key] = self.addVar(lb=lb, ub=ub, vtype=vtype, 
                                   name=name+'_'+'_'.join(str(i) for i in key))
        
        return var


def construct_coverage_set(G, S, B):
    """
    Compute coverage of start day and work stretch combinations
    """
    Coverage = cycledict(len(G), len(S))
    for g, s in product(G, S):
        Coverage[g, s] = collections.defaultdict(lambda: 0)

    for g, (idx, b) in product(G, B.items()):
        for g_, s in b:
            Coverage[g + g_, s][g, idx] += 1

    return Coverage
