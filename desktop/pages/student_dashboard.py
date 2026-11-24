from desktop.pages.dashboard import DashboardPage, FeaturePage


class StudentDashboard(DashboardPage):
    def __init__(self, name):
        super().__init__(
            "Student Dashboard",
            name,
            "Find your classes, open project workspaces, and keep track of your academic work.",
            (
                ("Enrolled Classes", "Enrollment coming soon"),
                ("Active Projects", "Personal project counts coming soon"),
                ("Assigned Tasks", "Task assignment coming soon"),
                ("Upcoming Deadlines", "Personal deadlines coming soon"),
            ),
            (
                ("View My Classes", "My Classes"),
                ("Join Class", "Join Class"),
                ("View My Projects", "My Projects"),
                ("View My Tasks", "My Tasks"),
            ),
            (
                ("My Classes", "Class details and enrollment by code are under development."),
                ("My Projects", "Personal project lists are under development. "
                 "Visit Project Workspace to browse existing shared projects."),
                ("My Tasks", "Assigned tasks and their due dates are under development. "
                 "You can still open a project's Tasks tab."),
            ),
        )

    def feature_pages(self):
        return {
            "My Classes": FeaturePage(
                "My Classes", "Class enrollment and access to class details and projects "
                "are under development."
            ),
            "Join Class": FeaturePage(
                "Join Class", "Joining a class with an enrollment code is under development."
            ),
            "My Projects": FeaturePage(
                "My Projects", "Your personal project list requires project ownership or "
                "membership filtering. Creating projects within a class is under development."
            ),
            "My Tasks": FeaturePage(
                "My Tasks", "Your assigned tasks, project names, statuses, and due dates "
                "will appear here when task assignment is available."
            ),
        }
