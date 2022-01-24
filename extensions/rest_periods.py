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
from gurobipy import quicksum


def cf_rest_period_ctr(cf_model, num_days, B, H, forbidden):
    """
    Modify compact formulation to enforce rest period constraints.
    """
    x = cf_model._x
    infeas_stints = [(0, 7), (0, 6), (1, 6), (1, 7), (6, 7)]
    for g_, bl in infeas_stints:
        cf_model.addConstrs(
            x[g, b, h] == 0 
            for g, b, h in x if (g % 7) == g_ and len(B[b]) == bl
            )
    cf_model.addConstrs(
        x[g, b, h] == 0 
        for g, b, h in x if (g % 7) == 4 and len(B[b]) == 6 and h == 0
        )

    cf_model.addConstrs(
        x[g, b, h] == 0 
        for g, b, h in x if (g + len(B[b]) - 1) % 7 in [2, 3, 4, 5] 
        and H[h] == 1
        )

    weekly_rest = {w: {} for w in range(0, num_days//7)}
    for week in range(0, num_days//7):
        start_one = {1+week*7: [], 2+week*7: [], 3+week*7: []}
        for g, b, h in x:
            if g in start_one:
                if g + len(B[b]) - 1 <= 5+week*7:
                    start_one[g].append((g, b, h))
        weekly_rest[week]["start_one"] = start_one

        end_one = {0+week*7: [], 1+week*7: [], 2+week*7: []}
        for g, b, h in x:
            first_day_off = (g + len(B[b])) % num_days
            days_off = [first_day_off]
            for h_ in range(1, H[h]):
                days_off.append(first_day_off + h_)
            days_off_begin = sum([1 for i in days_off 
                                  if i in [0+week*7, 1+week*7, 2+week*7]])
            if days_off_begin == 1 and days_off[-1] <= 2+week*7:
                end_one[days_off[-1]].append((g, b, h))
        weekly_rest[week]["end_one"] = end_one

    cf_model.addConstrs(
        quicksum(x[key] for key in weekly_rest[w]["end_one"][end]) 
        <= quicksum(x[key] for key in weekly_rest[w]["start_one"][end+1]) 
        for w in weekly_rest for end in weekly_rest[w]["end_one"]
        )

    for last_s in forbidden:
        cf_model.addConstrs(
            quicksum(x[g, b, h] for g, b, h in weekly_rest[w]["end_one"][end] 
                     if B[b][-1][1] == last_s and H[h] == 1) 
            <= quicksum(x[g, b, h] 
                        for g, b, h in weekly_rest[w]["start_one"][end+1] 
                        if B[b][0][1] not in forbidden[last_s]) 
            for w in weekly_rest for end in weekly_rest[w]["end_one"] 
            if H[0] == 1
            )
