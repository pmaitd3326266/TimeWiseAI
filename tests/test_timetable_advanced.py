"""Property-style and regression tests for the deterministic scheduler.

All random examples use fixed seeds so failures are reproducible.
"""
import random
from collections import Counter
from time import perf_counter

import pytest

from algorithms.timetable_generator import TimetableGenerator


def rec(cl, teacher, subject, count=1):
    return {
        "branch": f"Class{cl}", "semester": 1,
        "faculty_id": f"Teacher{teacher}", "faculty_name": f"Faculty {teacher}",
        "subject": f"Subject {subject}", "weekly_lectures": count,
    }


def verify(schedule, records, days=None):
    days = days or TimetableGenerator.DEFAULT_DAYS
    actual = Counter()
    teacher_slots = set()
    for class_name, week in schedule.items():
        assert list(week) == list(days)
        for day, periods in week.items():
            assert len(periods) == 6
            for index, slot in enumerate(periods):
                assert slot["lecture"] == index + 1
                assert slot["time"] == TimetableGenerator.TIME_SLOTS[index]
                if slot["subject"] == "Free":
                    assert not slot["faculty_id"]
                    continue
                tslot = (slot["faculty_id"], day, index)
                assert tslot not in teacher_slots, f"Faculty conflict: {tslot}"
                teacher_slots.add(tslot)
                actual[(class_name, slot["faculty_id"], slot["subject"])] += 1
    expected = Counter()
    for r in records:
        expected[(f"{r['branch']} - Semester {r['semester']}",
                  r["faculty_id"], r["subject"])] += r["weekly_lectures"]
    assert actual == expected


def test_multi_edge_same_class_teacher_different_subjects():
    records = [rec(0, 0, "Math", 12), rec(0, 0, "Science", 12),
               rec(1, 0, "Physics", 12), rec(1, 1, "Chemistry", 8)]
    verify(TimetableGenerator(records).generate_timetable(), records)


def test_full_week_multiple_classes_same_teacher():
    records = [rec(cl, 0, f"S{cl}", 6) for cl in range(6)]
    verify(TimetableGenerator(records).generate_timetable(), records)


def test_exact_saturation_multiple_teachers_and_classes():
    # Every teacher and class fills all 36 slots.
    records = [rec(cl, teacher, f"S{teacher}", 6)
               for cl in range(6) for teacher in range(6)]
    verify(TimetableGenerator(records).generate_timetable(), records)


@pytest.mark.parametrize("seed", range(35))
def test_seeded_feasible_random_multigraphs(seed):
    rng = random.Random(seed)
    nclasses = rng.randint(2, 10)
    nteachers = rng.randint(2, 12)
    classload = [0] * nclasses
    teacherload = [0] * nteachers
    records = []
    for i in range(150):
        possible = [(c, t) for c in range(nclasses)
                    for t in range(nteachers)
                    if classload[c] < 36 and teacherload[t] < 36]
        if not possible:
            break
        c, t = rng.choice(possible)
        count = min(rng.randint(1, 5), 36-classload[c], 36-teacherload[t])
        records.append(rec(c, t, f"S{i % 7}", count))
        classload[c] += count
        teacherload[t] += count
    verify(TimetableGenerator(records).generate_timetable(), records)


@pytest.mark.parametrize("days", [["Monday"], ["Tuesday", "Thursday"], ["Mon", "Tue", "Wed", "Thu"]])
def test_custom_days_no_conflicts(days):
    capacity = len(days) * 6
    records = [rec(0, 0, "A", capacity//2), rec(1, 0, "B", capacity-capacity//2)]
    verify(TimetableGenerator(records, days).generate_timetable(), records, days)


@pytest.mark.parametrize("value", [True, False, 2.5, "2.5", "", "  ", float("nan"), float("inf")])
def test_non_integer_lecture_counts_rejected(value):
    with pytest.raises(ValueError):
        TimetableGenerator([rec(0, 0, "A", value)]).generate_timetable()


@pytest.mark.parametrize("change", [
    {"branch": ""}, {"semester": ""}, {"faculty_name": ""},
    {"faculty_id": ""}, {"subject": ""},
])
def test_blank_required_fields_rejected(change):
    item = rec(0, 0, "A")
    item.update(change)
    with pytest.raises(ValueError):
        TimetableGenerator([item]).generate_timetable()


def test_input_records_unchanged():
    records = [rec(0, 0, "A", 2), rec(1, 0, "B", 2)]
    snapshot = [dict(r) for r in records]
    TimetableGenerator(records).generate_timetable()
    assert records == snapshot


def test_input_order_independence():
    records = [rec(0, 0, "A", 8), rec(1, 0, "B", 5),
               rec(0, 1, "C", 9), rec(1, 1, "D", 7)]
    expected = TimetableGenerator(records).generate_timetable()
    assert TimetableGenerator(list(reversed(records))).generate_timetable() == expected


def test_large_schedule_smoke_benchmark():
    # Not a strict timing threshold: CI runners have variable performance.
    rng = random.Random(123)
    records, classload, teacherload = [], [0]*60, [0]*60
    for i in range(300):
        possible = [(c,t) for c in range(60) for t in range(60)
                    if classload[c] < 36 and teacherload[t] < 36]
        c,t = rng.choice(possible)
        count = min(3, 36-classload[c], 36-teacherload[t])
        records.append(rec(c,t,f"S{i}",count))
        classload[c] += count
        teacherload[t] += count
    begin = perf_counter()
    schedule = TimetableGenerator(records).generate_timetable()
    elapsed = perf_counter()-begin
    verify(schedule, records)
    assert elapsed >= 0


def test_previous_greedy_false_failure_now_schedules_all_lectures():
    """A known feasible schedule that the old greedy allocator rejected."""
    edges = [
        (0, 0, 6), (1, 2, 3), (1, 1, 5), (0, 0, 7),
        (0, 1, 9), (1, 1, 10), (0, 2, 5), (1, 0, 10),
        (1, 2, 5), (1, 2, 2),
    ]
    records = [rec(cl, teacher, f"R{i}", count) for i, (cl, teacher, count) in enumerate(edges)]
    verify(TimetableGenerator(records).generate_timetable(), records)
