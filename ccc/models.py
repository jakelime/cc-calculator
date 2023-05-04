from dataclasses import dataclass
from pathlib import Path

import logging
import time
import os

import pandas as pd
import numpy as np

APP_NAME = "ccc"
# local libraries
if __name__.startswith(APP_NAME):
    from .config import Config

else:
    from config import Config


@dataclass
class FileTableRow:
    filepath: Path
    filename: str = ""
    date_modified: pd.Timestamp = pd.Timestamp("NaT")

    def __post_init__(self):
        self.filename = self.filepath.name
        self.date_modified = pd.Timestamp(os.path.getmtime(self.filepath), unit="s")


class UobExcelReader:
    """Reads excel files from UOB credit card transactions"""

    input_folder: Path = None
    filetable: pd.DataFrame = pd.DataFrame()
    dt_format: str = "%d %b %Y"

    def __init__(self, cfg, input_folder: Path = None, mode: str = "single"):
        self.log = logging.getLogger(APP_NAME)
        log = self.log
        self.cfg = cfg
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

    def get_filetable(self, folderpath=Path, glob_wildcard="*.xls"):
        filelist = folderpath.glob(glob_wildcard)
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

        df = pd.read_excel(filepath, skiprows=np.arange(0, 9), header=0)
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

        df["date_transacted"] = pd.to_datetime(df["date_transacted"],format=self.dt_format)

        qual_dict = {}
        for k,v in cfg["int_keys_to_qualification"].items():
            qual_dict[int(k)] = v

        df["qualified"] = df["key_code"].apply(
            lambda x: qual_dict[x]
        )
        return df.sort_index()

    def drop_na_with_threshold(self, dfin):
        df = dfin.copy()
        thresh = self.cfg["general"]["drop_na_threshold"]
        df = df[(df.isnull().sum(axis=1)) < thresh]
        return df

    def display_data(self, keys=["1", "2", "0"]):
        try:
            log, cfg = self.log, self.cfg
            dfin = self.df_raw.copy()
            cols = list(dfin.columns)
            cols_selected = [col for col in cols if col in cfg["display_columns"]]
            ## rearrange columns according to user configuration
            cols_selected = [
                col for col in cfg["display_columns"] if col in cols_selected
            ]
            critical_params = ["key_code", "tier1_qualified"]
            for param in critical_params:
                if param not in cols_selected:
                    cols_selected.append(param)
            assert cols_selected, f"the columns selection are invalid!"
            if len(cols_selected) < len(cfg["display_columns"]):
                log.warning(f"some of the column keys are invalid!")
                [log.warning(col) for col in cfg["display_columns"] if col not in cols]
            dfin = dfin[cols_selected]

            df = dfin[dfin["qualified"] == True]
            cols = list(df.columns)
            cols = [col for col in cols if "tier1_qualified" not in col]
            log.info(
                f"\n##########################################################################################\
                \nQualified amount for Tier1 = ${df['amount_sgd'].sum():.2f}"
            )
            log.info(f"\n{df[cols]}")

            for k in keys:
                df = dfin[dfin["key_code"] == k]
                cols = list(df.columns)
                cols = [col for col in cols if "tier1_qualified" not in col]
                totalsum = df["amount_sgd"].sum()

                if k == "3" and totalsum > 7:
                    log.info(
                        f"\
                    \n##########################################################################################\
                    \n##################################!!!!!!!!!!!!!!!!!!!!####################################\
                    \n##################################!!!!!!!!APPLE!!!!!!!####################################\
                    \n##################################!!!!!!!!!!!!!!!!!!!!####################################\
                    \n##########################################################################################"
                    )

                else:
                    pass

                log.info(
                    f"\n##########################################################################################\
                    \nkey_code=={k}, total amount = ${totalsum:.2f}"
                )
                log.info(f"\n{df[cols]}")

        except Exception as e:
            raise Exception(f"{inspect.currentframe().f_code.co_name}();{e}")

    def debug_print(self, df):
        df_ = df[["date_transacted", "item", "amount", "qualified", "key_code"]]
        self.log.info(f"df_:\n{df_}")


def test_uob_excel_reader(cfg):
    pd.set_option("display.max_rows", 20)
    pd.set_option("display.max_columns", 15)
    pd.set_option("display.width", 1000)

    uob = UobExcelReader(cfg)


if __name__ == "__main__":

    cfg = Config(hard_reset=True).cfg
    test_uob_excel_reader(cfg)
