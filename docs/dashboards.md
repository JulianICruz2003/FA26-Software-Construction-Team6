# Desktop dashboards

After sign-in, the desktop app selects the dashboard from the account role returned by `/auth/me`. Student and Professor accounts get separate dashboards and sidebar navigation. Unsupported roles see a message and can sign out. Server endpoints remain responsible for authorization.

- **Student Dashboard** lists the availability of enrolled classes, active projects, assigned tasks, and deadlines. Quick actions open My Classes, Join Class, My Projects, and My Tasks. From My Tasks, Open Project Tasks opens the selected project's Tasks tab or takes the user to the shared project browser to choose a project.
- **Professor Dashboard** lists the availability of classes taught, class projects, active projects, and tasks requiring attention. Quick actions open My Classes, Create Class, Class Projects, and Reviews / Progress.
- **Project Workspace** is available to both roles. Browse Shared Projects opens the existing searchable project list and standalone project creation. Open a project to access Overview, Tasks, Files, and Team. The workspace retains the selected project and tab while you move between pages. Files remain local selections.

The shared browser loads projects on demand and shows a retry message when loading fails. Its data comes from the existing shared project endpoint. Dashboard counts and personal or class-scoped lists remain unavailable until the corresponding endpoints enforce access. Class creation and joining currently open explanatory pages.

## Backend capabilities needed for integration

| Page | Authenticated API capabilities needed |
| --- | --- |
| Student My Classes and Join Class | List enrolled classes, get class details and associated projects, and enroll using a code. |
| Student My Projects | List projects by authorized ownership or membership and create a project in an enrolled class. |
| Student My Tasks | List tasks assigned to the signed-in student with project references, status, and due dates. |
| Professor My Classes and Create Class | List taught classes, create and manage classes, and get course identifiers, enrollment rosters, and project counts. |
| Professor Class Projects | List all projects in a class the professor teaches and authorize access to their workspaces, teams, and tasks. |
| Professor Reviews / Progress | Read class-scoped assignees, assignment and completion timestamps, due dates, statuses, and project progress. |
| Dashboard summaries | Derive metrics from authorized data, including agreed definitions for active projects, upcoming deadlines, and tasks requiring attention. |

Connect those capabilities through `ApiClient` once the team has agreed on endpoint contracts. The planned To Do, In Progress, and Completed statuses depend on the task-management changes. The existing workspace continues to use its current completion toggle.
