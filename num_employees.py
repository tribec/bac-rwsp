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
import math
from gurobipy import quicksum, GRB
max_num_shifts_per_week = 5.25
min_num_shifts_per_week = 4


def calculate_employee_bounds(staff_req, num_days, REST_PERIODS):
    """
    Calculate E_{lb} and E_{ub} based on maximum/minimum number of shifts per 
    week. The maximum number of shifts per week is reduced in case of rest
    period constraints.
    """
    sum_shifts = sum(sum(t) for t in staff_req)/(num_days//7)
    if REST_PERIODS:
        min_employees = sum_shifts / 5
    else:
        min_employees = sum_shifts / (max_num_shifts_per_week)
    max_employees = sum_shifts / (min_num_shifts_per_week)
    return min_employees, max_employees


def cf_employee_obj(cf_model, staff_req, num_days, REST_PERIODS):
    """
    Modify compact formulation to minimize number of employees.
    """
    x = cf_model._x
    cf_model._empl_obj = cf_model.addVar()
    cf_model.addConstr(
        cf_model._empl_obj == 
        quicksum(cf_model._num_cycles[g, b, h]*x[g, b, h] for g, b, h in x)
        )
    cf_model.setObjective(
                cf_model._empl_obj, GRB.MINIMIZE
                    )
    cf_model.remove(cf_model._ctr_num_employees)
    lb, ub = calculate_employee_bounds(staff_req, num_days, REST_PERIODS)
    cf_model.addConstr(
        sum(cf_model._num_cycles[g, b, h]*x[g, b, h] for g, b, h in x) 
        >= math.ceil(lb)
        )
    cf_model.addConstr(
        sum(cf_model._num_cycles[g, b, h]*x[g, b, h] for g, b, h in x) 
        <= math.floor(ub)
        )
