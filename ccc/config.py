# config.py
# Responsible for initializing configuration needed
# for the application. There are 2 configurations here:
# factory configuration and user configuration.

# global libraries
import os
import tomlkit
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from dotenv import load_dotenv


APP_NAME = "ccc"
# local libraries
if __name__.startswith(APP_NAME):
    from .utils import copyfile, ConfigError
else:
    from utils import copyfile, ConfigError


class Config:
    """
    This class is responsible intialising a logger object (to log messages)
    and initialising a tomlDocument object to be used as user configuration

    self.log = logging.Logger object
    self.cfg = tomlDocument object (similar to dict)
    """

    cfg: dict = None
    factory_bundles: Path = None
    factory_filename: str = "config.toml"
    user_bundles: Path = None
    user_wd: Path = None
    log: logging.Logger = None

    def __init__(
        self,
        hard_reset=False,
    ) -> None:
        load_dotenv()
        self.hard_reset = hard_reset
        self.factory_bundles = Path(__file__).parent.parent / "bundles"
        self.factory_filepath = self.factory_bundles / self.factory_filename

        self.user_wd = Path(os.path.expanduser("~/Documents/")) / f"_tools-{APP_NAME}"
        self.user_bundles = self.user_wd / "bundles"
        self.user_filepath = self.user_bundles / self.factory_filename
        self.logfile = self.user_wd / f"{APP_NAME}.log"
        self.log = self.setup_logger(self.logfile)

        if self.user_filepath.is_file() and not self.hard_reset:
            self.cfg = self.load_toml(self.user_filepath)
        else:
            self.cfg = self.load_toml()
        self.init_user_paths(self.hard_reset)
        self.cfg = self.post_init_keys(self.cfg)
        if self.hard_reset:
            self.log.warning("hard reset completed.")

    def setup_logger(self, log_filepath: Path = None, default_loglevel="INFO"):
        """
        Creates a logger object
        Logs to both console stdout and also a log file
        """

        logger = logging.getLogger(APP_NAME)
        if logger.hasHandlers():
            return logger

        if log_filepath is None:
            log_filepath = os.path.expanduser("~/Documents/") / "unnamed.log"

        if not log_filepath.is_file():
            log_filepath.parent.mkdir(parents=True, exist_ok=True)
            with log_filepath.open("w", encoding="utf-8") as f:
                f.write("")

        # Create handlers
        c_handler = logging.StreamHandler()
        f_handler = RotatingFileHandler(
            self.logfile, maxBytes=5_242_880, backupCount=10
        )
        c_handler.setLevel(default_loglevel)
        f_handler.setLevel(default_loglevel)

        # Create formatters and add it to handlers
        c_format = logging.Formatter("%(levelname)-8s: %(message)s")
        f_format = logging.Formatter(
            "[%(asctime)s]%(levelname)-8s: %(message)s", "%y-%j %H:%M:%S"
        )
        c_handler.setFormatter(c_format)
        f_handler.setFormatter(f_format)

        # Add handlers to the logger
        logger.addHandler(c_handler)
        logger.addHandler(f_handler)
        logger.setLevel(default_loglevel)
        logger.info("logger initialized")
        return logger

    def load_toml(self, custom_filepath: Path = None) -> object:
        filepath = self.factory_filepath
        if custom_filepath is not None:
            filepath = custom_filepath

        with open(filepath, mode="rt", encoding="utf-8") as fp:
            self.cfg = tomlkit.load(fp)
            self.log.debug(
                f"cfg loaded from //{filepath.parent.parent.name}/{filepath.parent.name}/{filepath.name}"
            )
        return self.cfg

    def write_toml(self, target_fp: object) -> None:
        if self.cfg is None:
            raise ConfigError("unable to write. empty cfg.")
        if not isinstance(target_fp, Path):
            target_fp = Path(target_fp)
        with open(target_fp, mode="wt", encoding="utf-8") as fp:
            tomlkit.dump(self.cfg, fp)
        target_fp = target_fp.resolve()
        msg = f"configuration file written //{target_fp.parent.name}/{target_fp.name}"
        if self.log:
            self.log.info(msg)
        else:
            print(msg)

    def init_user_paths(self, hard_reset=False):
        """Initialize the user working directory"""
        # Copies all bundled files, except for .py or keys
        if not self.user_bundles.is_dir():
            self.user_bundles.mkdir(parents=True, exist_ok=True)
        for fp in self.factory_bundles.glob("*.*"):
            if fp.suffix in [".py", ".key"]:
                continue
            copyfile(src=fp, dst=self.user_bundles / fp.name, overwrite=hard_reset)

    def post_init_keys(self, cfg_input: dict):
        cfg = cfg_input.copy()
        cfg["folders"] = {}
        cfg["folders"]["user_config_folder"] = str(self.user_bundles.resolve())
        cfg["folders"]["user_working_folder"] = str(self.user_wd.resolve())
        return cfg


def pretty_print(d, n: int = 0):
    log = logging.getLogger(APP_NAME)
    spaces = " " * n * 2
    for k, v in d.items():
        if isinstance(v, dict):
            log.info(f"{spaces}{k}:")
            pretty_print(v, n=n + 1)
        else:
            try:
                log.info(f"{spaces}{k}: {v}")
            except AttributeError:
                # Happens when parsing toml (below is to handle tomlkit class)
                log.info(f"{spaces}{k=}, {v=}")


def test_read_config():
    cfg = Config(hard_reset=True).cfg
    pretty_print(cfg)
    # print(cfg['int_keys_to_qualification'])


if __name__ == "__main__":
    test_read_config()
