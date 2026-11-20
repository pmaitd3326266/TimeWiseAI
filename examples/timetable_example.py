
from algorithms.timetable_generator import TimetableGenerator

# Sample faculty records for testing
faculty_records = [
    {
        "faculty_name": "Rahul Sharma",
        "faculty_id": "FAC001",
        "branch": "CSE AI/ML",
        "semester": 1,
        "subject": "ACS101",
        "weekly_lectures": 4
    },
    {
        "faculty_name": "Amit Verma",
        "faculty_id": "FAC002",
        "branch": "CSE AI/ML",
        "semester": 1,
        "subject": "AAS103D",
        "weekly_lectures": 5
    },
    {
        "faculty_name": "Priya Singh",
        "faculty_id": "FAC003",
        "branch": "CSE AI/ML",
        "semester": 1,
        "subject": "AAI101",
        "weekly_lectures": 3
    }
]

generator = TimetableGenerator(faculty_records)

timetable = generator.generate_timetable()

print("\n========== TIMEWISE AI TIMETABLE ==========")

for class_name, days in timetable.items():

    print("\nCLASS:", class_name)

    for day, lectures in days.items():

        print("\n", day)

        for lecture in lectures:

            print(
                lecture["time"],
                "|",
                lecture["subject"],
                "|",
                lecture["faculty_name"]
            )

print("\n========== TIMETABLE GENERATED SUCCESSFULLY ==========")
