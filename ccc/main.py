try:
    import models
    import views
    from config import ConfigManager
except ImportError:
    from . import models, views
    from .config import ConfigManager


APP_NAME = "ccc"
cfg = ConfigManager().config


def main():
    model = models.UobExcelReader()
    if model.df.empty:
        fpath = models.FileManager().get_file_from_output()
        model.parse(fpath=fpath, cleanup=False)
    uob = views.UobExcelViewer(model)
    uob.display_data()


if __name__ == "__main__":
    main()
