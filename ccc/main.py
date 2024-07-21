try:
    from config import ConfigManager
    import models
    import views
except ImportError as e:
    raise e
    from .config import ConfigManager
    from . import models
    from . import views


APP_NAME = "ccc"
cfg = ConfigManager().config

def main():

    model = models.UobExcelReader()
    uob = views.UobExcelViewer(cfg, model)
    uob.display_data()


if __name__ == "__main__":
    main()
