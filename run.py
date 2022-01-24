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
from types import SimpleNamespace
from algorithm import run_algorithm


'''
Definition of the problem variants (see Section 4.2 of our paper)
BP -> Benchmark problem (Section 4.1)
FW -> Maximizing the number of free weekends
RP -> Rest periods
NE -> Minimizing the number of employees
MS -> Finding multiple solutions'''
problem_variants = [
          (False, False, False, 0),  # BP
          (False, True, True, 0),  # FW/RP
          (False, True, False, 0),  # BP/RP
          (False, False, True, 0),  # FW/BP
          (True, False, False, 0),  # NE/BP
          (True, True, False, 0),  # NE/RP
          (False, False, False, 10),  # BP/MS
          (False, False, True, 10),  # FW/MS
          (True, False, False, 10)  # NE/MS
          ]

# Set of problem instances to be solved
instances = ["ExampleProblemFile.dzn"] 

# Define optimization tasks: Run each test instance for each problem variant
optimization_tasks = [(instance, *param) 
                      for instance in instances for param in problem_variants]

# Run algorithm for all optimization tasks
for task in optimization_tasks:
    path, EMPLOYEE_OBJ, REST_PERIODS, WEEKEND_OBJ, COUNT_SOL = task

    # Initialize run_data
    run_data = SimpleNamespace(path=path, num_days=-1, num_sol=0, 
                               time=0, schedule="", num_employees=-1,
                               EMPLOYEE_OBJ=EMPLOYEE_OBJ, REST_PERIODS=REST_PERIODS,
                               WEEKEND_OBJ=WEEKEND_OBJ, COUNT_SOL=COUNT_SOL)
    print("-----------------   Instance {}   -----------------".format(*task))

    # Call algorithm
    result = run_algorithm(run_data)
    if run_data.schedule:
        print(run_data.schedule)
    else:
        print("Instance is INFEASIBLE")
