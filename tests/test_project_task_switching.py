from unittest.mock import Mock

import httpx
import pytest

from desktop.pages.project_workspace import ProjectWorkspacePage


@pytest.mark.parametrize(
    "load_error",
    [httpx.ConnectError("connection lost"), ValueError("invalid response")],
    ids=["connection-failure", "invalid-response"],
)
def test_failed_project_switch_clears_tasks_and_retry_loads_current_project(
    qt_widget, load_error
):
    api_client = Mock()
    api_client.get_team_members.return_value = []
    api_client.get_tasks.side_effect = [
        [{"id": 10, "title": "First project task", "is_complete": False}],
        load_error,
        [{"id": 20, "title": "Second project task", "is_complete": False}],
        [{"id": 20, "title": "Second project task", "is_complete": True}],
    ]
    workspace = qt_widget(ProjectWorkspacePage, api_client)
    tasks = workspace.tasks_tab

    workspace.display_project({"id": 1, "name": "First project"})
    assert tasks.task_table.item(0, 0).text() == "First project task"
    tasks.task_table.selectRow(0)

    workspace.display_project({"id": 2, "name": "Second project"})
    assert tasks.project_label.text() == "Tasks for: Second project"
    assert tasks.task_table.rowCount() == 0
    assert not tasks.task_input.isEnabled()
    assert not tasks.add_button.isEnabled()
    assert not tasks.complete_button.isEnabled()
    assert not tasks.load_status.isHidden()
    assert "Could not load tasks" in tasks.load_status.text()
    assert not tasks.retry_button.isHidden()
    tasks.complete_button.click()
    api_client.update_task.assert_not_called()

    tasks.retry_button.click()
    assert [call.args for call in api_client.get_tasks.call_args_list] == [
        (1,), (2,), (2,)
    ]
    assert tasks.task_table.rowCount() == 1
    assert tasks.task_table.item(0, 0).text() == "Second project task"
    assert tasks.retry_button.isHidden()
    assert tasks.load_status.isHidden()
    assert tasks.add_button.isEnabled()
    assert tasks.complete_button.isEnabled()

    tasks.task_table.selectRow(0)
    tasks.complete_button.click()
    api_client.update_task.assert_called_once_with(2, 20, True)
    assert tasks.task_table.item(0, 1).text() == "Complete"
