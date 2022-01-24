# Implementation: A General Branch-and-Cut Framework for Rotating Workforce Scheduling

This repository hosts an implementation of the algorithm described in our paper **Becker, Tristan; Schiffer, Maximilian; Walther, Grit (2022): A General Branch-and-Cut Framework for Rotating Workforce Scheduling, accepted for publication in: INFORMS Journal on Computing**.

## Description

The algorithm quickly solves problem instances of the **Rotating Workforce Scheduling Problem** (RWSP) and several extensions, generating a feasible schedule or proving infeasibility.

## Code files

`reader.py` reads RWSP problem instances as proposed by the paper **L. Kletzander, N. Musliu, K. Smith-Miles: Instance space analysis for a personnel scheduling problem; Annals of Mathematics and Artificial Intelligence, 89 (2021), 7; 617 - 637.**

`algorithm.py` controls the execution of the compact formulation and subproblem, receiving the data for a specific problem instance and returning a schedule or proof of infeasibility.

`compact_formulation.py` constructs the compact formulation model.

`subproblem.py` constructs and solves the subproblem formulation.

`extensions/num_employees.py, num_weekends.py, rest_periods.py` contains the extensions of the compact formulation to accomodate for several extensions.

`helper.py` contains helper classes and functions for our algorithm, used for constructing and solving the mathematical formulations.

`run.py` provides an example of how to call our algorithm to solve a set of problem instances.

## Cite

The citation will be added, once the paper is published.

## Support

If you need help in using this software, please email [Tristan Becker](mailto:tristan.becker@tu-dresden.de).