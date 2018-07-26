"""Provide basic utilities for pyRevit scripts."""

import sys
import os
import os.path as op

from pyrevit import EXEC_PARAMS
from pyrevit.coreutils import logger
from pyrevit.coreutils import appdata
from pyrevit.coreutils import envvars
from pyrevit import framework
from pyrevit import revit
from pyrevit import output

# suppress any warning generated by native or third-party modules
import warnings
warnings.filterwarnings("ignore")


mlogger = logger.get_logger(__name__)


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
    """Return alternate script path of the current pyRevit command.

    Returns:
        str: alternate script path
    """
    return EXEC_PARAMS.command_alt_path


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
        :obj:`pyrevit.usagelog.record.CommandCustomResults`:
            Command results dict
    """
    from pyrevit.usagelog.record import CommandCustomResults
    return CommandCustomResults()


def get_pyrevit_version():
    """Return pyRevit version.

    Returns:
        :obj:`pyrevit.versionmgr.PyRevitVersion`: pyRevit version provider
    """
    from pyrevit.versionmgr import PYREVIT_VERSION
    return PYREVIT_VERSION


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


def get_config():
    """Create and return config section parser object for current script.

    Returns:
        :obj:`pyrevit.coreutils.configparser.PyRevitConfigSectionParser`:
            Config section parser object
    """
    from pyrevit.userconfig import user_config
    script_cfg_postfix = 'config'

    try:
        return user_config.get_section(EXEC_PARAMS.command_name +
                                       script_cfg_postfix)
    except Exception:
        return user_config.add_section(EXEC_PARAMS.command_name +
                                       script_cfg_postfix)


def save_config():
    """Save pyRevit config.

    Scripts should call this to save any changes they have done to their
    config section object received from script.get_config() method.
    """
    from pyrevit.userconfig import user_config
    user_config.save_changes()


def reset_config():
    """Reset pyRevit config.

    Script should call this to reset any saved configuration by removing section related to current script
    """
    from pyrevit.userconfig import user_config
    script_cfg_postfix = 'config'

    user_config.remove_section(EXEC_PARAMS.command_name +
                                   script_cfg_postfix)
    user_config.save_changes()


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
    proj_info = revit.get_project_info()

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


def journal_write(data_key, msg):
    """Write key and value to active Revit journal for current command.

    Args:
        data_key (str): data key
        msg (str): data value string
    """
    # Get the StringStringMap class which can write data into.
    # noinspection PyUnresolvedReferences
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
    # noinspection PyUnresolvedReferences
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
    uibutton = get_button()
    if not uibutton:
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
    mlogger.debug('Setting icon state to: {} ({})'
                  .format(new_state, icon_path))
    uibutton.set_icon(icon_path)


def exit():
    """Stop the script execution and exit."""
    sys.exit()


def show_file_in_explorer(file_path):
    """Show file in Windows Explorer."""
    import subprocess
    subprocess.Popen(r'explorer /select,"{}"'
                     .format(os.path.normpath(file_path)))


def open_url(url):
    """Open url in a new tab in default webbrowser."""
    import webbrowser
    return webbrowser.open_new_tab(url)


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
