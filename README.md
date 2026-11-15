## SPHEREx-Sky-Viewer — Exploring the Dynamic Universe
**Discovering the Universe, One Observation at a Time.**
An interactive near-infrared time-series flipbook for exploring NASA’s SPHEREx sky survey.
# About the Project
SPHEREx Sky Viewer turns multi-epoch near-infrared data from NASA’s SPHEREx space telescope into fast-loading, looped web flipbooks. Users enter sky coordinates and step through how a patch of sky changes over time, making it easier for researchers, students, and citizen scientists to spot moving or variable objects like asteroids, brown dwarfs, and variable stars.
# Why SPHEREx Needs a Visual Flipbook
NASA’s SPHEREx telescope launched on March 11, 2025, aboard a SpaceX Falcon 9 from Vandenberg Space Force Base. It maps the full sky every six months across 102 near-infrared spectral bands, capturing more than one billion objects.

**That scale creates a bottleneck:**

 Too much data for manual review: Over a billion sources across 102 bands cannot be checked by hand.
 Automated scripts miss subtle signals: Faint sources, slow proper motion, and overlapping or variable objects often slip past automated pipelines.
 Raw data is hard to use: Citizen science efforts like Backyard Worlds show how strong human pattern recognition is, yet multi-band FITS files remain tough to inspect without dedicated tools.
# Core Goal
Build a public web tool that takes a Right Ascension (RA) and Declination (Dec) and loops multi-epoch images for that patch of sky.
Features
* **Coordinate-driven sky lookup:** Enter RA and Dec to pull time-series cutouts for a specific region.
* **Time-series frame controls:** Loop epochs, step frame by frame, or add and subtract frames to highlight motion and brightness shifts.
 102-band spectral tools: Combine SPHEREx bands to improve signal-to-noise and inspect spectral features on the fly.
* **Adjustable field of view:** Balance wide coverage for faster-moving targets against download speed.
* **External catalog overlays:** Cross-check regions against archives such as Gaia and WISE.
 Shareable coordinates: Keep RA and Dec in the URL for quick sharing or embedding.
 Quality and contamination flags: Surface pixel-status and contamination flags to filter out instrumental artifacts.
* **Open-source foundation:** Built with tools like Astropy and Aladin/Web.
Tech Stack
Layer Tools, Table
# How It Works
* Data Acquisition: Query near-infrared cutouts by RA and Dec using NASA/IPAC IRSA SIA2 endpoints and AWS S3 open data buckets.
* Data Processing: Parse multi-extension FITS arrays with Astropy and PyVO and sequence frames across survey sweeps.
* Observation Comparison: Compare 6-month survey epochs side by side or in a loop to spot proper motion and brightness changes.
* Visualization: Render frames in a browser flipbook with frame-rate and band controls.
 Candidate Inspection: Review targets and benchmark objects such as WISE 0855 and Barnard’s Star.

# The Whole Architecture
* **The Spherex_integration file**This script creates a lightweight FastAPI backend server that connects your application directly to NASA’s astronomical databases. It takes sky coordinates (Right Ascension and Declination), queries NASA's IRSA archive for actual space imagery data, and returns downloadable links (access_url) that a frontend viewer (like JS9) can render.
* **The Backend file** This Astronomy Backend is a standalone Python library designed to query astronomical image metadata via NASA/IPAC IRSA's SIA2 service using Astropy and PyVO. It features robust coordinate handling, header-only FITS inspection, deterministic caching, JSON target presets, and safe product streaming while keeping storage modular and network-independent for automated testing.
# Project Preview
Add application screenshots here for:

 Dashboard
 Sky Visualization
 Time Comparison
 Object Exploration
Scientific Data &amp; Methodology
Data Sources
 NASA SPHEREx Mission
 NASA Science
 NASA Open Data Portal
 NASA/IPAC Infrared Science Archive (IRSA)
# How We Analyze Observations
 Multi-epoch near-infrared FITS handling: Uses Astropy and PyVO to parse multi-extension FITS files and isolate wavelength bands sensitive to molecular signatures (H2O, CO2, CO).
 Proper motion, parallax, and variability: Steps through 6-month survey sweeps to surface high proper-motion stars (Barnard’s Star), cold faint brown dwarfs missed by standard color cuts (WISE 0855), and variable stars changing in brightness (RW Aurigae, R Draconis).
 Quality flags and exploratory scope: Pulls pixel-status and contamination flags from IRSA to filter out instrumental artifacts. Any moving or variable target flagged in the viewer is an exploratory candidate and needs follow-up spectroscopic or photometric confirmation.

# The Team
* **Kamalesh Krithik** — Integration, Presentation:Project architecture, README documentation,
* **Ramsha Rais** — Backend Data Engineer: Python pipeline, Astropy/PyVO integration, and IRSA SIA2 API data querying.
* **Harsh Sahu** — Frontend Web Developer: UI/UX layout, coordinate search interface, and flipbook controls.
* **Piyush Warang** — Data & Systems Specialist: FITS image parsing, cache optimization, and target preset validation.
# Getting Started
* **Prerequisites**
* Git
* Python 3.9+
* Modern web browser (Chrome, Firefox, Edge, Safari)
# Installation
```
 git clone [https://github.com/rr-codes4/SPHEREX-Sky-Viewer.git](https://github.com/rr-codes4/SPHEREX-Sky-Viewer.git)
 cd SPHEREX-Sky-Viewer
 pip install -r requirements.txt
 py app.py
