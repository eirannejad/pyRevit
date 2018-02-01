import pyrevit.coreutils.git as git
from pyrevit.compat import safe_strtype
from pyrevit.coreutils.logger import get_logger
from pyrevit.versionmgr import get_pyrevit_repo

from pyrevit.userconfig import user_config
from pyrevit.extensions.extensionmgr import get_installed_extension_data


logger = get_logger(__name__)


CORE_UPDATE_TRIGGER = 'COREUPDATE'


def _get_extension_credentials(repo_info):
    try:
        repo_config = user_config.get_section(repo_info.name)
        if repo_config.private_repo:
            return repo_config.username, repo_config.password
        return None, None
    except:
        return None, None


def _fetch_remote(remote, repo_info):
    logger.debug('Fetching remote: {} of {}'
                 .format(remote.Name, repo_info.directory))
    username, password = _get_extension_credentials(repo_info)
    if username and password:
        repo_info.username = username
        repo_info.password = password

    git.git_fetch(repo_info)


def get_thirdparty_ext_repos():
    # get a list of all directories that could include extensions
    extensions = []
    logger.debug('Finding installed repos...')
    ext_info_list = get_installed_extension_data()

    for ext_info in ext_info_list:
        if ext_info and git.libgit.Repository.IsValid(ext_info.directory):
            extensions.append(ext_info)

    logger.debug('Valid third-party extensions for update: {}'
                 .format(extensions))

    repos = []
    for ext in extensions:
        repo_info = git.get_repo(ext.directory)
        if repo_info:
            repos.append(repo_info)

    return repos


def get_all_extension_repos():
    logger.debug('Finding all extension repos.')
    # pyrevit main repo
    repo_info_list = [get_pyrevit_repo()]
    # add all thirdparty extension repos
    repo_info_list.extend(get_thirdparty_ext_repos())
    logger.debug('Repos are: {}'.format(repo_info_list))
    return repo_info_list


def update_pyrevit(repo_info):
    repo = repo_info.repo
    logger.debug('Updating repo: {}'.format(repo_info.directory))
    head_msg = safe_strtype(repo.Head.Tip.Message).replace('\n', '')
    logger.debug('Current head is: {} > {}'
                 .format(repo.Head.Tip.Id.Sha, head_msg))
    username, password = _get_extension_credentials(repo_info)
    if username and password:
        repo_info.username = username
        repo_info.password = password

    try:
        updated_repo_info = git.git_pull(repo_info)
        logger.debug('Successfully updated repo: {}'
                     .format(updated_repo_info.directory))
        return updated_repo_info

    except git.PyRevitGitAuthenticationError as auth_err:
        logger.debug('Can not login to git repository to get updates: {} | {}'
                     .format(repo_info, auth_err))
        raise auth_err

    except Exception as update_err:
        logger.debug('Failed updating repo: {} | {}'
                     .format(repo_info, update_err))
        raise update_err


def get_updates(repo_info):
    repo = repo_info.repo
    at_least_one_fetch_was_successful = False

    logger.debug('Fetching updates for: {}'.format(repo_info.directory))
    for remote in repo.Network.Remotes:
        try:
            _fetch_remote(remote, repo_info)
            at_least_one_fetch_was_successful = True

        except git.PyRevitGitAuthenticationError:
            logger.debug('Failed fetching updates. '
                         'Can not login to repo to get updates: {}'
                         .format(repo_info))
            continue

        except:
            logger.debug('Failed fetching updates: {}'.format(repo_info))
            continue

    if at_least_one_fetch_was_successful:
            return True

    return False


def has_pending_updates(repo_info):
    if get_updates(repo_info):
        hist_div = git.compare_branch_heads(repo_info)
        if hist_div.BehindBy > 0:
            return True


def has_core_updates():
    pyrevit_repo = get_pyrevit_repo()
    if get_updates(pyrevit_repo):
        new_commits = git.get_all_new_commits(pyrevit_repo)

        logger.debug('Checking new commits on pyrevit repo.')
        for cmt_sha, cmt_msg in new_commits.items():
            logger.debug('{}: {}'.format(cmt_sha, cmt_msg))
            if CORE_UPDATE_TRIGGER in cmt_msg:
                logger.debug('pyrevit repo has core update at {}: {}'
                             .format(cmt_sha, cmt_msg))
                return True

    return False
