scoutrace-flowsimulation
========================

Simulation tool for linear scout races modelled as directed graphs with node capacity

Requires Python 3. Further requirements are listed in requirements.txt and can be installed with `pip install -r requirements.txt`

Select a route definition when starting the simulation:

```sh
python flowsimulation.py --route rute2025.py
```

The route file defaults to `rute2025.py`. Relative route paths are resolved from the project directory; absolute paths are also accepted. Route files define a `course` mapping and may expose activities as either `Act` or `Activities`.
