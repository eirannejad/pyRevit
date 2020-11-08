"""Provide basic utilities for pyRevit scripts.

Example:
    >>> from pyrevit import script
    >>> script.clipboard_copy('some text')
    >>> data = script.journal_read('data-key')
    >>> script.exit()
"""

import sys
import os
import os.path as op
import warnings
import re
import codecs
import json
import csv
import pickle

from pyrevit import EXEC_PARAMS, PyRevitException
from pyrevit import coreutils
from pyrevit.coreutils import logger
from pyrevit.coreutils import appdata
from pyrevit.coreutils import envvars
from pyrevit import framework
from pyrevit import revit
from pyrevit import output
from pyrevit import versionmgr
from pyrevit.labs import PyRevit


# suppress any warning generated by native or third-party modules
warnings.filterwarnings("ignore")

#pylint: disable=W0703,C0302,C0103,W0614
mlogger = logger.get_logger(__name__)


DATAFEXT = 'pym'


def get_info():
    """Return info on current pyRevit command.

    Returns:
        :obj:`pyrevit.extensions.genericcomps.GenericUICommand`:
            Command info object
    """
    from pyrevit.extensions.extensionmgr import get_command_from_path
    return get_command_from_path(EXEC_PARAMS.command_path)


def get_script_path():
    """Return script path of the current pyRevit command.

    Returns:
        str: script path
    """
    return EXEC_PARAMS.command_path


def get_alt_script_path():
    """Return config script path of the current pyRevit command.

    Returns:
        str: config script path
    """
    return EXEC_PARAMS.command_config_path


def get_bundle_name():
    """Return bundle name of the current pyRevit command.

    Returns:
        str: bundle name (e.g. MyButton.pushbutton)
    """
    return EXEC_PARAMS.command_bundle


def get_extension_name():
    """Return extension name of the current pyRevit command.

    Returns:
        str: extension name (e.g. MyExtension.extension)
    """
    return EXEC_PARAMS.command_extension


def get_unique_id():
    """Return unique id of the current pyRevit command.

    Returns:
        str: command unique id
    """
    return EXEC_PARAMS.command_uniqueid


def get_results():
    """Return command results dictionary for logging.

    Returns:
        :obj:`pyrevit.telemetry.record.CommandCustomResults`:
            Command results dict
    """
    from pyrevit.telemetry.record import CommandCustomResults
    return CommandCustomResults()


def get_pyrevit_version():
    """Return pyRevit version.

    Returns:
        :obj:`pyrevit.versionmgr._PyRevitVersion`: pyRevit version provider
    """
    return versionmgr.get_pyrevit_version()


def get_logger():
    """Create and return logger named for current script.

    Returns:
        :obj:`pyrevit.coreutils.logger.LoggerWrapper`: Logger object
    """
    return logger.get_logger(EXEC_PARAMS.command_name)


def get_output():
    """Return object wrapping output window for current script.

    Returns:
        :obj:`pyrevit.output.PyRevitOutputWindow`: Output wrapper object
    """
    return output.get_output()


def get_config(section=None):
    """Create and return config section parser object for current script.

    Args:
        section (str, optional): config section name

    Returns:
        :obj:`pyrevit.coreutils.configparser.PyRevitConfigSectionParser`:
            Config section parser object
    """
    from pyrevit.userconfig import user_config
    if not section:
        script_cfg_postfix = 'config'
        section = EXEC_PARAMS.command_name + script_cfg_postfix

    try:
        return user_config.get_section(section)
    except Exception:
        return user_config.add_section(section)


def save_config():
    """Save pyRevit config.

    Scripts should call this to save any changes they have done to their
    config section object received from script.get_config() method.
    """
    from pyrevit.userconfig import user_config
    user_config.save_changes()


