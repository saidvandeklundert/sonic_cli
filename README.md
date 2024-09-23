# sonic_cli

Some 'fun-code' for a Sonic CLI that monitors the state on the device and lets users switch between screens. 

Run locally without installing the package:


```
python -m monitor_device.controller_run_locally
```

Install locally:
```
# local install
pip install . 

# uninstall
pip uninstall sonic-cli

# editable local install:
pip install -e .
```

Test and linting:
```
python -m black .
pytest test\

pytest test\ --pdb
python -m pytest .\test\ --pdb
```

The application is structured along the lines of MVC.


Todo:
- add tail of /var/log/syslog.txt to main view
- add systems view that:
  - that displays CPU and mem usage
  - gives a tail of the logs
  - show all running containers
- give more options to the interface view:
  - toggle interfaces with and without description
  - toggle admin enabled and disabled interfaces
