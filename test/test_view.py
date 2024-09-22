from sonic_cli.data_models import (
    main_view_model_builder,
    lldp_view_model_builder,
    interface_view_model_builder,
)
from test.sonic_data_testing_double import SonicDataTestingDouble
from sonic_cli.view import MainView, InterfacesView, LldpView


def test_main_view(sonic_data_testing_double: SonicDataTestingDouble):
    data = main_view_model_builder(sonic_data_testing_double)
    main_view = MainView(data=data)
    assert isinstance(main_view, MainView)
    rendered_output = main_view.render()
    assert isinstance(rendered_output, str)
    assert "System model:" in rendered_output
    assert "System version:" in rendered_output
    assert "Kernel version:" in rendered_output
    assert "Detected LLDP neighbors:" in rendered_output


def test_lldp_view(sonic_data_testing_double: SonicDataTestingDouble):
    data = lldp_view_model_builder(sonic_data_testing_double)
    view = LldpView(data=data)
    assert isinstance(view, LldpView)
    rendered_output = view.render()
    assert isinstance(rendered_output, str)


def test_interfaces_view(sonic_data_testing_double: SonicDataTestingDouble):
    data = interface_view_model_builder(sonic_data_testing_double)
    view = InterfacesView(data=data)
    assert isinstance(view, InterfacesView)
    rendered_output = view.render()
    assert isinstance(rendered_output, str)
