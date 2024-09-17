from monitor_device import Configuration, Controller, Screen
from monitor_device.sonic_data import SonicData

if __name__ == "__main__":
    controller = Controller(
        Configuration(
            interval=1.0,
            screen=Screen.MAIN_VIEW,
            test=False,
            sonic_data_retriever=SonicData(),
        )
    )

    controller.run()
