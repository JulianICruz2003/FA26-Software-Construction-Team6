from desktop.pages.dashboard import DashboardPage, FeaturePage


class ProfessorDashboard(DashboardPage):
    def __init__(self, name):
        super().__init__(
            "Professor Dashboard",
            name,
            "Manage your courses, review student projects, and follow project progress.",
            (
                ("Classes Taught", "Class management coming soon"),
                ("Total Class Projects", "Class project counts coming soon"),
                ("Active Projects", "Class project activity coming soon"),
                ("Tasks Requiring Attention", "Progress monitoring coming soon"),
            ),
            (
                ("View My Classes", "My Classes"),
                ("Create Class", "Create Class"),
                ("View Class Projects", "Class Projects"),
                ("Monitor Project Progress", "Reviews / Progress"),
            ),
            (
                ("My Classes", "Class management and enrollment rosters are under development."),
                ("Class Projects", "Project lists for classes you teach are under development."),
                ("Reviews / Progress", "Student task assignments, due dates, and completion "
                 "tracking are under development."),
            ),
        )

    def feature_pages(self):
        return {
            "My Classes": FeaturePage(
                "My Classes", "Class management is under development. This area will show "
                "your courses, course identifiers, enrollment rosters, and project counts."
            ),
            "Create Class": FeaturePage(
                "Create Class", "Class creation is under development."
            ),
            "Class Projects": FeaturePage(
                "Class Projects", "Class project lists require class ownership and project "
                "authorization. Select a class here when those features become available."
            ),
            "Reviews / Progress": FeaturePage(
                "Reviews / Progress", "Student assignments, assignment and completion times, "
                "task statuses, due dates, and overall project progress are under development."
            ),
        }
