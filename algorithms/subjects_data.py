
# AKTU 2026-27 B.Tech First Year
# Semester 1 Subject Database

BRANCHES = {
    "CSE": "CSE",
    "CSE AI/ML": "CSE",
    "IT": "CSE",
    "ECE": "ECE",
    "Chemical Engineering": "CH",
    "Biotechnology": "BT"
}

SUBJECTS = {

    "CSE": {
        "semester_1": [
            {
                "type": "choice",
                "subjects": [
                    ("AAS101E", "Quantum Physics and Applications"),
                    ("AAS102D", "Applied Chemistry for Smart Systems")
                ]
            },
            ("AAS103D", "Calculus and Linear Algebra"),
            {
                "type": "choice",
                "subjects": [
                    ("AEE101A", "Fundamentals of Electrical Engineering"),
                    ("AEC101A", "Fundamentals of Electronics Engineering")
                ]
            },
            ("ACS101", "Programming Languages"),
            {
                "type": "choice",
                "subjects": [
                    ("AAS104", "Introduction to Indian Knowledge System"),
                    ("AAS105", "Professional Communication and Technical Writing")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("AAI101", "Introduction to AI and Prompt Engineering"),
                    ("AME101A", "Fundamentals of Mechanical Engineering")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("AAS151", "Applied Physics Lab"),
                    ("AAS152D", "Applied Chemistry for Smart Systems Lab")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("AEE151A", "Electrical Engineering Lab"),
                    ("AEC151A", "Electronics Engineering Lab")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("ACE151E", "Computer-Aided Engineering Drawing Lab"),
                    ("AID151", "Innovation and Design Thinking Lab")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("AAS153", "Language Lab"),
                    ("AAC101", "Environment and Sustainability")
                ]
            },
            ("AGP151", "General Proficiency")
        ]
    },

    "ECE": {
        "semester_1": [
            {
                "type": "choice",
                "subjects": [
                    ("AAS101C", "Quantum Physics and Electronic Sensors"),
                    ("AAS102C", "Applied Chemistry for Emerging Electronics and Futuristic Devices")
                ]
            },
            ("AAS103C", "Differential Calculus and Linear Algebra"),
            {
                "type": "choice",
                "subjects": [
                    ("AEE101A", "Fundamentals of Electrical Engineering"),
                    ("AEC101A", "Fundamentals of Electronics Engineering")
                ]
            },
            ("ACS101", "Programming Languages"),
            {
                "type": "choice",
                "subjects": [
                    ("AAS104", "Introduction to Indian Knowledge System"),
                    ("AAS105", "Professional Communication and Technical Writing")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("AAI101", "Introduction to AI and Prompt Engineering"),
                    ("AME101A", "Fundamentals of Mechanical Engineering")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("AAS151", "Applied Physics Lab"),
                    ("AAS152C", "Applied Chemistry Lab")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("AEE151A", "Electrical Engineering Lab"),
                    ("AEC151A", "Electronics Engineering Lab")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("ACE151C", "Computer-Aided Engineering Drawing Lab"),
                    ("AID151", "Innovation and Design Thinking Lab")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("AAS153", "Language Lab"),
                    ("AAC101", "Environment and Sustainability")
                ]
            },
            ("AGP151", "General Proficiency")
        ]
    },

    "CH": {
        "semester_1": [
            {
                "type": "choice",
                "subjects": [
                    ("AAS101G", "Physics of Process Engineering Materials"),
                    ("AAS102G", "Applied Chemistry for Process Engineering and Industrial Applications")
                ]
            },
            ("AAS103G", "Differential Calculus and Linear Algebra"),
            {
                "type": "choice",
                "subjects": [
                    ("AEE101B", "Fundamentals of Electrical Engineering"),
                    ("AEC101B", "Fundamentals of Electronics Engineering")
                ]
            },
            ("ACS101", "Programming Languages"),
            {
                "type": "choice",
                "subjects": [
                    ("AAS104", "Introduction to Indian Knowledge System"),
                    ("AAS105", "Professional Communication and Technical Writing")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("AAI101", "Introduction to AI and Prompt Engineering"),
                    ("AME101C", "Fundamentals of Mechanical Engineering")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("AAS151", "Applied Physics Lab"),
                    ("AAS152G", "Applied Chemistry Lab")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("AEE151B", "Electrical Engineering Lab"),
                    ("AEC151B", "Electronics Engineering Lab")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("ACE151F", "Computer-Aided Engineering Drawing Lab"),
                    ("AID151", "Innovation and Design Thinking Lab")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("AAS153", "Language Lab"),
                    ("AAC101", "Environment and Sustainability")
                ]
            },
            ("AGP151", "General Proficiency")
        ]
    },

    "BT": {
        "semester_1": [
            {
                "type": "choice",
                "subjects": [
                    ("AAS101F", "Physics of Materials and Biomaterials"),
                    ("AAS102F", "Applied Chemistry for Biomolecules and Bioprocess Systems")
                ]
            },
            ("AAS103F", "Calculus and Linear Algebra"),
            {
                "type": "choice",
                "subjects": [
                    ("AEE101C", "Fundamentals of Electrical Engineering"),
                    ("AEC101C", "Fundamentals of Electronics Engineering")
                ]
            },
            ("ACS101", "Programming Languages"),
            {
                "type": "choice",
                "subjects": [
                    ("AAS104", "Introduction to Indian Knowledge System"),
                    ("AAS105", "Professional Communication and Technical Writing")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("AAI101", "Introduction to AI and Prompt Engineering"),
                    ("AME101C", "Fundamentals of Mechanical Engineering")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("AAS151", "Applied Physics Lab"),
                    ("AAS152F", "Applied Chemistry Lab")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("AEE151C", "Electrical Engineering Lab"),
                    ("AEC151C", "Electronics Engineering Lab")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("ACE151G", "Computer-Aided Engineering Drawing Lab"),
                    ("AID151", "Innovation and Design Thinking Lab")
                ]
            },
            {
                "type": "choice",
                "subjects": [
                    ("AAS153", "Language Lab"),
                    ("AAC101", "Environment and Sustainability")
                ]
            },
            ("AGP151", "General Proficiency")
        ]
    }
}
