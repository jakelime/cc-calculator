APP_NAME = "ccc"
# local libraries
if __name__.startswith(APP_NAME):
    from .config import Config
    from . import models
    from . import views

else:
    from config import Config
    import models
    import views


def main():

    cfg = Config(hard_reset=True).cfg
    model = models.UobExcelReader(cfg, export_to_csv=True)
    uob = views.UobExcelViewer(cfg, model)
    uob.display_data()


if __name__ == "__main__":

    main()
