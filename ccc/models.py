from dataclasses import dataclass
from pathlib import Path

import logging
import time
import os

import pandas as pd

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


class UOB_ExcelReader:
    """Reads excel files from UOB credit card transactions"""
    input_folder: Path = None
    filetable: pd.DataFrame = pd.DataFrame()

    def __init__(self, cfg, input_folder: Path = None, mode: str="read_single_file"):
        self.log = logging.getLogger(APP_NAME)
        self.cfg = cfg
        if not input_folder:
            self.filetable = self.get_filetable(Path(__file__).parent.parent)
        else:
            self.filetable = self.get_filetable(input_folder)

        if mode not in
        # ft = self.filetable
        # self.filepath = ft.loc[ft.index[-1], "filename"]
        # if len(self.filetable) != 1:
        #     log.warning(
        #         f"multiple files detected; processing latest file: {os.path.split(self.filepath)[-1]}"
        #     )
        # self.df_raw = self.get_data(self.filepath)

    def get_filetable(self, folderpath=Path, glob_wildcard="*.xls"):
        filelist = folderpath.glob(glob_wildcard)
        if not filelist:
            raise RuntimeError(f"no files found; {folderpath=} {glob_wildcard=}")
        data = [FileTableRow(fp) for fp in filelist]
        df = pd.DataFrame(data)
        df = df.sort_values("date_modified").reset_index(drop=True)
        return df


    def get_data(self, filepath):
        try:
            cfg = self.cfg
            df = pd.read_excel(filepath, skiprows=[0, 1, 2, 3, 4, 5, 6, 7, 8], header=0)
            df["short_description"] = df["Description"].apply(
                lambda x: x.split("  ")[0]
            )

            dflist = []
            for k, v in cfg["category_to_keys"].items():
                df_ = df[df["Description"].str.contains(k)].copy()
                df_["key_code"] = v
                dflist.append(df_)

            df = pd.concat([df] + dflist)
            df.drop_duplicates(subset=["Description"], keep="last", inplace=True)
            df["key_code"].fillna("1", inplace=True)
            # print(df)
            # df = df.reset_index().drop_duplicates(keep='last')
            # df["key_code" ].fillna('1', inplace=True)
            # df["key_code"] = df["key_code"].apply(
            #     lambda x: "1" if x not in cfg["category_to_keys"].values() else x
            # )
            df["amount_sgd"] = df["Transaction Amount(Local)"]
            df["date_transacted"] = pd.to_datetime(df["Transaction Date"])
            df["posting_status"] = df["Posting Date"].apply(
                lambda x: "PENDING" if (x == "PENDING") else "ok"
            )

            df["tier1_qualified"] = df["key_code"].apply(
                lambda x: cfg["keys_to_qualification"][x]
            )
            return df
        except Exception as e:
            raise Exception(f"{inspect.currentframe().f_code.co_name}();{e}")

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

            df = dfin[dfin["tier1_qualified"] == True]
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


def test_uob_excel_reader(cfg):

    uob = UOB_ExcelReader(cfg)


if __name__ == "__main__":
    pd.set_option("display.max_rows", 500)
    pd.set_option("display.max_columns", 500)
    pd.set_option("display.width", 1000)
    time_1load = time.strftime("%d%b%y:%H%MH", time.localtime())

    cfg = Config(hard_reset=True).cfg
    test_uob_excel_reader(cfg)
