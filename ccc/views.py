import logging

import numpy as np
import pandas as pd

APP_NAME = "ccc"
try:
    from config import ConfigManager
    from models import UobExcelReader
    from utils import LoggerManager
except ImportError:
    from .utils import LoggerManager
    from .config import ConfigManager
    from .models import UobExcelReader

APP_NAME = "ccc"
lg = LoggerManager(APP_NAME).getLogger()
cfg = ConfigManager().config


class UobExcelViewer:
    """View UOB credit card transactions"""

    columns: list = ["date_transacted", "item", "amount", "key_code"]
    str_length: int = 84

    def __init__(self, model):
        self.model = model

    def make_text_centered(self, str_value) -> str:
        spaces1 = (self.str_length - (len(str_value) + 4)) // 2
        spaces2 = self.str_length - (len(str_value) + 4) - spaces1
        results = f"\n{'*'*spaces1}  {str_value}  {'*'*spaces2}\n"
        return results

    def display_data(self):
        lg.info(self.display_data_qualified())
        lg.info(self.display_data_from_category(3))
        lg.info(self.display_data_biggest())
        lg.info(self.display_data_from_category(2))
        lg.info(self.display_data_from_category(5))

    def display_data_from_category(self, category: int = 1):
        df = self.model.df.copy()
        df = df[df["key_code"] == category]
        total_amount = df["amount"].sum()
        df = df[self.columns]
        display_str = ""
        display_str += self.make_text_centered(f"{category=}")
        display_str += f"{df}\n"
        display_str += f"{'-'*self.str_length}\n"
        display_str += f"Subtotal = ${total_amount:.2f}\n"
        display_str += f"{'*'*self.str_length}\n"
        return display_str

    def display_data_qualified(self):
        df = self.model.df.copy()
        df = df[~df["item"].isin(cfg["exclusions"])]
        df = df[df["qualified"]]
        total_amount = df["amount"].sum()
        df = df[self.columns]
        display_str = ""
        display_str += self.make_text_centered("QUALIFIED")
        display_str += f"{df}\n"
        display_str += f"{'-'*self.str_length}\n"
        display_str += f"Subtotal = ${total_amount:.2f}\n"
        display_str += f"{'*'*self.str_length}\n"
        return display_str

    def display_data_biggest(self, title: str = "BIG PURCHASES"):
        df = self.model.df.copy()
        df = (
            df[df["amount"] > 0]
            .sort_values("amount", ascending=False)
            .head(cfg["number_of_top_big_purchases"])
        )
        total_amount = df["amount"].sum()
        df = df[self.columns]
        display_str = ""
        display_str += self.make_text_centered(title)
        display_str += f"{df}\n"
        display_str += f"{'-'*self.str_length}\n"
        display_str += f"Subtotal = ${total_amount:.2f}\n"
        display_str += f"{'*'*self.str_length}\n"
        return display_str


def test_uob_excel_viewer():
    pd.set_option("display.max_rows", 50)
    pd.set_option("display.max_columns", 15)
    pd.set_option("display.width", 1000)

    model = UobExcelReader()
    uob = UobExcelViewer(model)
    uob.display_data()


if __name__ == "__main__":
    test_uob_excel_viewer()
