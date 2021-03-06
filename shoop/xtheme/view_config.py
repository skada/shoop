# -*- coding: utf-8 -*-
# This file is part of Shoop.
#
# Copyright (c) 2012-2015, Shoop Ltd. All rights reserved.
#
# This source code is licensed under the AGPLv3 license found in the
# LICENSE file in the root directory of this source tree.
from django.utils.encoding import force_text

from shoop.xtheme.layout import Layout
from shoop.xtheme.models import SavedViewConfig


class ViewConfig(object):
    """
    A view configuration.

    Contains layout and plugin configuration for all placeholders in a given view.

    This class does not directly correspond to a database model; it may act as a
    container for `SavedViewConfig` objects, and wraps the `SavedViewConfig` API.
    """

    def __init__(self, theme, view_name, draft):
        """
        Initialize a view configuration.

        :param theme: Theme object (could be None to not touch the database)
        :type theme: shoop.xtheme.theme.Theme|None
        :param view_name: View name (the class name of the view)
        :type view_name: str
        :param draft: Load in draft mode?
        :type draft: bool
        """
        self.theme = theme
        self.view_name = force_text(view_name)
        self.draft = bool(draft)
        self._saved_view_config = None

    @property
    def saved_view_config(self):
        """
        Get a saved view config model depending on the current parameters.

        :return: A SavedViewConfig object for the current theme/view/draft mode, or None
        :rtype: shoop.xtheme.models.SavedViewConfig|None
        """
        if not self.theme or not self.theme.identifier:
            return None

        if self._saved_view_config is None:
            self._saved_view_config = SavedViewConfig.objects.appropriate(
                theme=self.theme,
                view_name=self.view_name,
                draft=self.draft
            )
            self.draft = self._saved_view_config.draft
        return self._saved_view_config

    def get_placeholder_layout(self, placeholder_name, default_layout=None):
        """
        Get a Layout object for the given placeholder.

        :param placeholder_name: The name of the placeholder to load.
        :type placeholder_name: str
        :param default_layout: Default layout configuration (either a dict or an actual Layout)
        :type default_layout: dict|Layout
        :return: Layout
        :rtype: Layout
        """
        svc = self.saved_view_config
        if svc:
            placeholder_data = svc.get_layout_data(placeholder_name)
            if placeholder_data:
                return Layout.unserialize(data=placeholder_data, placeholder_name=placeholder_name)
        if default_layout:
            if isinstance(default_layout, Layout):
                return default_layout
            return Layout.unserialize(default_layout)
        return Layout(placeholder_name=placeholder_name)

    def save_default_placeholder_layout(self, placeholder_name, layout):
        """
        Save a default placeholder layout (only if no data for the PH already
        exists).

        :param placeholder_name: Placeholder name
        :type placeholder_name: str
        :param layout: Layout or layout data
        :type layout: Layout|dict
        :return: True if saved
        :rtype: bool
        """
        if not self.draft:
            return False
        if self.saved_view_config and self.saved_view_config.get_layout_data(placeholder_name) is None:
            self.save_placeholder_layout(placeholder_name, layout)
            return True
        return False

    def publish(self):
        """
        Publish this revision of the view configuration as the currently public one.

        :return: Success flag
        :rtype: bool
        """
        svc = self.saved_view_config
        if not svc:
            raise ValueError("Unable to publish view config. Is a theme set?")
        svc.publish()
        self.draft = svc.draft
        return True

    def revert(self):
        """
        Revert this revision of the view configuration, if it's a draft.

        :return: Success flag
        :rtype: bool
        """
        svc = self.saved_view_config
        if not svc:
            raise ValueError("Unable to revert view config. Is a theme set?")
        svc.revert()
        self.draft = True
        self._saved_view_config = None
        return True

    def save_placeholder_layout(self, placeholder_name, layout):
        """
        Save the given layout as the layout for the given placeholder.

        :param placeholder_name: The placeholder name.
        :type placeholder_name: str
        :param layout: Layout object (or dict)
        :type layout: Layout|dict
        """
        svc = self.saved_view_config
        if not svc:
            raise ValueError("Unable to retrieve view config; unable to save data. Is a theme set?")
        svc.set_layout_data(placeholder_name, layout)
        svc.save()
