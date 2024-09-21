def test_import():
    import sonic_cli
    from sonic_cli.data_models import (
        Screen,
        ScreenList,
        TerminalSize,
        UserScreen,
        ScreenData,
        MainViewData,
        LldpViewData,
        InterfaceViewData,
        ViewData,
        data_model_builder,
    )
    from sonic_cli.controller import Controller, Configuration
    from sonic_cli import monitor
