#!/usr/bin/env python
# Modifications by Alex Lee <lee@ccs.neu.edu>
#              and Nick Aldwin <nick@aldwin.us>
# This module originated from the demos.
#
# Copyright (C) 2007, 2008, 2009 Jan Michael Alonzo <jmalonzo@gmai.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gobject
import gtk
import webkit


class BrowserPage(webkit.WebView):

    def __init__(self):
        webkit.WebView.__init__(self)
        # scale other content besides from text as well
        self.set_full_content_zoom(True)


class TabLabel(gtk.HBox):
    """A class for Tab labels"""

    __gsignals__ = {
        "close": (gobject.SIGNAL_RUN_FIRST,
                  gobject.TYPE_NONE,
                  (gobject.TYPE_OBJECT, ))}

    def __init__(self, title, child):
        """initialize the tab label"""
        gtk.HBox.__init__(self, False, 4)
        self.title = title
        self.label = gtk.Label(title)
        self.label.props.max_width_chars = 30
        self.label.set_alignment(0.0, 0.5)
        self.set_data("label", self.label)

    def set_label(self, text):
        """sets the text of this label"""
        self.label.set_label(text)

    def _close_tab(self, widget, child):
        self.emit("close", child)


class ContentPane(gtk.Notebook):

    __gsignals__ = {
        "focus-view-title-changed": (gobject.SIGNAL_RUN_FIRST,
                                     gobject.TYPE_NONE,
                                     (gobject.TYPE_OBJECT,
                                      gobject.TYPE_STRING)),
        "new-window-requested": (gobject.SIGNAL_RUN_FIRST,
                                 gobject.TYPE_NONE,
                                 (gobject.TYPE_OBJECT,))}

    def __init__(self):
        """initialize the content pane"""
        gtk.Notebook.__init__(self)
        self.props.scrollable = True
        self.props.homogeneous = True
        self.connect("switch-page", self._switch_page)
        self.show_all()

    def load(self, text):
        """load the given uri in the current web view"""
        child = self.get_nth_page(self.get_current_page())
        view = child.get_child()
        view.open(text)

    def new_tab_with_webview(self, webview):
        """creates a new tab with the given webview as its child"""
        self._construct_tab_view(webview)

    def new_tab(self, url=None):
        """creates a new page in a new tab"""
        # create the tab content
        browser = BrowserPage()
        self._construct_tab_view(browser, url)

    def _construct_tab_view(self, web_view, url=None):
        web_view.connect("load-finished", self._view_load_finished_cb)
        web_view.connect("create-web-view", self._new_web_view_request_cb)
        web_view.connect("title-changed", self._title_changed_cb)

        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.props.hscrollbar_policy = gtk.POLICY_AUTOMATIC
        scrolled_window.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
        scrolled_window.add(web_view)
        scrolled_window.show_all()

        # create the tab
        label = TabLabel(url, scrolled_window)
        label.connect("close", self._close_tab)
        label.show_all()

        new_tab_number = self.append_page(scrolled_window, label)
        self.set_tab_label_packing(scrolled_window, False, False,
                                   gtk.PACK_START)
        self.set_tab_label(scrolled_window, label)

        # hide the tab if there's only one
        self.set_show_tabs(self.get_n_pages() > 1)

        self.show_all()
        self.set_current_page(new_tab_number)

        # load the content
        web_view.load_uri(url)

    def _open_in_new_tab(self, menuitem, view):
        self.new_tab(self._hovered_uri)

    def _close_tab(self, label, child):
        page_num = self.page_num(child)
        if page_num != -1:
            view = child.get_child()
            view.destroy()
            self.remove_page(page_num)
        self.set_show_tabs(self.get_n_pages() > 1)

    def _switch_page(self, notebook, page, page_num):
        child = self.get_nth_page(page_num)
        view = child.get_child()
        frame = view.get_main_frame()
        self.emit("focus-view-title-changed", frame, frame.props.title)

    def _title_changed_cb(self, view, frame, title):
        child = self.get_nth_page(self.get_current_page())
        label = self.get_tab_label(child)
        label.set_label(title)
        self.emit("focus-view-title-changed", frame, title)

    def _view_load_finished_cb(self, view, frame):
        child = self.get_nth_page(self.get_current_page())
        label = self.get_tab_label(child)
        title = frame.get_title()
        if not title:
            title = frame.get_uri()
        if title:
            label.set_label(title)

    def _new_web_view_request_cb(self, web_view, web_frame):
        scrolled_window = gtk.ScrolledWindow()
        scrolled_window.props.hscrollbar_policy = gtk.POLICY_AUTOMATIC
        scrolled_window.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
        view = BrowserPage()
        scrolled_window.add(view)
        scrolled_window.show_all()

        vbox = gtk.VBox(spacing=1)
        vbox.pack_start(scrolled_window, True, True)

        window = gtk.Window()
        window.add(vbox)
        view.connect("web-view-ready", self._new_web_view_ready_cb)
        return view

    def _new_web_view_ready_cb(self, web_view):
        self.emit("new-window-requested", web_view)