def reset_config(section=None):
    """Reset pyRevit config.

    Script should call this to reset any save configuration by removing
    section related to current script.

    Args:
        section (str, optional): config section name
    """
    from pyrevit.userconfig import user_config
    if not section:
        script_cfg_postfix = 'config'
        section = EXEC_PARAMS.command_name + script_cfg_postfix
    elif section in [PyRevit.PyRevitConsts.ConfigsCoreSection]:
        raise PyRevitException('Can not remove internal config section: {}'
                               .format(section))

    try:
        user_config.remove_section(section)
        user_config.save_changes()
    except Exception:
        mlogger.debug('Failed resetting config for %s (%s)',
                      EXEC_PARAMS.command_name, section)


def get_universal_data_file(file_id, file_ext, add_cmd_name=False):
    """Return filename to be used by a user script to store data.

    File name is generated in this format:
    ``pyRevit_{file_id}.{file_ext}``

    Example:
        >>> script.get_universal_data_file('mydata', 'data')
        '.../pyRevit_mydata.data'
        >>> script.get_universal_data_file('mydata', 'data', add_cmd_name=True)
        '.../pyRevit_Command Name_mydata.data'

    Universal data files are not cleaned up at pyRevit startup.
    Script should manage cleaning up these files.

    Args:
        file_id (str): unique id for the filename
        file_ext (str): file extension
        add_cmd_name (bool, optional): add command name to file name

    Returns:
        str: full file path
    """
    if add_cmd_name:
        script_file_id = '{}_{}'.format(EXEC_PARAMS.command_name, file_id)
    else:
        script_file_id = file_id

    return appdata.get_universal_data_file(script_file_id, file_ext)


def get_data_file(file_id, file_ext, add_cmd_name=False):
    """Return filename to be used by a user script to store data.

    File name is generated in this format:
    ``pyRevit_{Revit Version}_{file_id}.{file_ext}``

    Example:
        >>> script.get_data_file('mydata', 'data')
        '.../pyRevit_2018_mydata.data'
        >>> script.get_data_file('mydata', 'data', add_cmd_name=True)
        '.../pyRevit_2018_Command Name_mydata.data'

    Data files are not cleaned up at pyRevit startup.
    Script should manage cleaning up these files.

    Args:
        file_id (str): unique id for the filename
        file_ext (str): file extension
        add_cmd_name (bool, optional): add command name to file name

    Returns:
        str: full file path
    """
    if add_cmd_name:
        script_file_id = '{}_{}'.format(EXEC_PARAMS.command_name, file_id)
    else:
        script_file_id = file_id

    return appdata.get_data_file(script_file_id, file_ext)


def get_instance_data_file(file_id, add_cmd_name=False):
    """Return filename to be used by a user script to store data.

    File name is generated in this format:
    ``pyRevit_{Revit Version}_{Process Id}_{file_id}.{file_ext}``

    Example:
        >>> script.get_instance_data_file('mydata')
        '.../pyRevit_2018_6684_mydata.tmp'
        >>> script.get_instance_data_file('mydata', add_cmd_name=True)
        '.../pyRevit_2018_6684_Command Name_mydata.tmp'

    Instance data files are cleaned up at pyRevit startup.

    Args:
        file_id (str): unique id for the filename
        add_cmd_name (bool, optional): add command name to file name

    Returns:
        str: full file path
    """
    if add_cmd_name:
        script_file_id = '{}_{}'.format(EXEC_PARAMS.command_name, file_id)
    else:
        script_file_id = file_id

    return appdata.get_instance_data_file(script_file_id)


