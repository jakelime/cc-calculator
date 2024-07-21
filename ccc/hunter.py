from pathlib import Path


def get_bank_excel_file(
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




if __name__ == "__main__":
    get_bank_excel_file()
