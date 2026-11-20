# Performance review

The timetable generator uses deterministic bipartite edge-colouring via perfect matchings. It first checks per-class and per-faculty weekly capacity and then schedules every requested lecture without either resource being double-booked. Its schedule is deterministic and the output format is unchanged.

For a weekly calendar with `D` working days and `P` periods, the number of matching rounds is at most `D × P` (normally 36). The implementation stores an `N × N` array of edge lists, where `N = max(number of classes, number of faculty)`, plus one entry per requested lecture and dummy lecture. A DFS-based perfect matching is used for each round. This is well suited to small/medium demonstration timetables; memory and matching time can grow significantly for very large institutions.

**Correctness checks:** seeded randomized feasible timetables, full occupancy, repeated subjects, custom working days and a counterexample the previous greedy allocator incorrectly rejected. See `TIMETABLE_ALGORITHM.md` and `tests/test_timetable_advanced.py`.

**Important limitations:** Room capacity, teacher availability, lab blocks, class sections and elective clashes are not modelled. Day interleaving is a heuristic for spreading lectures and does not guarantee optimal daily balancing. For a production university-scale solver with such constraints, a dedicated constraint solver would be appropriate.

There are no live Gemini response-time benchmarks. Performance of external AI requests depends on network latency, provider quotas and request contents.
