import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

try:
    from .config import ConfigManager
    from .utils import LoggerManager, get_time, write_output_log_filepath
except ImportError:
    from config import ConfigManager
    from utils import LoggerManager, get_time, write_output_log_filepath


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
        self.df = self.parse()

    def parse(self, filepattern: str = "", export: bool = False) -> pd.DataFrame:
        if not filepattern:
            filepattern = self.filepattern
        fpath = FileManager(filepattern).get_file()
        if fpath is None:
            raise FileNotFoundError(f"no files found; {filepattern=}")
        df = self.parse_data(fpath)
        if export:
            outpath = Path(cfg["folders"]["outf01"]) / f"{get_time()}.csv"
            df.to_csv(outpath)
            write_output_log_filepath(lg, outpath)
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


class UobExcelReaderOld:
    """Reads excel files from UOB credit card transactions"""

    input_folder: Optional[Path] = None
    filetable: pd.DataFrame = pd.DataFrame()
    dt_format: str = "%d %b %Y"

    def __init__(
        self,
        cfg,
        input_folder: Optional[Path] = None,
        mode: str = "single",
        export_to_csv: bool = False,
    ):
        log = self.log
        self.cfg = cfg
        self.export_to_csv = (
            cfg["export_to_csv"] if export_to_csv is None else export_to_csv
        )

        if not input_folder:
            self.filetable = self.get_filetable(Path(__file__).parent.parent)
        else:
            self.filetable = self.get_filetable(input_folder)

        match mode.lower():
            case "single":
                log.info(f"running single file read mode ...")
                ft = self.filetable
                self.df = self.get_data(ft.loc[ft.index[-1], "filepath"])
            case "multiple":
                dfs = [self.get_data(fp) for fp in self.filetable["filepath"]]
                self.df = pd.concat(dfs)
            case _:
                raise NotImplementedError(f"{mode=}")

    def get_filetable(self, folderpath=Path, glob_wildcard="*.xls") -> pd.DataFrame:
        filelist = [x for x in folderpath.glob(glob_wildcard)]
        if not filelist:
            raise RuntimeError(f"no files found; {folderpath=} {glob_wildcard=}")
        data = [FileTableRow(fp) for fp in filelist]
        df = pd.DataFrame(data)
        df = df.sort_values("date_modified").reset_index(drop=True)
        return df

    def get_data(self, filepath):
        log = self.log
        cfg = self.cfg
        log.info(f"reading {filepath.name} ...")

        df = pd.read_excel(filepath, skiprows=list(np.arange(0, 9)), header=0)
        df = self.drop_na_with_threshold(df)
        df = df.rename(self.cfg["column_headers"], axis=1)

        df["item"] = df["description"].apply(lambda x: x.split("  ")[0])

        dflist = []
        for k, v in cfg["category_to_int_keys"].items():
            df_ = df[df["item"].str.contains(k)].copy()
            df_["key_code"] = v
            dflist.append(df_)

        df = pd.concat([df] + dflist)
        df.drop_duplicates(subset=["description"], keep="last", inplace=True)
        df["key_code"].fillna(1, inplace=True)
        df["key_code"] = pd.to_numeric(
            df["key_code"], downcast="integer", errors="raise"
        )

        df["date_transacted"] = pd.to_datetime(
            df["date_transacted"], format=self.dt_format
        )

        qual_dict = {}
        for k, v in cfg["int_keys_to_qualification"].items():
            qual_dict[int(k)] = v

        df["qualified"] = df["key_code"].apply(lambda x: qual_dict[x])

        if self.export_to_csv:
            outpath = Path(cfg["folders"]["outf01"]) / f"{get_time()}.csv"
            df.to_csv(outpath)
            logOutput(outpath)

        return df.sort_index()

    def drop_na_with_threshold(self, dfin):
        df = dfin.copy()
        thresh = self.cfg["general"]["drop_na_threshold"]
        df = df[(df.isnull().sum(axis=1)) < thresh]
        return df


def test_uob_excel_reader():
    pd.set_option("display.max_rows", 20)
    pd.set_option("display.max_columns", 15)
    pd.set_option("display.width", 1000)

    uob = UobExcelReader()
    # uob.parse()
    lg.info("hello world!")


if __name__ == "__main__":
    test_uob_excel_reader()
