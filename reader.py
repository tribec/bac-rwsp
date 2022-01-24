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
import re


class Example:
    def read_data(self, path):
        print("Started reading: ", path)
        with open(path, "r") as f:
            file = f.read()
        self.num_employees = int(re.findall("groups = ([0-9]+);", file)[0])
        self.num_shifts = int(re.findall("numShifts = ([0-9]);", file)[0])
        self.temp_matrix = [[int(i) for i in re.findall(r"demand = \[[0-9\s,|]+\];", file, re.DOTALL)[0].replace("\n", ""
                               ).replace("|", "").replace("[", "").replace("]", "").replace(" ", ""
                               ).replace("demand=", "").replace(";","").strip().split(",")[e*7:(e+1)*7]] for e in range(self.num_shifts)]
        if self.num_shifts == 2:
            self.min_length_blocks = list(map(int, re.findall(r"minShift = \[([0-9]), ([0-9])\];", file)[0]))
            self.max_length_blocks = list(map(int, re.findall(r"maxShift = \[([0-9]), ([0-9])\];", file)[0]))
        elif self.num_shifts == 3:
            self.min_length_blocks = list(map(int, re.findall(r"minShift = \[([0-9]), ([0-9]), ([0-9])\];", file)[0]))
            self.max_length_blocks = list(map(int, re.findall(r"maxShift = \[([0-9]), ([0-9]), ([0-9])\];", file)[0]))
        self.min_days_off = int(re.findall("minOff = ([0-9]);", file)[0])
        self.max_days_off = int(re.findall("maxOff = ([0-9]);", file)[0])
        self.min_length_work_blocks = int(re.findall("minOn = ([0-9]);", file)[0])
        self.max_length_work_blocks = int(re.findall("maxOn = ([0-9]);", file)[0])
        forbidden = [list(i.replace("{", "").replace("}", "").split(",")) for i in re.findall("{[0-9,]+}|{}", 
                     re.findall(r"forbidden = \[(.+)\];", file)[0])]
        for i in range(self.num_shifts):
            if forbidden[i] == [""]:
                forbidden[i] = []
            else:
                forbidden[i] = list(map(int, forbidden[i]))
        if "forbidden3 = [|  |];" not in file:
            forbidden3 = [[int(i) for i in re.findall(r"forbidden3 = \[[0-9\s,|]+\];", file, re.DOTALL)[0].replace("\n", ""
                               ).replace("|", "").replace("[", "").replace("]", "").replace(" ", ""
                               ).replace("forbidden3=", "").replace(";", "").strip().split(",")[e*3:(e+1)*3]] for e in range(len(re.findall(r"forbidden3 = \[[0-9\s,|]+\];", file, re.DOTALL)[0].split("\n")))]
        else:
            forbidden3 = []
        self.length_of_schedule = 7
        Shifts = {1: 'D', 2: 'A', 3: 'N', 0: '-'}
        self.disallowed_shift_seq = []
        for idx, val in enumerate(forbidden):
            for disallowed in val:
                self.disallowed_shift_seq.append([Shifts[idx+1], Shifts[disallowed]])
        for val in forbidden3:
            disallowed = [Shifts[i] for i in val]
            self.disallowed_shift_seq.append(disallowed)


def read_example(name):
    data = Example()
    data.read_data(name)
    if data.num_shifts == 2:
        Shifts = {'D': 0, 'A': 1}
    elif data.num_shifts == 3:
        Shifts = {'D': 0, 'A': 1, 'N': 2}
    elif data.num_shifts == 4:
        Shifts = {'D': 0, 'A': 1, 'N': 2, 'B': 3}
        
    S = range(data.num_shifts)
    allowed = [(s, s_) for s in S for s_ in S if s != s_]
    forbidden = []
    for li in range(len(data.disallowed_shift_seq)):
        if len(data.disallowed_shift_seq[li]) == 2:
            try:
                allowed.remove(tuple(map(lambda x: Shifts[x], data.disallowed_shift_seq[li])))
            except ValueError:
                pass
        elif len(data.disallowed_shift_seq[li]) == 3:
            forbidden.append((Shifts[data.disallowed_shift_seq[li][0]], Shifts[data.disallowed_shift_seq[li][-1]]))
    blocks = []
    for s in S:
        for w in range(max(data.min_length_blocks[s], data.min_length_work_blocks), min(data.max_length_blocks[s] + 1, data.max_length_work_blocks + 1)):
            blocks.append((s,)*w)

    for transition in allowed:
        min_u, max_u = data.min_length_blocks[transition[0]], data.max_length_blocks[transition[0]]
        min_v, max_v = data.min_length_blocks[transition[1]], data.max_length_blocks[transition[1]]
        for u in range(min_u, max_u + 1):
            for v in range(min_v, max_v + 1):
                block = (transition[0],) * u + (transition[1],) * v
                if len(block) >= data.min_length_work_blocks and len(block) <= data.max_length_work_blocks:
                    blocks.append(block)

    triples = set()
    for t1 in allowed:
        for t2 in allowed:
            if t1[-1] == t2[0]:
                triples.add((t1[0], t1[1], t2[1]))

    for transition in triples:
        min_u, max_u = data.min_length_blocks[transition[0]], data.max_length_blocks[transition[0]]
        min_v, max_v = data.min_length_blocks[transition[1]], data.max_length_blocks[transition[1]]
        min_w, max_w = data.min_length_blocks[transition[2]], data.max_length_blocks[transition[2]]
        for u in range(min_u, max_u + 1):
            for v in range(min_v, max_v + 1):
                for w in range(min_w, max_w + 1):
                    block = (transition[0],) * u + (transition[1],) * v + (transition[2],) * w
                    if len(block) >= data.min_length_work_blocks and len(block) <= data.max_length_work_blocks:
                        blocks.append(block)

    return data.length_of_schedule, data.num_employees, data.num_shifts, data.temp_matrix, blocks, forbidden, data.min_days_off, data.max_days_off