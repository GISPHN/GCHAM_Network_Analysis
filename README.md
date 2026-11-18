# G-CHAM Network Analysis

QGIS plugin for shortest-distance routes, multi-origin catchment analysis, and multi-team public health patrol planning.

## Features

- Shortest-distance routes on a supplied road network
- Distance- and travel-time-based catchments, with combined or origin-specific outputs
- Multi-team patrol planning, including automatic adjustment options for unvisited destinations
- Walking, cycling, vehicle census, and custom travel speeds
- CSV, Excel summary workbook, and GeoPackage outputs
- Japanese and English interface and generated outputs

The patrol workbook is named `*_summary_report.xlsx`; the companion CSV remains `*_summary.csv`.

## Requirements

- QGIS 3.28 or later, including QGIS 4.x
- A projected road network in meters, with intersections split and connected at vertices

The routing engine uses the supplied line geometry and does not model one-way restrictions, vehicle access restrictions, or intersection delays. Patrol plans use a heuristic and are not guaranteed to be globally optimal.

## Installation

Install the plugin ZIP through QGIS Plugin Manager's “Install from ZIP” function. The Japanese guide includes detailed input descriptions, speed sources, and interpretation notes: [README_ja.txt](README_ja.txt).

## License

MIT. See [LICENSE](LICENSE).
