import os
import os.path as op

from pyrevit import HOST_APP, PyRevitException
from pyrevit.coreutils import ScriptFileParser, cleanup_string
from pyrevit.coreutils.logger import get_logger
import pyrevit.extensions as exts
from pyrevit.userconfig import user_config


logger = get_logger(__name__)


class GenericComponent(object):
    type_id = None

    def __init__(self):
        self.name = None

    def __repr__(self):
        return '<GenericComponent object with name \'{}\'>'.format(self.name)

    @property
    def is_container(self):
        return hasattr(self, '__iter__')

    def get_cache_data(self):
        cache_dict = self.__dict__.copy()
        cache_dict['type_id'] = self.type_id
        return cache_dict

    def load_cache_data(self, cache_dict):
        for k, v in cache_dict.items():
            self.__dict__[k] = v


class GenericUIComponent(GenericComponent):
    def __init__(self):
        GenericComponent.__init__(self)
        self.directory = None
        self.name = None
        self.unique_name = None
        self.library_path = None
        self.syspath_search_paths = []
        self.icon_file = None

    def __init_from_dir__(self, ext_dir):
        if not ext_dir.lower().endswith(self.type_id):
            raise PyRevitException('Can not initialize from directory: {}'
                                   .format(ext_dir))
        self.directory = ext_dir
        self.unique_name = self._get_unique_name()

    def __repr__(self):
        return '<type_id \'{}\' name \'{}\' @ \'{}\'>'\
            .format(self.type_id, self.name, self.directory)

    def _get_unique_name(self):
        """Creates a unique name for the command. This is used to uniquely
        identify this command and also to create the class in
        pyRevit dll assembly. Current method create a unique name based on
        the command full directory address.
        Example:
            self.direcotry =
            '/pyRevit.extension/pyRevit.tab/Edit.panel/Flip doors.pushbutton'
            unique name =
            pyRevitpyRevitEditFlipdoors
        """
        uname = ''
        inside_ext = False
        dir_str = self.directory
        for dname in dir_str.split(op.sep):
            if exts.UI_EXTENSION_POSTFIX in dname:
                inside_ext = True

            name, ext = op.splitext(dname)
            if ext != '' and inside_ext:
                uname += name
            else:
                continue
        return cleanup_string(uname)

    @property
    def bundle_name(self):
        return self.name + self.type_id

    def get_search_paths(self):
        return self.syspath_search_paths

    def get_lib_path(self):
        return self.library_path

    def has_syspath(self, path):
        return path in self.syspath_search_paths

    def add_syspath(self, path):
        if path and not self.has_syspath(path):
            logger.debug('Appending syspath: {} to {}'.format(path, self))
            self.syspath_search_paths.append(path)

    def remove_syspath(self, path):
        if path and self.has_syspath(path):
            logger.debug('Removing syspath: {} from {}'.format(path, self))
            return self.syspath_search_paths.remove(path)
        else:
            return None

    def get_bundle_file(self, file_name):
        file_addr = op.join(self.directory, file_name)
        return file_addr if op.exists(file_addr) else None


