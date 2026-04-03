# GNSS/INS Stereo-Spatial Joint Positioning

A sensor-fusion project for trajectory estimation using GNSS and inertial measurements, built around Kalman filtering, data preprocessing, time alignment, and trajectory visualization.

This repository combines:

- Simulation-based validation using formatted GNSS/IMU sample logs
- Real-data experiments using processed BeiDou/GNSS and INS records
- Two fusion strategies: loose coupling and close coupling
- Supporting scripts for preprocessing, anomaly filtering, and 2D/3D result visualization

## Project Overview

GNSS provides globally referenced positioning, but can be noisy, intermittent, and sensitive to multipath and altitude outliers. INS offers high-rate motion measurements, but its integration drifts over time. This project explores how to combine the two to obtain smoother and more stable trajectory estimates.

The implementation focuses on a practical engineering pipeline:

1. Parse raw GNSS and IMU logs
2. Clean and reformat the measurements
3. Filter abnormal altitude points
4. Align asynchronous GNSS and INS timestamps
5. Fuse the measurements with Kalman filters
6. Visualize fused trajectories and error trends

## Core Methods

### 1. Loose Coupling

File: [`experiment/loose_coupling.py`](/Users/hilbert/Desktop/Stereo-Spatial-Joint-Positioning-Technology-Based-on-GNSS-INS/experiment/loose_coupling.py)

The loose-coupling model treats GNSS position as the measurement and uses INS acceleration as the control input to drive the state prediction.

- State dimension: 9
- State variables: position, velocity, acceleration
- Measurement: longitude, latitude, altitude
- Control input: `acc_x`, `acc_y`, `acc_z`

This design is simple, interpretable, and useful as a baseline fusion architecture.

### 2. Close Coupling

File: [`experiment/close_coupling.py`](/Users/hilbert/Desktop/Stereo-Spatial-Joint-Positioning-Technology-Based-on-GNSS-INS/experiment/close_coupling.py)

The close-coupling model expands the state and directly incorporates both GNSS and inertial observations into the Kalman update.

- State dimension: 15
- State variables: position, velocity, acceleration, attitude, angular velocity
- Measurement dimension: 6
- Measurements: GNSS position plus INS acceleration

Compared with loose coupling, this approach preserves more motion information inside the filter and better reflects the structure of integrated navigation systems.

## Data Processing Pipeline

Key utility files:

- [`experiment/utils.py`](/Users/hilbert/Desktop/Stereo-Spatial-Joint-Positioning-Technology-Based-on-GNSS-INS/experiment/utils.py)
- [`experiment/preprocessing/gnss_preprocess.py`](/Users/hilbert/Desktop/Stereo-Spatial-Joint-Positioning-Technology-Based-on-GNSS-INS/experiment/preprocessing/gnss_preprocess.py)
- [`experiment/preprocessing/imu_preprocess.py`](/Users/hilbert/Desktop/Stereo-Spatial-Joint-Positioning-Technology-Based-on-GNSS-INS/experiment/preprocessing/imu_preprocess.py)

The preprocessing and alignment workflow includes:

- GNSS log extraction into structured timestamped position records
- IMU log extraction with acceleration bias correction
- Frame transformation of acceleration from body coordinates to ENU
- Optional gravity removal from inertial measurements
- Rolling-window altitude outlier filtering
- Timestamp alignment between lower-rate GNSS and higher-rate INS data

The current experimental dataset in this repository includes approximately:

- 116 processed GNSS samples
- 1421 processed INS samples

## Repository Structure

```text
.
├── experiment/
│   ├── close_coupling.py
│   ├── loose_coupling.py
│   ├── utils.py
│   ├── preprocessing/
│   ├── legacy/
│   ├── archive/
│   ├── processed_bd.txt
│   └── processed_gd.txt
├── simulation/
│   ├── kalman_fusion.py
│   ├── kalman_fusion_v2.py
│   ├── raw_data_converter.py
│   ├── outlier_filter.py
│   ├── gnss_plot_2d.py
│   ├── gnss_plot_3d.py
│   ├── sample*.txt
│   └── *.png
└── README.md
```