def get_document_data_file(file_id, file_ext, add_cmd_name=False):
    """Return filename to be used by a user script to store data.

    File name is generated in this format:
    ``pyRevit_{Revit Version}_{file_id}_{Project Name}.{file_ext}``

    Example:
        >>> script.get_document_data_file('mydata', 'data')
        '.../pyRevit_2018_mydata_Project1.data'
        >>> script.get_document_data_file('mydata', 'data', add_cmd_name=True)
        '.../pyRevit_2018_Command Name_mydata_Project1.data'

    Document data files are not cleaned up at pyRevit startup.
    Script should manage cleaning up these files.

    Args:
        file_id (str): unique id for the filename
        file_ext (str): file extension
        add_cmd_name (bool, optional): add command name to file name

    Returns:
        str: full file path
    """
    proj_info = revit.query.get_project_info()

    if add_cmd_name:
        script_file_id = '{}_{}_{}'.format(EXEC_PARAMS.command_name,
                                           file_id,
                                           proj_info.filename
                                           or proj_info.name)
    else:
        script_file_id = '{}_{}'.format(file_id,
                                        proj_info.filename
                                        or proj_info.name)

    return appdata.get_data_file(script_file_id, file_ext)


def get_bundle_file(file_name):
    """Return full path to file under current script bundle.

    Args:
        file_name (str): bundle file name

    Returns:
        str: full bundle file path
    """
    return op.join(EXEC_PARAMS.command_path, file_name)


def get_bundle_files(sub_path=None):
    """Return full path to all file under current script bundle.

    Returns:
        list[str]: list of bundle file paths
    """
    if sub_path:
        command_path = op.join(EXEC_PARAMS.command_path, sub_path)
    else:
        command_path = EXEC_PARAMS.command_path
    return [op.join(command_path, x) for x in os.listdir(command_path)]


def journal_write(data_key, msg):
    """Write key and value to active Revit journal for current command.

    Args:
        data_key (str): data key
        msg (str): data value string
    """
    # Get the StringStringMap class which can write data into.
    data_map = EXEC_PARAMS.command_data.JournalData
    data_map.Clear()

    # Begin to add the support data
    data_map.Add(data_key, msg)


def journal_read(data_key):
    """Read value for provided key from active Revit journal.

    Args:
        data_key (str): data key

    Returns:
        str: data value string
    """
    # Get the StringStringMap class which can write data into.
    data_map = EXEC_PARAMS.command_data.JournalData

    # Begin to get the support data
    return data_map[data_key]


def get_button():
    """Find and return current script ui button.

    Returns:
        :obj:`pyrevit.coreutils.ribbon._PyRevitRibbonButton`: ui button object
    """
    from pyrevit.coreutils.ribbon import get_current_ui
    pyrvt_tabs = get_current_ui().get_pyrevit_tabs()
    for tab in pyrvt_tabs:
        button = tab.find_child(EXEC_PARAMS.command_name)
        if button:
            return button
    return None


def get_all_buttons():
    """Find and return all ui buttons matching current script command name.

    Sometimes tools are duplicated across extensions for user access control
    so this would help smart buttons to find all the loaded buttons and make
    icon adjustments.

    Returns:
        :obj:`list(pyrevit.coreutils.ribbon._PyRevitRibbonButton)`:
            list of ui button objects
    """
    from pyrevit.coreutils.ribbon import get_current_ui
    pyrvt_tabs = get_current_ui().get_pyrevit_tabs()
    buttons = []
    for tab in pyrvt_tabs:
        button = tab.find_child(EXEC_PARAMS.command_name)
        if button:
            buttons.append(button)
    return buttons


def toggle_icon(new_state, on_icon_path=None, off_icon_path=None):
    """Set the state of button icon (on or off).

    This method expects on.png and off.png in command bundle for on and off
    icon states, unless full path of icon states are provided.

    Args:
        new_state (bool): state of the ui button icon.
        on_icon_path (str, optional): full path of icon for on state.
                                      default='on.png'
        off_icon_path (str, optional): full path of icon for off state.
                                       default='off.png'
    """
    # find the ui button
    uibuttons = get_all_buttons()
    if not uibuttons:
        mlogger.debug('Can not find ui button.')
        return

    # get icon for on state
    if not on_icon_path:
        on_icon_path = get_bundle_file('on.png')
        if not on_icon_path:
            mlogger.debug('Script does not have icon for on state.')
            return

    # get icon for off state
    if not off_icon_path:
        off_icon_path = get_bundle_file('off.png')
        if not off_icon_path:
            mlogger.debug('Script does not have icon for on state.')
            return

    icon_path = on_icon_path if new_state else off_icon_path
    mlogger.debug('Setting icon state to: %s (%s)',
                  new_state, icon_path)

    for uibutton in uibuttons:
        uibutton.set_icon(icon_path)