# superclass for all UI group items (tab, panel, button groups, stacks) --------
class GenericUIContainer(GenericUIComponent):
    allowed_sub_cmps = []

    def __init__(self):
        GenericUIComponent.__init__(self)
        self._sub_components = []
        self.layout_list = None

    def __init_from_dir__(self, ext_dir):
        GenericUIComponent.__init_from_dir__(self, ext_dir)

        self._sub_components = []

        self.name = op.splitext(op.basename(self.directory))[0]
        self.ui_title = self.name

        # each container can store custom libraries under
        # /Lib inside the container folder
        lib_path = op.join(self.directory, exts.COMP_LIBRARY_DIR_NAME)
        self.library_path = lib_path if op.exists(lib_path) else None

        # setting up search paths. These paths will be added to
        # all sub-components of this component.
        if self.library_path:
            self.syspath_search_paths.append(self.library_path)

        self.layout_list = self._read_layout_file()
        logger.debug('Layout is: {}'.format(self.layout_list))

        full_file_path = op.join(self.directory, exts.DEFAULT_ICON_FILE)
        self.icon_file = full_file_path if op.exists(full_file_path) else None
        if self.icon_file:
            logger.debug('Icon file is: {}'
                         .format(self.name, self.icon_file))

    def __iter__(self):
        return iter(self._get_components_per_layout())

    def _read_layout_file(self):
        full_file_path = op.join(self.directory, exts.DEFAULT_LAYOUT_FILE_NAME)
        if op.exists(full_file_path):
            layout_file = open(op.join(self.directory,
                                       exts.DEFAULT_LAYOUT_FILE_NAME), 'r')
            # return [x.replace('\n', '') for x in layout_file.readlines()]
            return layout_file.read().splitlines()
        else:
            logger.debug('Container does not have layout file defined: {}'
                         .format(self))

    def _get_components_per_layout(self):
        # if item is not listed in layout, it will not be created
        if self.layout_list and self._sub_components:
            logger.debug('Reordering components per layout file...')
            layout_index = 0
            _processed_cmps = []
            for layout_item in self.layout_list:
                for cmp_index, component in enumerate(self._sub_components):
                    if component.name == layout_item:
                        _processed_cmps.append(component)
                        layout_index += 1
                        break

            # insert separators and slideouts per layout definition
            logger.debug('Adding separators and slide outs per layout...')
            last_item_index = len(self.layout_list) - 1
            for i_index, layout_item in enumerate(self.layout_list):
                if exts.SEPARATOR_IDENTIFIER in layout_item \
                        and i_index < last_item_index:
                    separator = GenericComponent()
                    separator.type_id = exts.SEPARATOR_IDENTIFIER
                    _processed_cmps.insert(i_index, separator)
                elif exts.SLIDEOUT_IDENTIFIER in layout_item \
                        and i_index < last_item_index:
                    slideout = GenericComponent()
                    slideout.type_id = exts.SLIDEOUT_IDENTIFIER
                    _processed_cmps.insert(i_index, slideout)

            logger.debug('Reordered sub_component list is: {}'
                         .format(_processed_cmps))
            return _processed_cmps
        else:
            return self._sub_components

    def contains(self, item_name):
        for component in self._sub_components:
            if item_name == component.name:
                return True

    def add_syspath(self, path):
        if path and not self.has_syspath(path):
            logger.debug('Appending syspath: {} to {}'.format(path, self))
            for component in self._sub_components:
                component.add_syspath(path)
            self.syspath_search_paths.append(path)

    def remove_syspath(self, path):
        if path and self.has_syspath(path):
            logger.debug('Removing syspath: {} from {}'.format(path, self))
            for component in self._sub_components:
                component.remove_syspath(path)
            return self.syspath_search_paths.remove(path)
        else:
            return None

    def add_component(self, comp):
        for path in self.syspath_search_paths:
            comp.add_syspath(path)
        self._sub_components.append(comp)

    def get_components(self):
        return self._sub_components

    def get_components_of_type(self, cmp_type):
        sub_comp_list = []
        for sub_comp in self._sub_components:
            if isinstance(sub_comp, cmp_type):
                sub_comp_list.append(sub_comp)
            elif sub_comp.is_container:
                sub_comp_list.extend(sub_comp.get_components_of_type(cmp_type))

        return sub_comp_list


