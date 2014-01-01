from concurrent.futures import Future
from unittest import mock

from gmncurses.ui import signals, views
from gmncurses import controllers, config
from gmncurses.executor import Executor
from gmncurses.core import StateMachine

from . import factories


# AUTH

def test_when_clicking_login_button_controllers_handle_login_method_is_called():
    login_view = factories.login_view("", "")
    _ = mock.Mock()
    login_controller = controllers.auth.LoginController(login_view, _, _)
    login_controller.handle_login_request = mock.Mock()
    signals.emit(login_view.login_button, "click")
    assert login_controller.handle_login_request.call_count == 1

def test_login_controller_prints_an_error_message_on_unsuccessful_login():
    login_view = factories.login_view("admin", "123123")
    login_view.notifier = mock.Mock()
    executor = factories.patched_executor(login_response=factories.future(None))
    _ = mock.Mock()
    login_controller = controllers.auth.LoginController(login_view, executor, _)

    signals.emit(login_view.login_button, "click")

    assert login_view.notifier.error_msg.call_count == 1

# PROJECTS

def test_login_controller_transitions_to_projects_on_successful_login():
    username, password = "admin", "123123"
    login_view = factories.login_view(username, password)

    resp = Future()
    resp.set_result(factories.successful_login_response(username))
    f = mock.Mock()
    f.add_done_callback = lambda f: f(resp)
    executor  = mock.Mock()
    executor.login = mock.Mock(return_value=f)
    state_machine = mock.Mock()
    login_controller = controllers.auth.LoginController(login_view, executor, state_machine)

    signals.emit(login_view.login_button, "click")

    assert state_machine.logged_in.call_count == 1

def test_projects_controller_click_on_project_requests_the_project_detail():
    projects = factories.projects()
    projects_view = views.projects.ProjectsView()
    executor = factories.patched_executor()
    _ = mock.Mock()
    projects_controller = controllers.projects.ProjectsController(projects_view, executor, _)

    signals.emit(projects_view.project_buttons[0], "click")

    executor.project_detail.assert_called_with(projects[0])

def test_projects_controller_when_requesting_a_project_info_message_is_shown():
    projects = factories.projects()
    projects_view = views.projects.ProjectsView()
    projects_view.notifier = mock.Mock()
    executor = factories.patched_executor()
    _ = mock.Mock()
    projects_controller = controllers.projects.ProjectsController(projects_view, executor, _)

    signals.emit(projects_view.project_buttons[0], "click")

    assert projects_view.notifier.info_msg.call_count == 1

def test_projects_controller_click_on_project_when_project_is_fetched_transitions_to_project_detail():
    projects = factories.projects()
    fetched_project = projects[0]
    projects_view = views.projects.ProjectsView()
    executor = factories.patched_executor(project_detail=factories.future(fetched_project))
    state_machine = mock.Mock()
    projects_controller = controllers.projects.ProjectsController(projects_view, executor, state_machine)

    signals.emit(projects_view.project_buttons[0], "click")

    state_machine.project_detail.assert_called_with(fetched_project)

def test_projects_controller_when_project_fetching_fails_a_error_message_is_shown():
    projects = factories.projects()
    fetched_project = projects[0]
    projects_view = views.projects.ProjectsView()
    projects_view.notifier = mock.Mock()
    executor = factories.patched_executor(project_detail=factories.future(None))
    _ = mock.Mock()
    projects_controller = controllers.projects.ProjectsController(projects_view, executor, _)

    signals.emit(projects_view.project_buttons[0], "click")

    assert projects_view.notifier.error_msg.call_count == 1

# BACKLOG

def test_project_detail_controller_fetches_user_stories_and_transitions_to_backlog():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    executor = factories.patched_executor()
    state_machine = StateMachine(mock.Mock(), StateMachine.PROJECTS)
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor,
                                                                             state_machine)

    assert state_machine.state == state_machine.PROJECT_BACKLOG

def test_project_detail_backlog_controller_show_the_help_popup():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    executor = factories.patched_executor()
    _ = mock.Mock()
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor, _)

    assert not hasattr(project_detail_controller.view.backlog, "help_popup")
    project_detail_controller.handle(config.ProjectBacklogKeys.HELP)
    assert hasattr(project_detail_controller.view.backlog, "help_popup")

def test_project_detail_backlog_controller_show_the_new_user_story_form():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    executor = factories.patched_executor()
    _ = mock.Mock()
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor, _)

    assert not hasattr(project_detail_controller.view.backlog, "user_story_form")
    project_detail_controller.handle(config.ProjectBacklogKeys.CREATE_USER_STORY)
    assert hasattr(project_detail_controller.view.backlog, "user_story_form")

