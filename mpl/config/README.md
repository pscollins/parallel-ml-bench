# Overview

This directory contains different experiment configurations for MLton and MPL:

### MLton Configurations

* `mlton.json`: Default, scratch
* `mlton-baseline.json`: MLton baseline configuration (determinism + disable changed passes)
* `mlton-con.json`: `PreFlatten` for `ConApp`
* `mlton-tuple.json`: `PreFlatten` for `tuple`
* `mlton-aos.json`: `DeepFlatten` in AoS config
* `mlton-soa.json`: `DeepFlatten` in SoA config

### MPL Configurations

* `mpl.json`: Default MPL configuration
* `mpl-baseline.json`: Baseline configuration
* `mpl-con.json`: `PreFlatten` for `ConApp`
* `mpl-tuple.json`: `PreFlatten` for `tuple`
* `mpl-aos.json`: `DeepFlatten` in AoS config
* `mpl-soa.json`: `DeepFlatten` in SoA config
