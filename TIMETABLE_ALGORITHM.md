# Timetable generator: correctness and limits

The generator handles one class per (branch, semester) pair, and one faculty ID per teacher. Each faculty record requests a nonzero number of one-hour weekly lectures. Every class and every teacher can be assigned at most once in a given day/period.

## Guarantees under these constraints

The algorithm models the assignments as a **bipartite multigraph** (classes vs. faculty; one edge per lecture). It checks that no class or faculty requests more lectures than there are weekly slots, and then makes the graph regular by inserting temporary dummy lectures. It finds a perfect matching in each round, assigns the real matched lectures, and discards the dummy matches. By the matching property of regular bipartite graphs, this cannot double-book a class or teacher and cannot reject an otherwise feasible timetable under these *specific* constraints.

Schedule output remains unchanged: `class -> day -> list of six {lecture, time, subject, faculty_name, faculty_id} entries`, with unused slots marked `Free`. Assignment order is deterministic, and rounds are interleaved across working days to distribute scheduled lectures.

The implementation does **not** manage room capacity, labs spanning consecutive periods, lunch breaks beyond the fixed slots, teacher unavailability, class sections, elective groups, school holidays, or fairness beyond basic interleaving. These additional constraints would require an extended model and solver. Do not claim the generated schedule is *globally optimal*.

## Verification

`tests/test_timetable.py` and `tests/test_timetable_advanced.py` check exact lecture counts, no double bookings, full capacity, custom working days, invalid inputs, deterministic output, randomized feasible graphs, and a known counterexample that the prior greedy implementation incorrectly rejected. The large-schedule smoke test validates correctness; its runtime is recorded inside the test but deliberately has no strict CI timing threshold.

Run locally:

```sh
python -m pytest tests/test_timetable.py tests/test_timetable_advanced.py -v
python -m pytest --cov=algorithms.timetable_generator --cov-branch --cov-report=term-missing tests/test_timetable.py tests/test_timetable_advanced.py
```