# superclass for all single command classes (link, push button, toggle button)
# GenericUICommand is not derived from GenericUIContainer since a command
# can not contain other elements
class GenericUICommand(GenericUIComponent):
    """Superclass for all single commands.
    The information provided by these classes will be used to create a
    push button under Revit UI. However, pyRevit expands the capabilities of
    push button beyond what is provided by Revit UI. (e.g. Toggle button
    changes it's icon based on its on/off status)
    See LinkButton and ToggleButton classes.
    """
    def __init__(self):
        GenericUIComponent.__init__(self)
        self.ui_title = None
        self.script_file = self.config_script_file = None
        self.ttvideo_file = None
        self.max_revit_ver = self.min_revit_ver = None
        self.doc_string = self.author = None
        self.cmd_help_url = self.cmd_context = None
        self.unique_name = self.unique_avail_name = None
        self.class_name = self.avail_class_name = None
        self.beta_cmd = False
        self.requires_clean_engine = False
        self.requires_fullframe_engine = False

    def __init_from_dir__(self, cmd_dir):
        GenericUIComponent.__init_from_dir__(self, cmd_dir)

        self.name = op.splitext(op.basename(self.directory))[0]
        self.ui_title = self.name

        # setting up a unique availability name for command.
        self.unique_avail_name = \
            self.unique_name + exts.COMMAND_AVAILABILITY_NAME_POSTFIX

        icon_path = op.join(self.directory, exts.DEFAULT_ICON_FILE)
        self.icon_file = icon_path if op.exists(icon_path) else None
        logger.debug('Command {}: Icon file is: {}'
                     .format(self, self.icon_file))

        ttvideo_path = op.join(self.directory, exts.DEFAULT_TOOLTIP_VIDEO_FILE)
        self.ttvideo_file = ttvideo_path if op.exists(ttvideo_path) else None
        logger.debug('Command {}: Tooltip video file is: {}'
                     .format(self, self.ttvideo_file))

        self.script_file = self._find_script_file([exts.PYTHON_SCRIPT_POSTFIX,
                                                   exts.CSHARP_SCRIPT_POSTFIX,
                                                   exts.VB_SCRIPT_POSTFIX,
                                                   exts.RUBY_SCRIPT_POSTFIX])

        if self.script_file is None:
            logger.error('Command {}: Does not have script file.'.format(self))
            raise PyRevitException()
        if self.script_language == exts.PYTHON_LANG:
            self._analyse_python_script()

        self.config_script_file = \
            self._find_script_file([exts.DEFAULT_CONFIG_SCRIPT_FILE])

        if self.config_script_file is None:
            logger.debug('Command {}: Does not have independent config script.'
                         .format(self))
            self.config_script_file = self.script_file

        # each command can store custom libraries under
        # /Lib inside the command folder
        lib_path = op.join(self.directory, exts.COMP_LIBRARY_DIR_NAME)
        self.library_path = lib_path if op.exists(lib_path) else None

        # setting up search paths. These paths will be added to sys.path by
        # the command loader for easy imports.
        self.syspath_search_paths.append(self.directory)
        if self.library_path:
            self.syspath_search_paths.append(self.library_path)

    def _find_script_file(self, script_postfixes):
        for bundle_file in os.listdir(self.directory):
            for script_postfix in script_postfixes:
                if bundle_file.endswith(script_postfix):
                    return op.join(self.directory, bundle_file)
        return None

    def _analyse_python_script(self):
        try:
            # reading script file content to extract parameters
            script_content = ScriptFileParser(self.get_full_script_address())
            # extracting min requried Revit and pyRevit versions
            extracted_ui_title = \
                script_content.extract_param(exts.UI_TITLE_PARAM)  # type: str
            if extracted_ui_title:
                self.ui_title = extracted_ui_title

            self.doc_string = script_content.get_docstring()
            custom_docstring = \
                script_content.extract_param(exts.DOCSTRING_PARAM)  # type: str
            if custom_docstring:
                self.doc_string = custom_docstring

            self.author = script_content.extract_param(
                exts.AUTHOR_PARAM)  # type: str
            self.max_revit_ver = script_content.extract_param(
                exts.MAX_REVIT_VERSION_PARAM)  # type: str
            self.min_revit_ver = script_content.extract_param(
                exts.MIN_REVIT_VERSION_PARAM)  # type: str
            self.cmd_help_url = script_content.extract_param(
                exts.COMMAND_HELP_URL)  # type: str

            # panel buttons should be active always
            if self.type_id != exts.PANEL_PUSH_BUTTON_POSTFIX:
                self.cmd_context = script_content.extract_param(
                    exts.COMMAND_CONTEXT_PARAM)  # type: str
                if type(self.cmd_context) is list:
                    self.cmd_context = ';'.join(self.cmd_context)
            else:
                self.cmd_context = exts.CTX_ZERODOC

            self.beta_cmd = script_content.extract_param(
                exts.BETA_SCRIPT_PARAM)  # type: bool

            # only True when command is specifically asking for
            # a clean engine or a fullframe engine. False if not set.
            self.requires_clean_engine = script_content.extract_param(
                exts.CLEAN_ENGINE_SCRIPT_PARAM, False)  # type: bool
            self.requires_fullframe_engine = script_content.extract_param(
                exts.FULLFRAME_ENGINE_PARAM, False)  # type: bool

        except PyRevitException as script_parse_err:
            logger.error('Error parsing script file: {} | {}'
                         .format(self.script_file, script_parse_err))
        except Exception as generic_parse_err:
            logger.error('Error reading script file: {} | {}'
                         .format(self.script_file, generic_parse_err))

        # fixme: logger reports module as 'ast' after a
        # successfull param retrieval. Must be ast.literal_eval()
        logger.debug('Maximum host version: {}'.format(self.max_revit_ver))
        logger.debug('Minimum host version: {}'.format(self.min_revit_ver))
        logger.debug('command tooltip: {}'.format(self.doc_string))
        logger.debug('Command author: {}'.format(self.author))
        logger.debug('Command help url: {}'.format(self.cmd_help_url))

        if self.beta_cmd:
            logger.debug('Command is in beta.')

        try:
            # check minimum requirements
            self._check_dependencies()
        except PyRevitException as dependency_err:
            logger.debug(dependency_err)
            raise dependency_err

    def _check_dependencies(self):
        if self.min_revit_ver:
            # If host is older than the minimum host version, raise exception
            if int(HOST_APP.version) < int(self.min_revit_ver):
                raise PyRevitException('Script requires min host version: {}'
                                       .format(self.min_revit_ver))
        if self.max_revit_ver:
            # If host is newer than the max host version, raise exception
            if int(HOST_APP.version) > int(self.max_revit_ver):
                raise PyRevitException('Script requires max host version: {}'
                                       .format(self.max_revit_ver))

    @property
    def script_language(self):
        if self.script_file is not None:
            if self.script_file.endswith(exts.PYTHON_SCRIPT_FILE_FORMAT):
                return exts.PYTHON_LANG
            elif self.script_file.endswith(exts.CSHARP_SCRIPT_FILE_FORMAT):
                return exts.CSHARP_LANG
            elif self.script_file.endswith(exts.VB_SCRIPT_FILE_FORMAT):
                return exts.VB_LANG
        else:
            return None

    @staticmethod
    def is_valid_cmd():
        return True

    def has_config_script(self):
        return self.config_script_file != self.script_file

    def get_help_url(self):
        return self.cmd_help_url

    def get_full_script_address(self):
        return op.join(self.directory, self.script_file)

    def get_full_config_script_address(self):
        return op.join(self.directory, self.config_script_file)

    def add_syspath(self, path):
        if path and not self.has_syspath(path):
            logger.debug('Appending syspath: {} to {}'.format(path, self))
            self.syspath_search_paths.append(path)
