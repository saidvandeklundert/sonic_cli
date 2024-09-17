from monitor_device import Controller, Configuration
from monitor_device.sonic_data_testing_double import SonicDataTestingDouble


controller = Controller(
    Configuration(
        sonic_data_retriever=SonicDataTestingDouble(),
    )
)

controller.run()
