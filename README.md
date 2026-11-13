🌌 SPHEREx-Sky-Viewer — Exploring the Dynamic Universe

<p align="center">
<img src="https://img.shields.io/badge/NASA-Space%20Apps%20Challenge-0B3D91?style=for-the-badge&logo=nasa&logoColor=white" />
<img src="https://img.shields.io/badge/Year-2026-171717?style=for-the-badge" />
<img src="https://img.shields.io/badge/Domain-Astrophysics-6C63FF?style=for-the-badge" />
<img src="https://img.shields.io/badge/Status-In%20Development-orange?style=for-the-badge" />
</p>

<h3 align="center">
Discovering the Universe, One Observation at a Time.
</h3>

<p align="center">
<i>Interactive near-infrared time-series data viewer for NASA's SPHEREx mission data.</i>
</p>

**About the Project**

The SPHEREx Sky Viewer is an interactive web-based flip-book for visualizing near-infrared time-domain data from the NASA SPHEREx space telescope. Our visualization transforms complex multi-epoch data from astronomical surveys into quick-to-load looped images enabling citizen scientists and researchers to detect moving targets like asteroids, brown dwarfs, and variable stars missed by automated algorithms.

## Understanding SPHEREx and the need for this project
The SPHEREx space telescope launched on  March 11, 2025, on a SpaceX Falcon 9 rocket from Vandenberg Space Force Base.Its primary objective was to conduct an all-sky spectral survey in optical and near-infrared light (102 color bands) to map the cosmos. Since then it has returned images of more than a billion objects.


**🎯 Problem Statement**

* **Overwhelming Data Scale:** NASA's SPHEREx mission maps the entire sky every six months across 102 near-infrared spectral bands, collecting images of over one billion celestial objects—including brown dwarfs, asteroids, comets, and variable stars.
* **Limitations of Automated Algorithms:** Due to the high density of data in space, many automated searching scripts will fail to detect subtle proper motions, faint objects, or overlapping/variable objects. 
* **The Manual Inspection Bottleneck:** Although citizen science project like the Backyard World have proven that human engagement and pattern recognition is important to find rare objects but analyzing raw multi-spectral data remains too complex for everyday volunteers without specialized tools. 

**Our Challenge**
* A public facing web-tool that loops over the images of the specific patch of sky
* Users enter the coordinate in terms of Right Ascension and Declination
  
**🚀 Advanced Features & Design Considerations**
* Modular and Scalable Data Pipeline: Ingests incoming rolling data releases from SPHEREx.
* Multi-band and spectral analysis: Combines the 102 bands in SPHEREx using the detector arrays to improve signal to noise ratios and produce spectral information on the fly.
* Time series image manipulation: Ability to sequence frames together, add/subtract images from different timeframes to highlight moving or variable objects.
* Customizable field of view: Users can choose the size of their field of view to balance between wide fields for fast moving objects and optimal downloading speeds.
* Overlay external archival data: Combine with data from other missions (e.g Gaia, WISE).
* URL coordinates: Include co-ordinates in the URL to allow easy sharing and embedding on external websites.
* Metadata and Quality Flags: Show essential data including contamination and pixel flags.
*Open source: Utilises open source tools such as Astropy, Aladin/Web.

🛰️ Technology & Tools

Our project combines modern development technologies with astronomical data exploration.

Technology	Application
Frontend	HTML5 / CSS3 / JavaScript
Backend	Python
Programming Language	Python & JavaScript
Data Processing	Astropy & PyVO
Visualization	Custom Canvas / Image Flipbook Engine
APIs / Data Sources	NASA/IPAC Infrared Science Archive (IRSA) SIA2 & AWS S3
⚙️ How It Works

Our proposed workflow:

mermaid
flowchart TD
   * A["🛰️ SPHEREx Observational Data"] --> B["📥 Data Acquisition"]
   * B --> C["⚙️ Data Processing"]
   * C --> D["🔍 Observation Comparison"]
   * D --> E["📊 Visualization"]
   * E --> F["🌌 Interactive Sky Exploration"]
   * F --> G["🔭 Investigating Potential Moving Objects"]

    style A fill:#102B55,color:#fff
    style F fill:#403477,color:#fff
    style G fill:#173E35,color:#fff

