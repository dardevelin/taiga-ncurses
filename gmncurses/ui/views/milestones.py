# -*- coding: utf-8 -*-

"""
gmncurses.ui.views.milestones
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""

import urwid

from gmncurses.ui.widgets import generic, milestones, backlog

from . import base


class ProjectMilestoneSubView(base.SubView):
    help_popup_title = "Milestone Help Info"
    help_popup_info = base.SubView.help_popup_info + (
       ( "Milestone Movements:", (
           ("↑ | k | ctrl p", "Move Up"),
           ("↓ | j | ctrl n", "Move Down"),
           #("← | h | ctrl b", "Move Left"),
           #("→ | l | ctrl f", "Move Right"),
       )),
       ( "Milestone Actions:", (
           ("m", "Change to another Milestone"),
           ("N", "Create new US (TODO)"),
           ("n", "Create new Task (TODO)"),
           ("e", "Edit selected US/Task (TODO Task)"),
           ("Supr", "Delete selected US/Task"),
       )),
    )

    def __init__(self, parent_view, project, notifier, tabs):
        super().__init__(parent_view)

        self.project = project
        self.notifier = notifier

        self.info = milestones.MilestoneInfo(project)
        self.stats = milestones.MilestoneStats(project)
        self.taskboard = milestones.MilestoneTaskboard(project)

        self.widget = urwid.ListBox(urwid.SimpleListWalker([
            tabs,
            generic.box_solid_fill(" ", 1),
            self.info,
            generic.box_solid_fill(" ", 1),
            self.stats,
            generic.box_solid_fill(" ", 1),
            self.taskboard,
        ]))

    def open_user_story_form(self, user_story={}):
        self.user_story_form = backlog.UserStoryForm(self.project, user_story=user_story)
        # FIXME: Calculate the form size
        self.parent.show_widget_on_top(self.user_story_form, 80, 24)

    def close_user_story_form(self):
        del self.user_story_form
        self.parent.hide_widget_on_top()

    def get_user_story_form_data(self):
        if hasattr(self, "user_story_form"):
            data = {
                "subject": self.user_story_form.subject,
                "milestone": self.user_story_form.milestone,
                "points": self.user_story_form.points,
                "status": self.user_story_form.status,
                "tags": self.user_story_form.tags,
                "description": self.user_story_form.description,
                "team_requirement": self.user_story_form.team_requirement,
                "client_requirement": self.user_story_form.client_requirement,
                "project": self.project["id"],
            }
            return data
        return {}

    def open_milestones_selector_popup(self, current_milestone={}):
        self.milestone_selector_popup = milestones.MIlestoneSelectorPopup(self.project, current_milestone)
        # FIXME: Calculate the popup size
        self.parent.show_widget_on_top(self.milestone_selector_popup, 100, 28)

    def close_milestone_selector_popup(self):
        del self.milestone_selector_popup
        self.parent.hide_widget_on_top()
