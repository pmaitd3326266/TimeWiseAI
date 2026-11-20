"""Deterministic conflict-free weekly timetable generation.

A class and a faculty member can each teach at most once in a time slot.
For these constraints, the problem is bipartite multigraph edge colouring:
classes and faculty are vertices, and requested lectures are edges.
A bipartite multigraph with maximum degree D can always be scheduled in D
slots. The regularised perfect-matching construction below therefore avoids
false failures caused by greedy lecture placement.

Room availability, teacher availability, labs, and preferred teaching hours
are *not* modelled by this generator.
"""
from collections import Counter


class TimetableGenerator:
    DEFAULT_DAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday")
    TIME_SLOTS = (
        "10:00 AM - 11:00 AM", "11:00 AM - 12:00 PM", "12:00 PM - 1:00 PM",
        "2:00 PM - 3:00 PM", "3:00 PM - 4:00 PM", "4:00 PM - 5:00 PM",
    )

    def __init__(self, faculty_records, working_days=None):
        self.faculty_records = list(faculty_records)
        self.working_days = list(working_days) if working_days is not None else list(self.DEFAULT_DAYS)
        if (not self.working_days or any(not isinstance(d, str) or not d.strip() for d in self.working_days)
                or len(self.working_days) != len(set(self.working_days))):
            raise ValueError("Working days must be a non-empty list of unique days.")
        self.time_slots = list(self.TIME_SLOTS)

    @staticmethod
    def _read_record(record, capacity):
        try:
            raw = record["weekly_lectures"]
            if isinstance(raw, bool) or (isinstance(raw, float) and not raw.is_integer()):
                raise ValueError("Lecture count must be an integer")
            count = int(raw)
            if str(raw).strip() != str(count) and not isinstance(raw, float):
                raise ValueError("Lecture count must be an integer")
            faculty_id = str(record["faculty_id"]).strip()
            faculty_name = str(record["faculty_name"]).strip()
            subject = str(record["subject"]).strip()
            branch = str(record["branch"]).strip()
            semester = str(record["semester"]).strip()
        except (ValueError, KeyError, TypeError, AttributeError, OverflowError) as exc:
            raise ValueError("Invalid faculty record.") from exc
        if not branch or not semester or not faculty_id or not faculty_name or not subject or not 1 <= count <= capacity:
            raise ValueError(f"Invalid lecture count or faculty details for {faculty_name}.")
        return (f"{branch} - Semester {semester}", faculty_id, faculty_name, subject, count)

    @staticmethod
    def _perfect_matching(edges):
        """Find a deterministic perfect matching in a regular bipartite multigraph.

        ``edges[i][j]`` holds the lectures remaining between class i and
        teacher j. ``None`` indicates a dummy lecture for regularisation.
        """
        n = len(edges)
        right_owner = [-1] * n

        def augment(left, visited):
            for right in range(n):
                if not edges[left][right] or right in visited:
                    continue
                visited.add(right)
                owner = right_owner[right]
                if owner == -1 or augment(owner, visited):
                    right_owner[right] = left
                    return True
            return False

        for left in range(n):
            if not augment(left, set()):
                raise RuntimeError("Could not schedule a feasible timetable.")
        return [(left, right) for right, left in enumerate(right_owner)]

    def generate_timetable(self):
        capacity = len(self.working_days) * len(self.time_slots)
        class_demand, teacher_demand = Counter(), Counter()
        records = [self._read_record(r, capacity) for r in self.faculty_records]
        for class_name, faculty_id, _faculty_name, _subject, count in records:
            class_demand[class_name] += count
            teacher_demand[faculty_id] += count
        for class_name, demand in class_demand.items():
            if demand > capacity:
                raise ValueError(f"{class_name} requests {demand} lectures but has only {capacity} slots.")
        for faculty_id, demand in teacher_demand.items():
            if demand > capacity:
                raise ValueError(f"Faculty {faculty_id} requests {demand} lectures but has only {capacity} slots.")

        classes = sorted(class_demand)
        timetable = {
            name: {day: [
                {"lecture": i + 1, "time": time, "subject": "Free", "faculty_name": "", "faculty_id": ""}
                for i, time in enumerate(self.time_slots)
            ] for day in self.working_days}
            for name in classes
        }
        if not records:
            return timetable

        teachers = sorted(teacher_demand)
        degree = max(max(class_demand.values()), max(teacher_demand.values()))
        n = max(len(classes), len(teachers))
        ci = {name: i for i, name in enumerate(classes)}
        ti = {name: i for i, name in enumerate(teachers)}

        # Each cell contains real lectures or dummy placeholders. A regular
        # bipartite graph always has a perfect matching; removing one matching
        # per round yields a guaranteed conflict-free allocation.
        edges = [[[] for _ in range(n)] for _ in range(n)]
        left_degree, right_degree = [0] * n, [0] * n
        for class_name, faculty_id, faculty_name, subject, count in sorted(records):
            left, right = ci[class_name], ti[faculty_id]
            edges[left][right].extend([(subject, faculty_name, faculty_id)] * count)
            left_degree[left] += count
            right_degree[right] += count

        # Fill deficit degrees using dummy lectures; the total deficits match.
        left, right = 0, 0
        while left < n and right < n:
            if left_degree[left] == degree:
                left += 1
                continue
            if right_degree[right] == degree:
                right += 1
                continue
            amount = min(degree - left_degree[left], degree - right_degree[right])
            edges[left][right].extend([None] * amount)
            left_degree[left] += amount
            right_degree[right] += amount

        # Interleave days across slots to spread lectures across the week.
        # Eg round 0 Monday first period; round 6 Monday second period.
        for round_index in range(degree):
            day = self.working_days[round_index % len(self.working_days)]
            period = round_index // len(self.working_days)
            for left, right in self._perfect_matching(edges):
                lecture = edges[left][right].pop()
                if lecture is None or left >= len(classes):
                    continue
                subject, faculty_name, faculty_id = lecture
                timetable[classes[left]][day][period] = {
                    "lecture": period + 1, "time": self.time_slots[period],
                    "subject": subject, "faculty_name": faculty_name, "faculty_id": faculty_id,
                }
        return timetable