## Experimental Outputs

The repository already contains generated trajectory figures under [`simulation/`](/Users/hilbert/Desktop/Stereo-Spatial-Joint-Positioning-Technology-Based-on-GNSS-INS/simulation):

- [`simulation/filtered_path.png`](/Users/hilbert/Desktop/Stereo-Spatial-Joint-Positioning-Technology-Based-on-GNSS-INS/simulation/filtered_path.png)
- [`simulation/filtered_path_3D.png`](/Users/hilbert/Desktop/Stereo-Spatial-Joint-Positioning-Technology-Based-on-GNSS-INS/simulation/filtered_path_3D.png)
- [`simulation/filtered_path_3D_origin.png`](/Users/hilbert/Desktop/Stereo-Spatial-Joint-Positioning-Technology-Based-on-GNSS-INS/simulation/filtered_path_3D_origin.png)

These outputs demonstrate the project’s ability to:

- Reconstruct 2D and 3D motion trajectories from raw measurement logs
- Compare raw GNSS paths against fused trajectories
- Inspect altitude behavior and outlier effects visually

## Tech Stack

- Python
- NumPy
- Pandas
- Matplotlib
- FilterPy
- GeographicLib
- Optional MATLAB scripts for supplementary testing

## Quick Start

### Environment

Recommended Python version: `3.9+`

Install the main dependencies:

```bash
pip install numpy pandas matplotlib filterpy geographiclib openpyxl
```

### Run Real-Data Fusion Experiments

Loose coupling:

```bash
cd experiment
python loose_coupling.py
```

Close coupling:

```bash
cd experiment
python close_coupling.py
```

### Run Preprocessing Scripts

GNSS preprocessing:

```bash
cd experiment/preprocessing
python gnss_preprocess.py
```

IMU preprocessing:

```bash
cd experiment/preprocessing
python imu_preprocess.py
```

### Run Simulation Scripts

```bash
cd simulation
python kalman_fusion.py
python kalman_fusion_v2.py
```

## What This Project Demonstrates

For GitHub and resume presentation, this project highlights the following engineering capabilities:

- Sensor fusion system design for GNSS/INS integrated navigation
- Kalman filter modeling with explicit state-space formulation
- Practical handling of asynchronous multi-sensor data streams
- Measurement cleaning, outlier detection, and coordinate transformation
- Experimental scripting for visualization and algorithm validation
- End-to-end workflow from raw logs to fused trajectory outputs

## Resume-Friendly Summary

Designed and implemented a GNSS/INS sensor-fusion pipeline for trajectory estimation using loose-coupling and close-coupling Kalman filters. Built preprocessing scripts for raw GNSS/IMU logs, performed timestamp alignment and altitude outlier filtering, transformed inertial measurements into a navigation frame, and generated 2D/3D visualizations for simulation and real-data validation.

## Current Limitations

This repository is best understood as an experimental navigation prototype rather than a production-grade localization stack.

Current limitations include:

- Filter parameters are manually tuned rather than automatically optimized
- Evaluation is primarily qualitative, with limited benchmark metrics
- File paths and script entrypoints are research-oriented rather than packaged as a library
- Some historical scripts remain in `archive/` and `legacy/` for comparison and traceability

## Next-Step Improvements

If this project is extended further, the highest-value upgrades would be:

- Add quantitative evaluation metrics such as RMSE and drift statistics
- Refactor the fusion logic into reusable modules
- Provide a unified CLI or notebook workflow
- Add unit tests for parsing, alignment, and filtering functions
- Compare loose and close coupling on a shared benchmark dataset

## License

No license file is currently included. Add a license before public distribution if you plan to open-source this project on GitHub.
