# Ariadne

## Astrodynamics, Orbit Estimation and Conjunction Assessment Framework

<p align="center">
<img src="assets/orbit_hero.jpg" width="900" alt="Ariadne orbit visualization hero image"/>
</p>

Ariadne is a research focused astrodynamics framework for orbital propagation, orbit estimation and conjunction assessment.

The project combines orbital mechanics, numerical computation and statistical estimation into a unified command line tool capable of working with both local satellite data and live orbital catalogs.

Every workflow follows the same philosophy. Data is ingested, normalized into a common satellite state model, analysed, and exported into scientific or visualization friendly formats.

---

## Features

### Data Ingestion

Ariadne accepts multiple satellite data formats through a single interface.

Supported inputs include

• TLE catalogs

• CSV state vectors

• Plain text state files

• Automatic format detection

• Unified satellite state representation

---

### Live Catalog Fetching

Satellite catalogs can be retrieved directly from public providers.

Supported sources include

• CelesTrak

• Space Track

Features include

• NORAD lookup

• Catalog downloads

• Local caching

• Live propagation workflows

---

## Command Line Interface

Everything is available through a single executable.

```bash
ariadne fetch
ariadne validate
ariadne propagate
ariadne od
ariadne conjunct
ariadne screen
```

Example commands

```bash
ariadne fetch --source celestrak --group active

ariadne validate --input iss.tle

ariadne propagate --input iss.tle --hours 24 --step 30

ariadne od --input observations.csv --method ukf

ariadne conjunct --primary sat_a.tle --secondary sat_b.tle

ariadne screen --catalog active.tle --primary iss.tle --threshold-km 5
```

---

## Orbital Propagation

Ariadne provides tools for modelling and predicting spacecraft trajectories using orbital state information.

Capabilities include

• TLE parsing

• Satellite orbit propagation

• Numerical propagation

• Future state prediction

• Orbital trajectory analysis

• Propagation validation

<p align="center">
<img src="assets/orbit_propagation.jpg" width="800" alt="Orbital trajectory analysis and propagation validation plot"/>
</p>

---

## Reference Frame Transformations

Accurate coordinate transformations are essential for spacecraft tracking and observation modelling.

Supported transformations include

• Earth Centered Inertial

• Earth Centered Earth Fixed

• Topocentric frames

• Azimuth elevation and range

• Observation geometry

<p align="center">
<img src="assets/frame_transform.jpg" width="800" alt="Azimuth, elevation, and range observation geometry diagram"/>
</p>

---

## Measurement Simulation

Ariadne provides configurable observation simulation for developing and testing estimation systems.

Features include

• Synthetic observations

• Range measurements

• Angular measurements

• Sensor noise models

• Ground truth generation

---

## Orbit Determination

Ariadne estimates spacecraft states from imperfect observations using nonlinear estimation techniques.

Supported methods

• Batch Least Squares

• Extended Kalman Filter

• Unscented Kalman Filter

Capabilities include

• State prediction

• Measurement updates

• Covariance propagation

• Uncertainty estimation

---

## Statistical Validation

Filter performance is evaluated through statistical consistency testing.

Methods include

### NEES

Normalized Estimation Error Squared

### NIS

Normalized Innovation Squared

These metrics verify that predicted uncertainty remains consistent with observed estimation performance.

---

## Conjunction Assessment

Ariadne evaluates close approaches between resident space objects.

Capabilities include

• Relative state computation

• Time of closest approach

• RIC frame analysis

• Covariance combination

• Collision probability estimation

• Hard body radius modelling

---

## Space Object Screening

Entire satellite catalogs can be screened for potential conjunction events.

Features include

• Catalog processing

• Candidate filtering

• Encounter screening

• Risk identification

<p align="center">
<img src="assets/catalog_screening.jpg" width="800" alt="Catalog conjunction screening and risk identification plot"/>
</p>

---

## Export

Analysis results can be exported into multiple formats.

Supported outputs

• JSON

• CSV

• CZML

• Ground track plots

• RIC plots

These outputs integrate with scientific workflows and Cesium based visualization.

---

## Validation

Ariadne is evaluated against publicly available orbital data and historical conjunction scenarios.

Validation includes

• Standard propagation benchmarks

• Real satellite tracking

• Historical conjunction cases

• Predicted versus reported encounters

<p align="center">
<img src="assets/historical_validation.jpg" width="800" alt="Historical conjunction cases: predicted versus reported encounters"/>
</p>

---

## Project Structure

```text
Ariadne/
│
├── ariadne/
│   ├── cli/
│   ├── ingest/
│   ├── fetch/
│   ├── propagate/
│   ├── estimate/
│   ├── conjunction/
│   ├── export/
│   ├── viewer/
│   ├── models/
│   ├── utils/
│   └── config/
│
├── data/
├── docs/
├── tests/
├── examples/
├── assets/
└── pyproject.toml
```

---

## Installation

```bash
git clone https://github.com/yourusername/Ariadne.git

cd Ariadne

python -m venv .venv

source .venv/bin/activate

pip install -e .
```

---

## Design

Ariadne follows a layered architecture.

```text
Input

↓

Satellite State

↓

Propagation

↓

Estimation

↓

Conjunction

↓

Export
```

Every module remains independent while sharing the same normalized satellite state representation.

---

## Documentation

Documentation includes

• API reference

• Mathematical background

• Command reference

• Usage examples

• Validation studies

---

## Testing

Quality assurance includes

• Unit testing

• Numerical regression

• Property based testing

• Statistical validation

• Continuous integration

---

## Scientific Foundations

Ariadne is built upon

• Orbital mechanics

• Numerical methods

• Probability theory

• Bayesian estimation

• Space Situational Awareness

---

## Roadmap

Current development focuses on

• Robust data ingestion

• Live catalog integration

• Orbit propagation

• Orbit determination

• Conjunction assessment

• Scientific visualization

---

## License

Apache 2.0 License