def test_project_detail_backlog_controller_submit_new_user_story_form_with_errors():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    project_view.backlog.notifier = mock.Mock()
    executor = factories.patched_executor()
    _ = mock.Mock()
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor, _)
    project_detail_controller.handle(config.ProjectBacklogKeys.CREATE_USER_STORY)
    form = project_detail_controller.view.backlog.user_story_form

    signals.emit(form.save_button, "click")
    assert project_view.backlog.notifier.error_msg.call_count == 1

def test_project_detail_backlog_controller_submit_new_user_story_form_successfully():
    us_subject = "Create a new user story"
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    project_view.backlog.notifier = mock.Mock()
    executor = factories.patched_executor(create_user_story_response=factories.future(
                           factories.successful_create_user_story_response(us_subject)))
    _ = mock.Mock()
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor, _)
    project_detail_controller.handle(config.ProjectBacklogKeys.CREATE_USER_STORY)
    form = project_detail_controller.view.backlog.user_story_form
    project_view.backlog.notifier.reset_mock()

    form._subject_edit.set_edit_text(us_subject)
    signals.emit(form.save_button, "click")
    assert project_view.backlog.notifier.info_msg.call_count == 1
    assert executor.create_user_story.call_args.call_list()[0][0][0]["subject"] == us_subject
    assert executor.create_user_story.call_count == 1
    assert executor.create_user_story.return_value.result()["subject"] == us_subject

def test_project_detail_backlog_controller_show_the_edit_user_story_form():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    executor = factories.patched_executor()
    _ = mock.Mock()
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor, _)

    assert not hasattr(project_detail_controller.view.backlog, "user_story_form")
    project_detail_controller.handle(config.ProjectBacklogKeys.EDIT_USER_STORY)
    assert hasattr(project_detail_controller.view.backlog, "user_story_form")
    assert (project_detail_controller.view.backlog.user_story_form.user_story ==
            project_detail_controller.view.backlog.user_stories.widget.get_focus().user_story)

def test_project_detail_backlog_controller_submit_the_edit_user_story_form_with_errors():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    project_view.backlog.notifier = mock.Mock()
    executor = factories.patched_executor()
    _ = mock.Mock()
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor, _)
    project_detail_controller.handle(config.ProjectBacklogKeys.EDIT_USER_STORY)
    form = project_detail_controller.view.backlog.user_story_form

    form._subject_edit.set_edit_text("")
    signals.emit(form.save_button, "click")
    assert project_view.backlog.notifier.error_msg.call_count == 1

def test_project_detail_backlog_controller_submit_edit_user_story_form_successfully():
    us_subject = "Update a user story"
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    project_view.backlog.notifier = mock.Mock()
    executor = factories.patched_executor(update_user_story_response=factories.future(
                           factories.successful_update_user_story_response(us_subject)))
    _ = mock.Mock()
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor, _)
    project_detail_controller.handle(config.ProjectBacklogKeys.EDIT_USER_STORY)
    form = project_detail_controller.view.backlog.user_story_form
    project_view.backlog.notifier.reset_mock()

    form._subject_edit.set_edit_text(us_subject)
    signals.emit(form.save_button, "click")
    assert project_view.backlog.notifier.info_msg.call_count == 1
    assert (executor.update_user_story.call_args.call_list()[0][0][0]["id"] ==
            project_detail_controller.view.backlog.user_story_form.user_story["id"])
    assert executor.update_user_story.call_args.call_list()[0][0][1]["subject"] == us_subject
    assert executor.update_user_story.call_count == 1
    assert executor.update_user_story.return_value.result()["subject"] == us_subject

def test_project_detail_backlog_controller_move_user_story_down():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    project_view.backlog.notifier = mock.Mock()
    executor = factories.patched_executor()
    _ = mock.Mock()
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor, _)
    project_view.backlog.notifier.reset_mock()

    us_a_old = project_detail_controller.backlog.user_stories[0]
    us_b_old = project_detail_controller.backlog.user_stories[1]

    project_detail_controller.handle(config.ProjectBacklogKeys.US_DOWN)
    assert project_view.backlog.notifier.info_msg.call_count == 1

    us_b_new = project_detail_controller.backlog.user_stories[0]
    us_a_new = project_detail_controller.backlog.user_stories[1]

    assert us_a_old == us_a_new
    assert us_b_old == us_b_new

def test_project_detail_backlog_controller_move_user_story_up():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    project_view.backlog.notifier = mock.Mock()
    executor = factories.patched_executor()
    _ = mock.Mock()
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor, _)
    project_detail_controller.view.backlog.user_stories.widget.contents.focus = 2
    project_view.backlog.notifier.reset_mock()

    us_a_old = project_detail_controller.backlog.user_stories[0]
    us_b_old = project_detail_controller.backlog.user_stories[1]

    project_detail_controller.handle(config.ProjectBacklogKeys.US_UP)
    assert project_view.backlog.notifier.info_msg.call_count == 1

    us_b_new = project_detail_controller.backlog.user_stories[0]
    us_a_new = project_detail_controller.backlog.user_stories[1]

    assert us_a_old == us_a_new
    assert us_b_old == us_b_new

