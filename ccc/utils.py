import logging
import os
import platform
import re
import shutil
import subprocess
import time
import unicodedata
from logging.handlers import RotatingFileHandler
from pathlib import Path

APP_NAME = "ccc"


class LoggerManager:
    def __init__(
        self,
        app_name: str = "",
        logfile_backupCount: int = 5,
        logfile_maxBytes: int = 2_097_152,
        default_level=logging.INFO,
        debug_mode: bool = False,
    ):
        if not app_name:
            app_name = __name__
        self.default_level = default_level
        if debug_mode:
            self.default_level = logging.DEBUG
        self.logfile_backupCount = logfile_backupCount
        self.logfile_maxBytes = logfile_maxBytes
        self.app_name = app_name
        self.logger_name = app_name
        self.logger = logging.getLogger(self.app_name)
        if not self.logger.handlers:
            # Set ups the logger if it is not already initialised
            self.init_logger(self.logger)

    def init_logger(self, logger):
        logger_filepath = self.set_log_filepath()
        logger.setLevel(self.default_level)
        formatter = logging.Formatter("%(asctime)s-%(levelname)s: %(message)s")
        fhandler = RotatingFileHandler(
            filename=logger_filepath,
            maxBytes=self.logfile_maxBytes,
            backupCount=self.logfile_backupCount,
        )
        fhandler.setFormatter(formatter)
        fhandler.setLevel(self.default_level)
        chandler = logging.StreamHandler()
        chandler.setLevel(self.default_level)
        chandler.setFormatter(formatter)
        logger.addHandler(fhandler)
        logger.addHandler(chandler)
        logger.info(f"logger initialised - {logger_filepath}")
        return logger

    def get_logger(self):
        return self.logger

    def getLogger(self):
        return self.logger

    def setLevel(self, level: str = "info"):
        match level.lower():
            case "info":
                for h in self.logger.handlers:
                    h.setLevel("INFO")
            case "debug":
                for h in self.logger.handlers:
                    h.setLevel("DEBUG")
            case "warning" | "warn":
                for h in self.logger.handlers:
                    h.setLevel("WARNING")
            case "error":
                for h in self.logger.handlers:
                    h.setLevel("ERROR")
            case _:
                raise RuntimeError(f"unknown log {level=}")
        self.logger.critical(f"logger level changed to {level}")

    def change_level(self, level: str = "info"):
        self.setLevel(level)

    def set_level(self, level: str = "info"):
        self.setLevel(level)

    def set_log_filepath(self, dirpath: str = "~/Library/Logs") -> Path:
        logs_dirpath = Path(dirpath).expanduser()
        if not os.access(logs_dirpath, os.W_OK):
            raise OSError(f"logs directory is not writeable - {dirpath=}")
        logger_filepath = logs_dirpath / self.app_name / "main_application.log"
        if not logger_filepath.parent.is_dir():
            logger_filepath.parent.mkdir()
        self.logger_filepath = logger_filepath
        return logger_filepath


class ConfigError(Exception):
    """Error due to invalid parameters in user config file"""


class QueueHandler(logging.Handler):
    """
    Class to send logging records to a queue
    It can be used from different threads
    The ConsoleUi class polls this queue to display records in a ScrolledText widget

    Example from Moshe Kaplan: https://gist.github.com/moshekaplan/c425f861de7bbf28ef06
    (https://stackoverflow.com/questions/13318742/python-logging-to-tkinter-text-widget) is not thread safe!
    See https://stackoverflow.com/questions/43909849/tkinter-python-crashes-on-new-thread-trying-to-log-on-main-thread
    """

    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)


def copyfile(src: Path, dst: Path, overwrite=False):
    """
    Wrapper to copy a file src to dst
    Exceptions will be caught and logged, without breaking the code
    """
    log = LoggerManager(APP_NAME).getLogger()

    if dst.is_file() and not overwrite:
        log.debug(f"already exist, skipping ../{dst.name}")
        return

    try:
        shutil.copyfile(src, dst)
        log.debug(f"copied src to //{dst.parent.name}/{dst.name}")

    except OSError:
        log.error(f"OSError: no permissions to src=//{dst.parent.name}")

    except Exception as e:
        log.error(f"copying file error; {e}")


