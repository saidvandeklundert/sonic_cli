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

