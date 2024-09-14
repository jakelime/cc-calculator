import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from .config import ConfigManager
from .utils import LoggerManager, get_time, write_output_log_filepath

APP_NAME = "ccc"
lg = LoggerManager(APP_NAME).getLogger()
cfg = ConfigManager().config


@dataclass
class FileTableRow:
    filepath: Path
    filename: str = ""
    date_modified: pd.Timestamp = pd.Timestamp("NaT")

    def __post_init__(self):
        self.filename = self.filepath.name
        self.date_modified = pd.Timestamp(os.path.getmtime(self.filepath), unit="s")


class FileManager:
    def __init__(self, filepattern: str = "CC_TXN_History_*.xls") -> None:
        self.filepattern = filepattern

    def get_file(self) -> Path | None:
        fpath = self.get_file_from_downloads(filepattern=self.filepattern)
        if fpath is None:
            fpath = self.get_file_from_codebase(filepattern=self.filepattern)
        if fpath is None:
            raise FileNotFoundError(f"no files found; {self.filepattern=}")
        return fpath

    @staticmethod
    def get_file_from_downloads(
        dir_str="~/Downloads", filepattern: str = "CC_TXN_History_*.xls"
    ) -> Path | None:
        dirpath = Path(dir_str).expanduser()
        if not dirpath.is_dir():
            raise NotADirectoryError(f"invalid {dirpath=}")
        fpath_iter = dirpath.glob(filepattern)
        try:
            fpath = next(fpath_iter)
            return fpath
        except StopIteration:
            return None

    @staticmethod
    def get_file_from_codebase(
        filepattern: str = "CC_TXN_History_*.xls",
    ) -> Path | None:
        dirpath = Path(__file__).parent.parent
        fpath_iter = dirpath.glob(filepattern)
        try:
            fpath = next(fpath_iter)
            return fpath
        except StopIteration:
            return None

    def get_file_from_output(self):
        dirpath = Path(cfg["output_dir"]).expanduser()
        fpaths = [x for x in dirpath.glob(self.filepattern)]
        if not fpaths:
            raise FileNotFoundError(f"no files in output {dirpath}")
        fpaths = sorted(fpaths, key=lambda t: os.path.getmtime(t))
        return fpaths[-1]


class UobExcelReader:
    """Reads excel files from UOB credit card transactions"""

    def __init__(
        self,
        dt_format: str = "%d %b %Y",
        filepattern: str = "CC_TXN_History_*.xls",
    ):
        self.export_to_csv = cfg.get("export_to_csv", False)
        self.dt_format = dt_format
        self.filepattern = filepattern
        try:
            self.df = self.parse()
        except Exception:
            self.df = pd.DataFrame()

    def parse(
        self,
        fpath: Optional[Path] = None,
        filepattern: str = "",
        export: bool = False,
        cleanup: bool = True,
    ) -> pd.DataFrame:
        if not filepattern:
            filepattern = self.filepattern
        if fpath is None:
            fpath = FileManager(filepattern=filepattern).get_file()
        if fpath is None:
            raise FileNotFoundError(f"no files found; {filepattern=}")
        self.fpath = fpath
        df = self.parse_data(fpath)
        self.df = df
        if export:
            outpath = Path(cfg["folders"]["outf01"]) / f"{get_time()}.csv"
            df.to_csv(outpath)
            write_output_log_filepath(lg, outpath)
        if cleanup:
            self.perform_clean_up()
        return df

    def parse_data(self, filepath):
        lg.info(f"reading {filepath.name} ...")
        df = pd.read_excel(filepath, skiprows=list(np.arange(0, 9)), header=0)
        df = self.drop_na_with_threshold(df)
        col_headers = cfg["parser_settings"]["columns_mapper"]
        if col_headers:
            df = df.rename(col_headers, axis=1)

        df["item"] = df["description"].apply(lambda x: x.split("  ")[0])

        dflist = []
        for k, v in cfg["category_mapper"].items():
            df_ = df[df["item"].str.contains(k)].copy()
            df_["key_code"] = v
            dflist.append(df_)

        df = pd.concat([df] + dflist)
        df.drop_duplicates(subset=["description"], keep="last", inplace=True)
        df["key_code"] = df["key_code"].fillna(1)
        df["key_code"] = pd.to_numeric(
            df["key_code"], downcast="integer", errors="raise"
        )
        df["date_transacted"] = pd.to_datetime(
            df["date_transacted"], format=self.dt_format
        )

        qual_dict = {}
        for k, v in cfg["qualifications_table"].items():
            qual_dict[int(k)] = v

        df["qualified"] = df["key_code"].apply(lambda x: qual_dict[x])

        return df.sort_index()

    def drop_na_with_threshold(self, dfin):
        df = dfin[
            (dfin.isnull().sum(axis=1)) < cfg["parser_settings"]["drop_na_threshold"]
        ]
        return df

        df = dfin.copy()
        thresh = self.cfg["general"]["drop_na_threshold"]
        df = df[(df.isnull().sum(axis=1)) < thresh]
        return df

    def perform_clean_up(self):
        if not self.fpath.is_file():
            lg.warning("nothing to cleanup")
        dirpath = Path(cfg["output_dir"]).expanduser()
        outpath = dirpath / self.fpath.name
        if not dirpath.is_dir():
            dirpath.mkdir(exist_ok=True, parents=True)
            lg.warning(f"created {dirpath=}")

        shutil.copy(self.fpath, outpath)
        lg.debug(f"created copy in {outpath}")
        os.remove(self.fpath)
        lg.debug(f"created copy in {outpath}")
        lg.info(f"clean up completed - {self.fpath}")


def test_uob_excel_reader():
    pd.set_option("display.max_rows", 20)
    pd.set_option("display.max_columns", 15)
    pd.set_option("display.width", 1000)

    uob = UobExcelReader()


if __name__ == "__main__":
    test_uob_excel_reader()
