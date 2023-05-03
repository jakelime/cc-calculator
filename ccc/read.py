import pandas as pd
import logging
import time
import os
import inspect
import collections
import glob
import config as cs


class CCStatementReader:
    """docstring for CCStatementReader"""

    def __init__(self, log, cfg):
        self.log, self.cfg = log, cfg
        self.filetable = self.get_filetable()
        ft = self.filetable
        self.filepath = ft.loc[ft.index[-1], "filename"]
        if len(self.filetable) != 1:
            log.warning(
                f"multiple files detected; processing latest file: {os.path.split(self.filepath)[-1]}"
            )
        self.df_raw = self.get_data(self.filepath)

    def get_filetable(self):
        try:
            FILETABLE = collections.namedtuple(
                "FileTable", "filename filepath datemodified"
            )
            filelist = glob.glob(os.path.join(os.getcwd(), "*.xls"))
            if not filelist:
                raise Exception(f"no files found.")
            # fpathlist=sorted(fpathlist, key=lambda t: os.path.getmtime(t))
            logging.info(f"found: x{len(filelist)} files")
            filetable_list = []
            for filepath in filelist:
                _, filename = os.path.split(filepath)
                datemodified = os.path.getmtime(filepath)
                filetable_list.append(FILETABLE(filename, filepath, datemodified))
            ft = pd.DataFrame(filetable_list)
            ft = ft.sort_values("datemodified").reset_index(drop=True)
            return ft
        except Exception as e:
            raise Exception(f"{inspect.currentframe().f_code.co_name}();{e}")

    def get_data(self, filepath):
        try:
            cfg = self.cfg
            df = pd.read_excel(filepath, skiprows=[0, 1, 2, 3, 4, 5, 6, 7, 8], header=0)
            df["short_description"] = df["Description"].apply(
                lambda x: x.split("  ")[0]
            )

            dflist = []
            for k,v  in cfg["category_to_keys"].items():
                df_ = df[df["Description"].str.contains(k)].copy()
                df_["key_code"] = v
                dflist.append(df_)

            df = pd.concat([df]+dflist)
            df.drop_duplicates(subset=['Description'],keep='last', inplace=True)
            df["key_code" ].fillna('1', inplace=True)
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


def cf_setup_logger(name, default_level=logging.INFO):
    print(f".initialising logging ..")
    consoleFormatter = logging.Formatter("%(name)s: %(message)s")
    logging.basicConfig(
        filename="defaultlog.txt",
        level=default_level,
        format="[%(asctime)s]%(name)s;%(levelname)s;%(filename)s;%(funcName)s(): %(message)s",
    )
    console = logging.StreamHandler()
    console.setLevel(default_level)
    console.setFormatter(consoleFormatter)
    logging.getLogger("").addHandler(console)
    logger = logging.getLogger(name)
    logging.info(f" >>logger loaded.")
    return logger


def sf_replace_keys(cfg, v):
    try:
        changekey = cfg["category_to_keys"]
        if v in changekey.keys():
            return changekey[v]
        else:
            return v
    except Exception as e:
        raise e


def main():
    try:
        log = cf_setup_logger(__name__)
        cfg = cs.cfg
        card = CCStatementReader(log, cfg)
        card.display_data(keys=["3", "4", "1", "2", "0"])
        # card.display_data(keys=["1"])
    except Exception as e:
        log.error(f"{inspect.currentframe().f_code.co_name}();{e}")


if __name__ == "__main__":
    pd.set_option("display.max_rows", 500)
    pd.set_option("display.max_columns", 500)
    pd.set_option("display.width", 1000)
    time_1load = time.strftime("%d%b%y:%H%MH", time.localtime())

    main()