def exit():     #pylint: disable=W0622
    """Stop the script execution and exit."""
    sys.exit()


def show_file_in_explorer(file_path):
    """Show file in Windows Explorer."""
    coreutils.show_entry_in_explorer(file_path)


def show_folder_in_explorer(folder_path):
    """Show folder in Windows Explorer."""
    coreutils.open_folder_in_explorer(folder_path)


def open_url(url):
    """Open url in a new tab in default webbrowser."""
    import webbrowser
    if re.match('^https*://', url.lower()):
        webbrowser.open_new_tab(url)
    else:
        webbrowser.open_new_tab('http://' + url)


def clipboard_copy(string_to_copy):
    """Copy string to Windows Clipboard."""
    framework.Clipboard.SetText(string_to_copy)


def load_index(index_file='index.html'):
    """Load html file into output window.

    This method expects index.html file in the current command bundle,
    unless full path to an html file is provided.

    Args:
        index_file (str, optional): full path of html file.
    """
    outputwindow = get_output()
    if not op.isfile(index_file):
        index_file = get_bundle_file(index_file)
    outputwindow.open_page(index_file)


def load_ui(ui_instance, ui_file='ui.xaml', set_owner=True):
    ui_file = get_bundle_file(ui_file)
    if ui_file:
        ui_instance.load_xaml(
            ui_file,
            literal_string=False,
            handle_esc=True,
            set_owner=set_owner
            )
        ui_instance.setup()
        return ui_instance
    else:
        raise PyRevitException("Missing bundle ui file: {}".format(ui_file))


def get_envvar(envvar):
    """Return value of give pyRevit environment variable.

    The environment variable system is used to retain small values in memory
    between script runs (e.g. active/inactive state for toggle tools). Do not
    store large objects in memory using this method. List of currently set
    environment variables could be sees in pyRevit settings window.

    Args:
        envvar (str): name of environment variable

    Returns:
        any: type of object stored in environment variable

    Example:
        >>> script.get_envvar('ToolActiveState')
        True
    """
    return envvars.get_pyrevit_env_var(envvar)


def set_envvar(envvar, value):
    """Set value of give pyRevit environment variable.

    The environment variable system is used to retain small values in memory
    between script runs (e.g. active/inactive state for toggle tools). Do not
    store large objects in memory using this method. List of currently set
    environment variables could be sees in pyRevit settings window.

    Args:
        envvar (str): name of environment variable
        value (any): value of environment variable

    Example:
        >>> script.set_envvar('ToolActiveState', False)
        >>> script.get_envvar('ToolActiveState')
        False
    """
    return envvars.set_pyrevit_env_var(envvar, value)


def dump_json(data, filepath):
    """Dumps given data into given json file.

    Args:
        data (object): serializable data to be dumped
        filepath (str): json file path
    """
    json_repr = json.dumps(data, indent=4, ensure_ascii=False)
    with codecs.open(filepath, 'w', "utf-8") as json_file:
        json_file.write(json_repr)


def load_json(filepath):
    """Loads data from given json file.

    Args:
        filepath (str): json file path

    Returns:
        object: deserialized data
    """
    with codecs.open(filepath, 'r', "utf-8") as json_file:
        return json.load(json_file)


def dump_csv(data, filepath):
    """Dumps given data into given csv file.

    Args:
        data (list[list[str]]): data to be dumped
        filepath (str): csv file path
    """
    with codecs.open(filepath, 'wb', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='\"')
        writer.writerows(data)