def get_time(datetimestrformat: str = "%Y%m%d_%H%M%S"):
    """
    Returns the datetime string at the time of function call
    :param datetimestrformat: datetime string format, defaults to "%Y%m%d_%H%M%S"
    :type datetimestrformat: str, optional
    :return: datetime in string format
    :rtype: str
    """
    return time.strftime(datetimestrformat, time.localtime(time.time()))


def classtimer(func):
    def wrapper(ref_self, *args, **kwargs):
        log = LoggerManager(APP_NAME).getLogger()
        t0 = time.perf_counter()
        a = func(ref_self, *args, **kwargs)
        time_taken = time.perf_counter() - t0
        if time_taken < 100:
            time_taken = f"{time_taken:.4f}s"
        else:
            time_taken = f"{(time_taken/60):.2f}mins"
        log.info(f"[{func.__name__}] elapsed_time = {time_taken}")
        return a

    return wrapper


def timer(func):
    def wrapper(*args, **kwargs):
        log = LoggerManager(APP_NAME).getLogger()
        t0 = time.perf_counter()
        a = func(*args, **kwargs)
        log.info(f"[{func.__name__}] elapsed_time = {(time.perf_counter()-t0):.4f}s")
        return a

    return wrapper


def get_latest_git_tag(repo_path: Path = None, err_code: str = "versionError"):
    """function to use GitPython to get a list of tags

    :param repo_path: path where .git resides in
    :type repo_path: pathlib.Path
    :return: latest git tag
    :rtype: str
    """
    try:
        sp = subprocess.run(
            ["git", "describe", "--tag"],
            check=True,
            timeout=5,
            capture_output=True,
            encoding="utf-8",
        )
        results = sp.stdout.strip()

        if not results:
            results = err_code

    except subprocess.CalledProcessError as e:
        if e.returncode == 128:
            results = "git_fatal_err"
        else:
            results = f"{e=}"

    except Exception as e:
        results = f"{e=}"

    finally:
        return results


def open_folder(path):
    log = LoggerManager(APP_NAME).getLogger()
    path = Path(path)
    if path.is_dir():
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    else:
        raise Exception(f"invalid {path=}")
    log.info(f"Open folder success //{path.name}")


def write_version_file(
    parent_dir: Path,
    filename: str = "version.txt",
    version: str = "versionErr",
):
    log = LoggerManager(APP_NAME).getLogger()
    version_file = parent_dir / filename
    try:
        with open(version_file, "w") as fm:
            fm.write(version)
        log.info(f"version updated to {version}")
        return True
    except IOError:
        log.error("IOError: software version update failed")
    finally:
        return False


def copy_version_to_userConfigFolder(
    srcDir: Path, dstDir: Path, filename: str = "version.txt"
):
    src = srcDir / filename
    dst = dstDir / filename
    try:
        shutil.copy2(src, dst)
    except FileNotFoundError:
        raise FileNotFoundError(f"Copy src=~/{srcDir.name}/{filename}")
    except PermissionError:
        raise PermissionError(f"Copy dst=~/{dst.parent}/{dst.name}")
    except Exception as e:
        raise e


def get_version(version_file: Path):
    try:
        with open(version_file, "r") as fm:
            version = fm.readline()
        return version
    except IOError:
        log = LoggerManager(APP_NAME).getLogger()
        log.warning(f"{version_file=}")
        log.error(f"IOError: unable to access {version_file=}")
        return "versionErr"


def rmtree(path_to_clear: Path):
    try:
        log = LoggerManager(APP_NAME).getLogger()
        if not isinstance(path_to_clear, Path):
            path = Path(path_to_clear)
        else:
            path = path_to_clear
        if not path.is_dir():
            return None

        for fp in path.rglob("*"):
            log.info(f"removing //{fp.parent.name}/{fp.name}")
            try:
                os.remove(fp)
            except Exception as e:
                if fp.is_dir():
                    continue
                else:
                    log.warning(f"failed to remove!, {e=}")

        for fp in path.rglob("*"):
            os.rmdir(fp)
        os.rmdir(path)
        # shutil.rmtree(path=path_to_clear)
        path.mkdir(parents=True, exist_ok=True)
        log.info(f"deleted //{path.parent.name}/{path.name}/*.*")
        return path
    except Exception as e:
        raise e


