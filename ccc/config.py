from pathlib import Path

import tomlkit as tmk
import utils
from tomlkit import toml_file
from tomlkit.toml_document import TOMLDocument

APP_NAME = "ccc"


class ConfigManager:
    def __init__(self, dirpath: str = "~/Library/Preferences") -> None:
        self.app_name = APP_NAME
        self.dirpath = dirpath
        self.config_filepath = self.get_config_filepath()
        if not self.config_filepath.is_file():
            self.write_toml_file(self.config_filepath)
        self.config = self.parse_config(self.config_filepath)

    def get_config_dirpath(self) -> Path:
        dirpath = Path(self.dirpath).expanduser()
        utils.check_write_permission(dirpath)
        dirpath = Path(self.dirpath).expanduser() / self.app_name
        if not dirpath.is_dir():
            dirpath.mkdir()
        return dirpath

    def get_config_filepath(self, filename: str = "config.toml") -> Path:
        config_filepath = self.get_config_dirpath() / filename
        return config_filepath

    @staticmethod
    def write_toml_file(outpath: Path) -> None:
        toml_doc = ConfigToml(outpath)
        toml_doc.write_to_file()

    @staticmethod
    def parse_config(fpath) -> dict:
        tf = toml_file.TOMLFile(fpath)
        doc = tf.read()
        config = doc.unwrap()
        return config

    def reset(self) -> None:
        """
        Resets the configuration file by writing a new TOML file and parsing it.

        This function writes a new TOML file to the configured filepath using the `write_toml_file` method.
        It then parses the newly written TOML file using the `parse_config` method and updates the `config` attribute
        with the parsed configuration.

        Parameters:
            None

        Returns:
            None
        """
        self.write_toml_file(self.config_filepath)
        self.config = self.parse_config(self.config_filepath)


class ConfigToml:
    def __init__(self, config_filepath: Path) -> None:
        self.config_filepath = config_filepath
        self.doc = self.init_doc()

    def write_to_file(self) -> Path:
        tf = toml_file.TOMLFile(self.config_filepath)
        tf.write(self.doc)
        print(f"wrote config to {self.config_filepath}")
        return self.config_filepath

    def init_doc(self) -> TOMLDocument:
        doc = tmk.document()
        doc.add(tmk.comment("Configuration file for CreditCardCompiler"))
        doc.add(tmk.nl())

        doc["display_columns"] = [
            "date_transacted",
            "posting_status",
            "key_code",
            "tier1_qualified",
            "short_description",
            "amount_sgd",
        ]
        doc["number_of_top_big_purchases"] = 20
        doc["export_to_csv"] = False
        doc["exclusions"] = ["GIRO PAYMENT"]

        parser = tmk.table()
        doc["parser_settings"] = parser
        parser["strftime"] = "%d%b%y:%H%MH"
        parser["drop_na_threshold"] = 5
        parser["output_dir"] = "~/Documents/ccc-parser/output"

        colm = tmk.table()
        parser["columns_mapper"] = colm
        colm["Transaction Date"] = "date_transacted"
        colm["Posting Date"] = "date_posted"
        colm["Description"] = "description"
        colm["Foreign Currency Type"] = "currency_foreign"
        colm["Transaction Amount(Foreign)"] = "amount_foreign"
        colm["Local Currency Type"] = "currency"
        colm["Transaction Amount(Local)"] = "amount"

        # [category_to_int_keys]
        cat = tmk.table()
        doc["category_mapper"] = cat
        cat["BUS/MRT"] = 2
        cat["SERAYA"] = 0
        cat["GRAB"] = 0
        cat["GRAB"].comment("# Grab wallet top up are not qualified")
        cat["NUHMC-PHARMACY"] = 0
        cat["NUH"] = 0
        cat["NUH"].comment("# Medical bills are not qualified")
        cat["GIRO"] = 0
        cat["CR"] = 0
        cat["Previous"] = 0
        cat["AXS"] = 0
        cat["AXS"].comment("# AXS transactions are not qualified")
        cat["ATOME"] = 0
        cat["ATOME"].comment("# ATOME is installment")
        cat["APPLE.COM/BILL"] = 3
        cat["CIRCLES.LIFE"] = 4
        cat["UOB ONE CASH REBATE"] = 5
        cat["ONE CARD ADDITIONAL REBATE"] = 5
        cat["PAYMT THRU E-BANK"] = 0
        cat["PAYMT THRU E-BANK"].comment("# credit card payment")

        qt = tmk.table()
        doc["qualifications_table"] = qt
        qt.add(tmk.comment("In this table, true are qualified transactions"))
        qt.add(tmk.comment("#0 are unqualified transactions"))
        qt["0"] = False
        qt.add(tmk.comment("#1 qualified transactions"))
        qt["1"] = True
        qt.add(tmk.comment("#2 are transports"))
        qt["2"] = False
        qt.add(tmk.comment("# track bills from Apple"))
        qt["3"] = True
        qt.add(tmk.comment("# track bills from Utilities"))
        qt["4"] = True
        qt.add(tmk.comment("# track rebates"))
        qt["5"] = False
        return doc


def main():
    # cfg = ConfigManager().config
    confm = ConfigManager()
    confm.reset()
    cfg = confm.config
    print(cfg)


if __name__ == "__main__":
    main()
