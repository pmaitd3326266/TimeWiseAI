import pytest
from algorithms.timetable_generator import TimetableGenerator


def record(fid="T1", branch="CSE", semester=1, subject="MATH", weekly=3):
    return {"faculty_id": fid, "faculty_name": "Teacher " + fid, "branch": branch,
            "semester": semester, "subject": subject, "weekly_lectures": weekly}


def flattened(result):
    return [(cls, day, i, item) for cls, days in result.items() for day, slots in days.items()
            for i, item in enumerate(slots) if item["subject"] != "Free"]


def test_empty_schedule():
    assert TimetableGenerator([]).generate_timetable() == {}


def test_full_capacity_single_class():
    schedule = TimetableGenerator([record(weekly=36)]).generate_timetable()
    assert len(flattened(schedule)) == 36


@pytest.mark.parametrize("count", [1, 2, 6, 7, 18, 30, 36])
def test_exact_lecture_count(count):
    schedule = TimetableGenerator([record(weekly=count)]).generate_timetable()
    assert len(flattened(schedule)) == count


def test_multiple_subjects_do_not_clash_in_same_class():
    schedule = TimetableGenerator([record(subject="MATH", weekly=12), record(fid="T2", subject="PHY", weekly=12)]).generate_timetable()
    assert len(flattened(schedule)) == 24


def test_shared_teacher_does_not_double_book():
    records = [record(fid="T1", branch="CSE", weekly=12), record(fid="T1", branch="ECE", weekly=12)]
    booked = flattened(TimetableGenerator(records).generate_timetable())
    slots = [(day, period) for _, day, period, entry in booked if entry["faculty_id"] == "T1"]
    assert len(slots) == len(set(slots)) == 24


def test_class_capacity_exceeded():
    with pytest.raises(ValueError, match="requests"):
        TimetableGenerator([record(weekly=25), record(fid="T2", subject="PHYS", weekly=25)]).generate_timetable()


def test_teacher_capacity_exceeded():
    with pytest.raises(ValueError, match="Faculty"):
        TimetableGenerator([record(weekly=30), record(branch="ECE", weekly=30)]).generate_timetable()


@pytest.mark.parametrize("count", [0, -1, 37, "abc", None])
def test_invalid_weekly_counts(count):
    with pytest.raises(ValueError):
        TimetableGenerator([record(weekly=count)]).generate_timetable()


def test_duplicate_days_rejected():
    with pytest.raises(ValueError):
        TimetableGenerator([], ["Monday", "Monday"])


def test_empty_days_rejected():
    with pytest.raises(ValueError):
        TimetableGenerator([], [])


def test_deterministic_repeatability():
    records = [record(weekly=15), record(fid="T2", subject="PHY", weekly=8)]
    assert TimetableGenerator(records).generate_timetable() == TimetableGenerator(records).generate_timetable()


def test_day_load_balanced():
    schedule = TimetableGenerator([record(weekly=12)]).generate_timetable()
    counts = [sum(x["subject"] != "Free" for x in slots) for slots in schedule["CSE - Semester 1"].values()]
    assert max(counts) - min(counts) <= 1


def test_custom_day_count_limits_capacity():
    with pytest.raises(ValueError):
        TimetableGenerator([record(weekly=7)], working_days=["Monday"] ).generate_timetable()


def test_remaining_slots_filled_with_free():
    schedule = TimetableGenerator([record(weekly=1)]).generate_timetable()
    slots = [x for day in schedule["CSE - Semester 1"].values() for x in day]
    assert len(slots) == 36
    assert sum(x["subject"] == "Free" for x in slots) == 35