def factory_reset(app_name: str) -> int:
    log = LoggerManager(APP_NAME).getLogger()
    user_docs = Path(os.path.expanduser("~/Documents/"))
    working_dir = user_docs / f"_tools-{app_name}"
    counter = 0
    if not working_dir.is_dir():
        log.error(f"nothing to reset. {working_dir=}")
        return 1

    src_dir = working_dir
    dst_dir = user_docs / f"_tools-{app_name}_backup_{get_time()}"
    try:
        shutil.copytree(src=src_dir, dst=dst_dir)
        log.info(f"backup done //{dst_dir.parent.name}/{dst_dir.name}")
    except Exception as e:
        log.error(f"backup failed; {e=}")

    try:
        if platform.system().lower() == "windows":
            log.info(f"system OS = {platform.system()}")
            log.warning("logger will shut down during factory reset")
            for handler in log.handlers:
                if "FileHandler" in str(handler.__class__):
                    log.info(f"shutting down {handler.__class__}")
                    handler.close()
                    log.removeHandler(handler)
                    counter += 1

        shutil.rmtree(path=src_dir)
        log.info(f"rmdir done //{src_dir.parent.name}/{src_dir.name}")

    except Exception as e:
        log.error(f"rmdir failed; {e=}")
        return 2

    if counter > 0:
        if log is None:
            print("RESTARTING APP IS COMPULSORY")
            print("Please restart this app to complete factory reset!")
        else:
            log.error("RESTARTING APP IS COMPULSORY")
            log.warning("Please restart this app to complete factory reset!")
        return 3

    if log is None:
        print("reset completed successfully")
    else:
        log.error("reset completed successfully")
    return 0


def get_file(
    folderpath_str: str,
    wildcard_str: str,
    default_index: None | int = -1,
    recursive: bool = True,
):
    """Get file(s) from a given folder, using the given wildcard

    :param folderpath_str: folderpath in string format
    :type folderpath_str: str
    :param wildcard_str: wildcard
    :type wildcard_str: str
    :param default_index: {None: returns all files in a list, 0: returns oldest modified file, -1: returns latest modified file}, defaults to -1
    :type default_index: None | int
    :raises NotADirectoryError: if folderpath_str is nto a valid directory
    :raises FileNotFoundError: no files found
    :return: list of Path objects or Path, depending on default_index
    :rtype: list[Path] or Path
    """

    log = LoggerManager(APP_NAME).getLogger()
    folderpath = Path(folderpath_str)
    if not folderpath.is_dir():
        raise NotADirectoryError(f"{folderpath}=")
    if recursive:
        files = [f for f in folderpath.rglob(wildcard_str)]
    else:
        files = [f for f in folderpath.glob(wildcard_str)]
    if not files:
        raise FileNotFoundError(f"{wildcard_str=}; {folderpath=}")
    # files = sorted(files)
    files = sorted(files, key=lambda fp: os.stat(fp).st_mtime)
    if default_index is None:
        return files
    elif len(files) > 1:
        log.debug(f"multiple files found, selected #{default_index}")
        filepath = files[default_index]
    else:
        filepath = files[0]
    return filepath


def convert_legal_filename(value, allow_unicode=False):
    """
    Adapted from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Also strip leading and
    trailing whitespace, dashes, and underscores. Strips all dashes.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = (
            unicodedata.normalize("NFKD", value)
            .encode("ascii", "ignore")
            .decode("ascii")
        )
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[-\s]+", "-", value).strip("-_")
    value = value.replace("-", "")
    return value


def get_logger_level_bool(level: int = 10):
    logger = LoggerManager(APP_NAME).getLogger()
    return logger.getEffectiveLevel() <= level


def write_output_log_filepath(
    log, outpath, txtstr="saved", level="INFO", prefix: str = ""
):
    ostr = f"{prefix}{txtstr} //{outpath.parent.name}/{outpath.name}"
    match level.upper():
        case "INFO":
            log.info(ostr)
        case "DEBUG":
            log.debug(ostr)
        case "CRITICAL":
            log.critical(ostr)
        case "WARNING":
            log.warning(ostr)
        case _:
            print(ostr)


def check_write_permission(directory_path):
    if not os.access(directory_path, os.W_OK):
        raise OSError(f"directory is not writeable - {directory_path=}")


if __name__ == "__main__":
    # print(get_latest_git_tag(repo_path=Path(__file__).parent.parent))
    # logger = setup_basic_logger()
    factory_reset(app_name=APP_NAME)