def load_csv(filepath):
    """Read lines from given csv file

    Args:
        filepath (str): csv file path

    Returns:
        list[list[str]]: csv data
    """
    with codecs.open(filepath, 'rb', encoding='utf-8') as csvfile:
        return list(csv.reader(csvfile, delimiter=',', quotechar='\"'))


def store_data(slot_name, data, this_project=True):
    """Wraps python pickle.dump() to easily store data to pyRevit data files

    To store native Revit objects, use revit.serialize(). See Example

    Args:
        slot_name (type): desc
        data (obj): any pickalable data
        this_project (bool): data belongs to this project only

    Example:
        >>> from pyrevit import revit
        ... from pyrevit import script
        ...
        ...
        ... class CustomData(object):
        ...     def __init__(self, count, element_ids):
        ...         self._count = count
        ...         # serializes the Revit native objects
        ...         self._elmnt_ids = [revit.serialize(x) for x in element_ids]
        ...
        ...     @property
        ...     def count(self):
        ...         return self._count
        ...
        ...     @property
        ...     def element_ids(self):
        ...         # de-serializes the Revit native objects
        ...         return [x.deserialize() for x in self._elmnt_ids]
        ...
        ...
        ... mydata = CustomData(
        ...     count=3,
        ...     element_ids=[<DB.ElementId>, <DB.ElementId>, <DB.ElementId>]
        ... )
        ...
        ... script.store_data("Selected Elements", mydata)

    """
    # for this specific project?
    if this_project:
        data_file = get_document_data_file(file_id=slot_name,
                                           file_ext=DATAFEXT,
                                           add_cmd_name=False)
    # for any project file
    else:
        data_file = get_data_file(file_id=slot_name,
                                  file_ext=DATAFEXT,
                                  add_cmd_name=False)

    with open(data_file, 'w') as dfile:
        pickle.dump(data, dfile)


def load_data(slot_name, this_project=True):
    """Wraps python pickle.load() to easily load data from pyRevit data files

    To recover native Revit objects, use revit.deserialize(). See Example

    Similar to pickle module, the custom data types must be defined in the main
    scope so the loader can create an instance and return original stored data

    Args:
        slot_name (type): desc
        this_project (bool): data belongs to this project only

    Returns:
        obj: stored data

    Example:
        >>> from pyrevit import revit
        ... from pyrevit import script
        ...
        ...
        ... class CustomData(object):
        ...     def __init__(self, count, element_ids):
        ...         self._count = count
        ...         # serializes the Revit native objects
        ...         self._elmnt_ids = [revit.serialize(x) for x in element_ids]
        ...
        ...     @property
        ...     def count(self):
        ...         return self._count
        ...
        ...     @property
        ...     def element_ids(self):
        ...         # de-serializes the Revit native objects
        ...         return [x.deserialize() for x in self._elmnt_ids]
        ...
        ...
        ... mydata = script.load_data("Selected Elements", element_ids)
        ... mydata.element_ids
        [<DB.ElementId>, <DB.ElementId>, <DB.ElementId>]
    """
    # for this specific project?
    if this_project:
        data_file = get_document_data_file(file_id=slot_name,
                                           file_ext=DATAFEXT,
                                           add_cmd_name=False)
    # for any project file
    else:
        data_file = get_data_file(file_id=slot_name,
                                  file_ext=DATAFEXT,
                                  add_cmd_name=False)

    with open(data_file, 'r') as dfile:
        return pickle.load(dfile)


def data_exists(slot_name, this_project=True):
    """Checks if data file in a specified slot and for certain project exists.

    Args:
        slot_name (type): desc
        this_project (bool): data belongs to this project only

    Returns:
        bool: true if the path exists
    """
    # for this specific project?
    if this_project:
        data_file = get_document_data_file(file_id=slot_name,
                                           file_ext=DATAFEXT,
                                           add_cmd_name=False)
    # for any project file
    else:
        data_file = get_data_file(file_id=slot_name,
                                  file_ext=DATAFEXT,
                                  add_cmd_name=False)
    return os.path.exists(data_file)