*Data Acquisition: Query near-infrared astronomical cutouts via NASA/IPAC IRSA SIA2 endpoints and AWS S3 open data buckets using sky coordinates (RA/Dec).
*Data Processing: Parse multi-extension FITS spectral arrays using Astropy and PyVO to sequence multi-epoch survey sweeps.
*Observation Comparison: Compare 6-month survey interval frames side-by-side or in loops to identify proper motion and brightness variability.
*Visualization: Render multi-spectral observations through an interactive web-based flipbook engine with custom frame-rate controls.
*Exploration: Enable users and citizen scientists to visually inspect celestial targets, including benchmark candidates like WISE 0855 and Barnard’s Star.

Project Preview

<p align="center">
<b>Explore the Universe Through Our Platform</b>
</p>

<!-- Add your actual application screenshots below -->

Dashboard	Sky Visualization
!Dashboard	!Sky Explorer
Time Comparison	Object Exploration
!Comparison	!Object Explorer
Replace these image paths with screenshots from your actual application.

# 🧪 Scientific Data & Resources

Our project is inspired by publicly available astronomical research and NASA's scientific resources.

NASA SPHEREx Mission
NASA Science
NASA Open Data Portal
NASA/IPAC Infrared Science Archive

Scientific note: Potential moving-object candidates identified through our platform are exploratory observations, not confirmed astronomical discoveries.

## 🔬 Scientific Methodology & Validation

 **1. Handling Multi-Epoch Near-Infrared Data**
SPHEREx maps the entire sky every six months in 102 near-infrared bands. Our backend processes multi-extension FITS (Flexible Image Transport System) files via **Astropy** and **PyVO**, allowing researchers to isolate specific wavelength bands rich in molecular signatures ($\text{H}_2\text{O}, \text{CO}_2, \text{CO}$).

**2. Detecting Proper Motion & Parallax**
By sequencing observations across multiple 6-month survey sweeps, our flipbook engine enables the visual detection of:
* **High Proper Motion Objects:** Tracking angular sky displacement over time (e.g., benchmark target **Barnard’s Star**).
* **Sub-stellar Brown Dwarfs:** Identifying faint, moving cold objects that traditional automated color-cut pipelines often overlook (e.g., benchmark target **WISE 0855**).
* **Variable Stars:** Spotting flux/brightness changes across epochs (e.g., **RW Aurigae** and **R Draconis**).

**3. Scientific Integrity & Rigor**
* **Exploratory Classification:** All moving objects or transient anomalies flagged by our interface are categorized as *candidate detections* requiring secondary spectroscopic or photometric verification.
* **Metadata & Quality Flag Integration:** Pulls pixel-status and contamination flags directly from IRSA archives to ensure users don't mistake instrumental artifacts for real astronomical bodies.
# Our Impact

We believe that space exploration should not be limited to scientists and research institutions.

# Our project aims to:

Make astronomical observations easier to understand.
Encourage curiosity about the universe.
Promote the use of open scientific datasets.
Introduce students to real-world astronomical exploration.
Demonstrate how technology can make scientific data more accessible.

Because every great discovery begins with curiosity.

# 👨‍🚀 Meet the Team
  
* **Kamalesh Krithik** Integration, Presentation & Domain Lead	Project architecture, README documentation, scientific validation, and pitch presentation

* **Ramsha Rais**	Backend Data Engineer	Python pipeline, Astropy/PyVO integration, and IRSA SIA2 API data querying

* **Harsh Sahu**	Frontend Web Developer	Interactive UI/UX layout, coordinate search interface, and flipbook controls
  
* **Piyush Warang**	Data & Systems Specialist	FITS image parsing, cache optimization, and target preset validation

🛠️ Getting Started
Prerequisites
Git
Python 3.9+
Modern Web Browser (Chrome, Firefox, Edge, Safari)

# Installation
    ```bash
     
       git clone https://github.com/rr-codes4/SPHEREX-Sky-Viewer.git
       cd SPHEREX-Sky-Viewer


# Install the dependencies:

    ```bash

       pip install -r requirements.txt


# Start the application:

    ```bash
      py app.py


# Acknowledgements

We express our gratitude to:

NASA — For the SPHEREx mission and its contribution to astronomical research.
NASA Space Apps Challenge — For encouraging innovation through science and technology.
The open-source community — For providing tools and resources that support our development.


<p align="center">
<img src="https://img.shields.io/badge/BUILT%20WITH-CURIOSITY-6C63FF?style=for-the-badge" />
</p>

<h2 align="center">
🌌 LOOK UP. EXPLORE. DISCOVER.
</h2>

<p align="center">
<i>Exploring the universe, one observation at a time.</i>
<br><br>
<b>NASA Space Apps Challenge 2026</b>
</p>
