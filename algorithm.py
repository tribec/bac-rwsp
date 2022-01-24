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

from compact_formulation import construct_compact_formulation
from extensions.num_weekends import cf_weekend_obj
from extensions.num_employees import cf_employee_obj
from extensions.rest_periods import cf_rest_period_ctr

from reader import read_example
from time import time
from subproblem import subproblem
from helper import subcyclecuts
import collections


def run_algorithm(run_data, time_limit=1000):
    # num_sol counts the number of solutions found
    num_sol = 0

    # Read problem parameteres from problem instance file
    (length_of_schedule, num_employees, S, demand, 
        blocks, forbidden, min_off, max_off) = read_example(run_data.path)
    
    run_data.num_employees = num_employees
    run_data.num_days = length_of_schedule
    B = {i: [(idx, s) for idx, s in enumerate(b)] 
         for i, b in enumerate(blocks)}
    # Allowable day off sequences
    H = {idx: val for idx, val in enumerate(range(min_off, max_off + 1))}
    f_dict = collections.defaultdict(list)
    for f, l in forbidden:
        f_dict[f].append(l)
    forbidden = f_dict

    cf_model = construct_compact_formulation(num_employees, run_data.num_days, 
                                             S, min_off, max_off, demand, 
                                             B, H, forbidden)
    
    cf_model.setParam("TimeLimit", 1000)
    cf_model._B = B
    cf_model._H = H
    cf_model._run_data = run_data
    x = cf_model._x

    # Consider extensions
    if run_data.WEEKEND_OBJ:
        cf_weekend_obj(cf_model, run_data.num_days, blocks, min_off, max_off)

    if run_data.EMPLOYEE_OBJ:
        cf_employee_obj(cf_model, demand, 
                        run_data.num_days, run_data.REST_PERIODS)

    if run_data.REST_PERIODS:
        cf_rest_period_ctr(cf_model, run_data.num_days, B, H, forbidden)

    terminate = False
    start_time = time()
    while not terminate:
        cf_model.optimize(subcyclecuts)

        # Compact formulation is infeasible
        if cf_model.status != 2:
            run_data.time = time() - start_time
            return run_data

        cf_sol = []
        for g, b, h in x:
            if x[g, b, h].X:
                for _ in range(int(round(x[g, b, h].X))):
                    cf_sol.append((g, b, h))

        sp_result = subproblem(cf_sol, B, H, forbidden, 
                               run_data.num_days, run_data.REST_PERIODS)

        status, result = sp_result
        terminate = False
        # Feasible solution found
        if status == 1:
            num_sol += 1
            if num_sol >= run_data.COUNT_SOL:
                terminate = True
                run_data.num_sol = num_sol
                run_data.schedule = result
                run_data.time = time() - start_time
                return run_data
            else:
                if run_data.EMPLOYEE_OBJ:
                    cf_model.addConstr(
                        quicksum(cf_model._num_cycles[g, b, h]*x[g, b, h] 
                                 for g, b, h in x) >= cf_model.objVal
                        )
                if run_data.WEEKEND_OBJ:
                    cf_model.addConstr(
                        quicksum(cf_model._free_we[g, b, h]*x[g, b, h] 
                                 for g, b, h in x) <= cf_model.objVal
                        )
                M = 20
                ms_helper = cf_model.addVar(vtype=GRB.BINARY)
                # Constraints (15) and (16)
                cf_model.addConstr(
                    quicksum(x[k] for k in x if x[k].X > 0.5) 
                    <= quicksum(x[k].X for k in x) - 1 + M*(1 - ms_helper)
                    )
                cf_model.addConstr(
                    quicksum(x[k] for k in x if x[k].X > 0.5) 
                    >= quicksum(x[k].X for k in x) + 1 - M*ms_helper
                    )
        # Subproblem infeasible
        elif status == 2:
            # Constraints (12)
            cf_model.addConstr(quicksum(x[k] for k in x if x[k].X > 0.1) 
                               <= sum(x[k].X for k in x) - 1)

        # Time limit reached
        if (time() - start_time) >= time_limit:
            run_data.time = "time limit"
            return run_data
