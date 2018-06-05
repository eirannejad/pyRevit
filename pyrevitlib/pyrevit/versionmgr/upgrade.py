"""
perform upgrades between versions here,
e.g. adding a new config parameter

"""

import pyrevit.coreutils.appdata as appdata
from pyrevit.coreutils import find_loaded_asm, get_revit_instance_count


def _filelogging_config_upgrade(user_config):
    """ Upgrades local files and settings per this commit changes.
    commit message:   Added file handler to logger
    commit hash:      d5c1cb548bfc08530d9f8b6ba9899e8f46f1d631
    """

    try:
        assert user_config.core.filelogging
    except:
        user_config.core.filelogging = False
        user_config.save_changes()


def _cleanup_cache_files():
    """ Upgrades local files and settings per this commit changes.
    commit message:   Organized data files per Revit version in appdata folder
    commit hash:      44dd765c0f662f3faf5a40b92e3c5173804be37f
    """
    cache_file_exts = ['pickle', 'json', 'log', 'pym']
    for cache_file_ext in cache_file_exts:
        for cache_file_path in appdata.list_data_files(file_ext=cache_file_ext,
                                                       universal=True):
                appdata.garbage_data_file(cache_file_path)

    # Cleanup Universal Dll files
    if get_revit_instance_count() == 1:
        for asm_file_path in appdata.list_data_files(file_ext='dll',
                                                     universal=True):
            if not find_loaded_asm(asm_file_path, by_location=True):
                appdata.garbage_data_file(asm_file_path)


def _loadbeta_config_upgrade(user_config):
    """ Upgrades local files and settings per this commit changes.
    commit message:   Added support for __beta__ Issue# 155
    commit hash:      d1237aa50a430f86a9362af5c2471c16254fd20e
    """

    try:
        assert user_config.core.loadbeta
    except:
        user_config.core.loadbeta = False
        user_config.save_changes()


def _startuplogtimeout_config_upgrade(user_config):
    """ Upgrades local files and settings per this commit changes.
    commit message:   Updated settings window to allow adjusting
                      the startup window timeout
    commit hash:      75ffba6d19e98862a28d5d180345c124df696246
    """

    try:
        assert user_config.core.startuplogtimeout
    except:
        user_config.core.startuplogtimeout = 0
        user_config.save_changes()


def _disabe_legacy_revitpythonwrapper_extension():
    """ Disables the old revitpythonwrapper library extension
    RPW is now a builtin module in pyRevit
    """
    from pyrevit.plugins.extpackages import get_ext_package_by_name
    legacy_rpw_pkg = get_ext_package_by_name('RevitPythonWrapper')
    if legacy_rpw_pkg:
        legacy_rpw_pkg.disable_package()


def _rocketmode_config_upgrade(user_config):
    if not user_config.core.has_option('rocketmode'):
        user_config.core.rocketmode = False
        user_config.save_changes()

def _autoupdate_config_upgrade(user_config):
    if not user_config.core.has_option('autoupdate'):
        user_config.core.autoupdate = False
        user_config.save_changes()


def upgrade_user_config(user_config):
    _filelogging_config_upgrade(user_config)
    _loadbeta_config_upgrade(user_config)
    _startuplogtimeout_config_upgrade(user_config)
    _rocketmode_config_upgrade(user_config)
    _autoupdate_config_upgrade(user_config)


def upgrade_existing_pyrevit():
    _cleanup_cache_files()
    _disabe_legacy_revitpythonwrapper_extension()
