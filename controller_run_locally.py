from sonic_cli import Controller, Configuration
from test.sonic_data_testing_double import SonicDataTestingDouble

controller = Controller(
    Configuration(
        sonic_data_retriever=SonicDataTestingDouble(),
    )
)

controller.run()
