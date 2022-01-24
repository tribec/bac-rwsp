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
from gurobipy import Model, quicksum, GRB, tuplelist
import itertools
import collections
shifts = {0: 'D', 1: 'A', 2: 'N', 3: 'B'}
Node = collections.namedtuple("Node", "start end fwork "
                              "lwork nwork do string_rep mp_id")   


def subproblem(x, blocks, H, forbidden, num_days, REST_PERIODS):
    """
    Construct and solve subproblem formulation
    """
    def subtour(edges):
        n = len(Nodes)
        uv = list(range(n))
        shortest_cycle = range(n+1)
        while uv:
            curr_cycle = []
            neighbors = uv
            while neighbors:
                curr_node = neighbors[0]
                curr_cycle.append(curr_node)
                uv.remove(curr_node)
                neighbors = [j for i, j in edges.select(curr_node, '*') 
                             if j in uv]
            if len(curr_cycle) < len(shortest_cycle):
                shortest_cycle = curr_cycle
        return shortest_cycle

    def subtourelim(model, where):
        if where == GRB.Callback.MIPSOL:
            n = len(Nodes)
            vals = model.cbGetSolution(model._vars)
            sol_edges = tuplelist((i, j) for i, j in model._vars.keys() 
                                 if vals[i, j] > 0.5)
            tour = subtour(sol_edges)
            if len(tour) < n:
                # Constraints (9)
                model.cbLazy(
                    quicksum(model._vars[i, j]
                             for i, j in itertools.permutations(tour, 2))
                    <= len(tour)-1
                    )
    Nodes = {}
    for idx, (day, block, daysoff) in enumerate(x):
        end = (day + len(blocks[block]) + H[daysoff]) % num_days
        fwork, lwork = blocks[block][0][1], blocks[block][-1][1]
        string_rep = ("".join(shifts[i[1]] for i in blocks[block]) 
                      + "".join("-" for _ in range(H[daysoff])))
        Nodes[idx] = Node(day, end, fwork, lwork, len(blocks[block]), 
                          H[daysoff], string_rep, (day, block, daysoff))

    infeas = []
    for i1 in Nodes:
        for i2 in Nodes:
            n1, n2 = Nodes[i1], Nodes[i2]
            if n1.end != n2.start:
                infeas.append((i1, i2))
            elif n1.do == 1 and n2.fwork in forbidden[n1.lwork]:
                infeas.append((i1, i2))
            elif REST_PERIODS:
                combined = n1.string_rep + n2.string_rep
                # Offset until next week starts
                idx_offset = 7 - (n1.start % 7)
                # Is a whole week contained in the sequence?
                if len(combined) > idx_offset + 7:
                    if sum(1 for i in combined[idx_offset:idx_offset+7] 
                           if i == "-") < 2:
                        infeas.append((i1, i2))

    m = Model()
    m.setParam("OutputFlag", 0)
    vars = m.addVars(Nodes, Nodes, vtype=GRB.BINARY)

    # Constraints (7)
    m.addConstrs(
        quicksum(vars[i, j] for j in Nodes) == 1 for i in Nodes
    )

    # Constraints (8)
    m.addConstrs(
        quicksum(vars[i, j] for i in Nodes) == 1 for j in Nodes
    )

    # Constraints (10)
    m.addConstrs(vars[i, i] == 0 for i in Nodes)

    # Eliminate infeasible arcs
    m.addConstrs(vars[i, j] == 0 for i, j in infeas)

    m._vars = vars
    m.Params.lazyConstraints = 1

    try:
        m.optimize(subtourelim)
        vals = m.getAttr('x', vars)
        selected = tuplelist((i, j) 
                             for i, j in vals.keys() if vals[i, j] > 0.5)

        tour = subtour(selected)
        # print(tour)
        str_sol = "".join(Nodes[i].string_rep for i in tour)
        prepend_from_end = Nodes[tour[0]].start
        end = str_sol[-prepend_from_end:]
        str_sol = end + str_sol[:-prepend_from_end]
        return 1, str_sol
    except:
        return 2, None
