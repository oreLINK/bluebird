"""Bluebird data pipeline.

Data flows through four medallion layers, each in its own sub-package:

- ``bronze``  : ``Extractor`` classes fetch raw source data, stored unchanged.
- ``silver``  : ``Transformer`` classes clean and normalise bronze data.
- ``gold``    : ``Aggregator`` classes compute KPIs from silver data.
- ``diamond`` : ``Displayer`` classes shape gold data into frontend JSON.
"""

__version__ = "0.1.0"