def test_project_detail_backlog_controller_update_user_stories_order_with_errors():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    project_view.backlog.notifier = mock.Mock()
    executor = factories.patched_executor(update_user_stories_order_response=factories.future(None))
    _ = mock.Mock()
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor, _)

    project_detail_controller.handle(config.ProjectBacklogKeys.UPDATE_USER_STORIES_ORDER)
    assert project_view.backlog.notifier.error_msg.call_count == 1

def test_project_detail_backlog_controller_update_user_stories_order_with_success():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    project_view.backlog.notifier = mock.Mock()
    executor = factories.patched_executor()
    _ = mock.Mock()
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor, _)
    project_view.backlog.notifier.reset_mock()

    project_detail_controller.handle(config.ProjectBacklogKeys.UPDATE_USER_STORIES_ORDER)
    assert project_view.backlog.notifier.info_msg.call_count == 1

def test_project_detail_backlog_controller_delete_user_story_with_errors():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    project_view.backlog.notifier = mock.Mock()
    executor = factories.patched_executor(delete_user_story_response=factories.future(None))
    _ = mock.Mock()
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor, _)

    project_detail_controller.handle(config.ProjectBacklogKeys.DELETE_USER_STORY)
    assert project_view.backlog.notifier.error_msg.call_count == 1
    assert (executor.delete_user_story.call_args.call_list()[0][0][0]["id"] ==
            project_detail_controller.backlog.user_stories[0]["id"])

def test_project_detail_backlog_controller_delete_user_story_order_with_success():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    project_view.backlog.notifier = mock.Mock()
    executor = factories.patched_executor()
    _ = mock.Mock()
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor, _)
    project_view.backlog.notifier.reset_mock()

    project_detail_controller.handle(config.ProjectBacklogKeys.DELETE_USER_STORY)
    assert project_view.backlog.notifier.info_msg.call_count == 1
    assert (executor.delete_user_story.call_args.call_list()[0][0][0]["id"] ==
            project_detail_controller.backlog.user_stories[0]["id"])

# ISSUES

def test_project_detail_controller_fetches_issues_and_transitions_to_issues():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    executor = factories.patched_executor()
    state_machine = StateMachine(mock.Mock(), StateMachine.PROJECTS)
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor,
                                                                             state_machine)
    assert state_machine.state == state_machine.PROJECT_BACKLOG

    project_detail_controller.handle(config.ProjectKeys.ISSUES)
    assert state_machine.state == state_machine.PROJECT_ISSUES

def test_project_detail_issues_controller_show_the_help_popup():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    executor = factories.patched_executor()
    _ = mock.Mock()
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor, _)
    project_detail_controller.handle(config.ProjectKeys.ISSUES)

    assert not hasattr(project_detail_controller.view.issues, "help_popup")
    project_detail_controller.handle(config.ProjectIssuesKeys.HELP)
    assert hasattr(project_detail_controller.view.issues, "help_popup")

# MILESTONES

def test_project_detail_controller_fetches_task_and_transitions_to_sprint_taskboard():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    executor = factories.patched_executor()
    state_machine = StateMachine(mock.Mock(), StateMachine.PROJECTS)
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor,
                                                                             state_machine)
    assert state_machine.state == state_machine.PROJECT_BACKLOG

    project_detail_controller.handle(config.ProjectKeys.MILESTONES)
    assert state_machine.state == state_machine.PROJECT_MILESTONES

def test_project_detail_sprints_controller_show_the_help_popup():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    executor = factories.patched_executor()
    _ = mock.Mock()
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor, _)
    project_detail_controller.handle(config.ProjectKeys.MILESTONES)

    assert not hasattr(project_detail_controller.view.sprint, "help_popup")
    project_detail_controller.handle(config.ProjectMilestoneKeys.HELP)
    assert hasattr(project_detail_controller.view.sprint, "help_popup")

# WIKI

def test_project_detail_controller_fetches_wiki_pages_and_transitions_to_wiki():
    project = factories.project()
    project_view = views.projects.ProjectDetailView(project)
    executor = factories.patched_executor()
    state_machine = StateMachine(mock.Mock(), StateMachine.PROJECTS)
    project_detail_controller = controllers.projects.ProjectDetailController(project_view, executor,
                                                                             state_machine)
    assert state_machine.state == state_machine.PROJECT_BACKLOG

    project_detail_controller.handle(config.ProjectKeys.WIKI)
    assert state_machine.state == state_machine.PROJECT_WIKI