class WebToolbar(gtk.Toolbar):

    __gsignals__ = {
        "load-requested": (gobject.SIGNAL_RUN_FIRST,
                           gobject.TYPE_NONE,
                           (gobject.TYPE_STRING,))}

    def __init__(self, location_enabled=True):
        gtk.Toolbar.__init__(self)
        # location entry
        if location_enabled:
            self._entry = gtk.Entry()
            self._entry.connect('activate', self._entry_activate_cb)
            entry_item = gtk.ToolItem()
            entry_item.set_expand(True)
            entry_item.add(self._entry)
            self._entry.show()
            self.insert(entry_item, -1)
            entry_item.show()

    def location_set_text(self, text):
        if hasattr(self, '_entry'):
            self._entry.set_text(text)

    def _entry_activate_cb(self, entry):
        self.emit("load-requested", entry.props.text)


class WebBrowser(gtk.Window):

    def __init__(self, url, show_toolbar=True):
        gtk.Window.__init__(self)
        toolbar = WebToolbar(show_toolbar)
        content_tabs = ContentPane()
        content_tabs.connect("focus-view-title-changed",
                             self._title_changed_cb, toolbar)
        toolbar.connect("load-requested", load_requested_cb, content_tabs)
        vbox = gtk.VBox(spacing=0)
        vbox.pack_start(toolbar, expand=False, fill=False)
        vbox.pack_start(content_tabs)
        self.add(vbox)
        self.set_default_size(800, 600)
        self.connect('destroy', destroy_cb, content_tabs)
        self.show_all()
        content_tabs.new_tab(url)

        #hide cursor initially
        #(it still shows up if the mouse is moved)
        pix_data = """/* XPM */
 static char * invisible_xpm[] = {
 "1 1 1 1",
 "       c None",
 " "};"""
        color = gtk.gdk.Color()
        pix = gtk.gdk.pixmap_create_from_data(None,
                                              pix_data,
                                              1, 1, 1, color, color)
        invisible = gtk.gdk.Cursor(pix, pix, color, color, 0, 0)
        self.window.set_cursor(invisible)

    def _title_changed_cb(self, tabbed_pane, frame, title, toolbar):
        uri = frame.get_uri()
        if uri:
            toolbar.location_set_text(uri)


# event handlers
def load_requested_cb(widget, text, content_pane):
    if not text:
        return
    content_pane.load(text)


def destroy_cb(window, content_pane):
    """destroy window resources"""
    num_pages = content_pane.get_n_pages()
    while num_pages != -1:
        child = content_pane.get_nth_page(num_pages)
        if child:
            view = child.get_child()
        num_pages = num_pages - 1
    window.destroy()


def main(url):
    webbrowser = WebBrowser(url)
    webbrowser.fullscreen()
    gtk.main()
