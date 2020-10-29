from gi.repository import GObject, GtkSource, Gtk

from subprocess import Popen
from os import getenv
from typing import Optional, Tuple, Any

from ocrd_utils.constants import MIMETYPE_PAGE
from ocrd_models.ocrd_page import to_xml
from ocrd_browser.view import View
from ocrd_browser.view.base import FileGroupSelector, FileGroupFilter

GObject.type_register(GtkSource.View)


class ViewXml(View):
    """
    A view of the current PAGE-XML with syntax highlighting
    """

    label = 'PAGE-XML'

    def __init__(self, name: str, window: Gtk.Window):
        super().__init__(name, window)
        self.file_group: Tuple[Optional[str], Optional[str]] = (None, MIMETYPE_PAGE)
        # noinspection PyTypeChecker
        self.text_view: GtkSource.View = None
        # noinspection PyTypeChecker
        self.buffer: GtkSource.Buffer = None

    def build(self) -> None:
        super().build()
        self.add_configurator('file_group', FileGroupSelector(FileGroupFilter.PAGE))
        button = Gtk.Button.new_with_label('PageViewer')
        button.connect('clicked', self.open_jpageviewer)
        button.set_visible(True)
        self.action_bar.pack_start(button)

        lang_manager = GtkSource.LanguageManager()
        style_manager = GtkSource.StyleSchemeManager()

        self.text_view = GtkSource.View(visible=True, vexpand=False, editable=False, monospace=True,
                                        show_line_numbers=True,
                                        width_request=400)
        self.buffer = self.text_view.get_buffer()
        self.buffer.set_language(lang_manager.get_language('xml'))
        self.buffer.set_style_scheme(style_manager.get_scheme('tango'))

        self.scroller.add(self.text_view)

    @property
    def use_file_group(self) -> str:
        return self.file_group[0]

    def config_changed(self, name: str, value: Any) -> None:
        super().config_changed(name, value)
        self.reload()

    def open_jpageviewer(self, button: Gtk.Button) -> None:
        if self.current and self.current.file:
            # must be something like 'java -jar /path/to/JPageViewer.jar'
            if getenv('PAGEVIEWER'):
                pageviewer = getenv('PAGEVIEWER')
            else:
                pageviewer = 'pageviewer'
            Popen([pageviewer,
                   # without this, relative paths in imageFilename are resolved
                   # w.r.t. the PAGE file's directory, not the workspace directory
                   '--resolve-dir', str(self.document.directory),
                   str(self.document.path(self.current.file)),
                   # better omit this until prima-page-viewer#16 is fixed:
                   #str(self.document.path(self.current.pc_gts.get_Page().get_imageFilename()))
            ], cwd=self.document.directory)

    def redraw(self) -> None:
        if self.current:
            self.text_view.set_tooltip_text(self.page_id)
            if self.current.file:
                with self.document.path(self.current.file).open('r') as f:
                    text = f.read()
            else:
                text = to_xml(self.current.pc_gts)
            self.buffer.set_text(text)
        else:
            self.buffer.set_text('')

