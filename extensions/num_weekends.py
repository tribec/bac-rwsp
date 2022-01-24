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
import itertools
from gurobipy import quicksum, GRB


def cf_weekend_obj(cf_model, num_days, blocks, min_off, max_off):
    """
    Compute number of free weekends per stint and modify compact formulation to 
    maximize the number of free weekends.
    """
    G = range(num_days)
    B = range(len(blocks))
    H = {idx: val for idx, val in enumerate(range(min_off, max_off + 1))}
    free_weekends = {}
    for g, b, h in itertools.product(G, B, H):
        stint = []
        for g_offset, s in enumerate(blocks[b]):
            curr = (g + g_offset) % 7
            stint.append((curr, s))
        curr_g = stint[-1][0] + 1
        for _ in range(H[h]):
            stint.append((curr_g % 7, 3))
            curr_g += 1
        num_we = 0
        for idx in range(len(stint)):
            if stint[idx][0] == 4 and stint[idx][1] != 2:
                if len(stint) >= idx + 3:
                    if stint[idx+1][1] == 3 and stint[idx+2][1] == 3:
                        num_we += 1
        free_weekends[g, b, h] = num_we

    cf_model._free_we = free_weekends

    cf_model.setObjective(
        quicksum(free_weekends[g, b, h] * cf_model._x[g, b, h] 
                 for (g, b, h) in cf_model._x), GRB.MAXIMIZE
        )
