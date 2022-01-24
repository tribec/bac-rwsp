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
from gurobipy import GRB, quicksum
from helper import ShiftModel, construct_coverage_set, get_num_planning_cycles


def construct_compact_formulation(num_employees, num_days, num_shifts, 
                                  min_off, max_off, staff_req, B, H, forbidden):

    G = range(num_days)
    S = range(num_shifts)

    m = ShiftModel()
    m.setParam("OutputFlag", 0)

    block_ending_day = {
        (g, b): (g + len(B[b]) - 1) % num_days for g in G for b in B
        }

    # Decision Variables
    x = m.addCyclicVars(num_days, len(B), len(H), vtype=GRB.INTEGER, name="x")
    v = m.addVars(num_days, num_days, vtype=GRB.INTEGER, name="v")

    C = construct_coverage_set(G, S, B)

    # Simple upper bound for x_{gbh}
    ub = {}
    for g in G:
        for b in B:
            max_block = 1e6
            for d, s in B[b]:
                curr_d = (g+d) % len(G)
                if staff_req[s][curr_d] < max_block:
                    max_block = staff_req[s][curr_d]
            ub[g, b] = max_block

    num_cycles = {
        (g, b, h): get_num_planning_cycles(g, (g+len(B[b])-1) % num_days, H[h], 
                                           num_days, len(B[b]))
        for g, b, h in x
                }

    # Constraints (1)
    m.addConstrs(
        quicksum(num_times * x[g_, b, h] 
                 for (g_, b), num_times in C[g, s].items() for h in H) 
        == staff_req[s][g]
        for g in G for s in S
        )

    # Constraints (2)
    m._ctr_num_employees = m.addConstr(
            sum(num_cycles[g, b, h]*x[g, b, h] for g, b, h in x) 
            == num_employees
            )

    # Constraints (3)
    m.addConstrs(
        quicksum(
            x[g, b, h] for g, b, h in x 
            if g == i and (g + len(B[b]) + H[h]) % 7 == j) 
        == v[i, j]
        for i, j in v
        )

    # Constraints (4)
    m.addConstrs(
        quicksum(v[i, j] for i in G) == quicksum(v[j, i] for i in G) for j in G
        )

    # Constraints (13)
    m.addConstrs(
        quicksum(
                 x[g, b, 0] for (g, b), g_ in block_ending_day.items() 
                 if g_ == g_curr and B[b][-1][1] == last_shift)
        <= quicksum(
            x[(g_curr + 2) % num_days, b, h] for h in H for b in B 
            if B[b][0][1] not in forbidden[last_shift]
            )
        for g_curr in G for last_shift in forbidden if H[0] == 1
        )

    # Upper bound on x_{gbh}
    m.addConstrs(
        quicksum(x[g, b, h] for h in H) <= ub[g, b] for g in G for b in B
        )

    m.Params.lazyConstraints = 1

    # Expose model variables/parameters
    m._x = x
    m._v = v
    m._num_cycles = num_cycles

    return m
