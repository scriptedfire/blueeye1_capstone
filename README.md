<p align="center">
  <a href="" rel="noopener">
 <img width=200px height=200px src="https://i.imgur.com/6wj0hh6.jpg" alt="Project logo"></a>
</p>

<h3 align="center">Project Title</h3>

<div align="center">

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![GitHub Issues](https://img.shields.io/github/issues/kylelobo/The-Documentation-Compendium.svg)](https://github.com/kylelobo/The-Documentation-Compendium/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/kylelobo/The-Documentation-Compendium.svg)](https://github.com/kylelobo/The-Documentation-Compendium/pulls)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

</div>

---

<p align="center"> This is the repository for the Space Weather Impact Tool for Power Grids. There are three main folders. Electric Field Calculator contains the magnetic field predictor, the electric field calculator, and the solar storm data scraper. The GIC and TTC folder contains the geomagnetically induced current (GIC) calculator as well as the transformer thermal capacity (TTC) estimator. GUI contains the graphical user interface as well as the central part of the system that will call each subsystem when needed.
    <br> 
</p>

## 📝 Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Deployment](#deployment)
- [Usage](#usage)
- [Built Using](#built_using)
- [TODO](../TODO.md)
- [Contributing](../CONTRIBUTING.md)
- [Authors](#authors)
- [Acknowledgments](#acknowledgement)

## 🧐 About <a name = "about"></a>

The purpose of this project is to develop a tool that can assist electrical grid operators when there is a solar storm. The goal is to predict the effects that in incoming solar storm will have on the power grid so that operators can respond ahead of time instead of responding only in real time. To do this, the solar storm data is gathered from NOAA's website from the DISCOVR satellite at the L1 Lagrange point. This data is used with Tysganenko's TS05 model to predict what the surface magnetic fields will be. With this data, the surface electric fields can be calulated which will then allow the GICs to be calculated and the transformer heating. All of this information will then be displayed to the user in a GUI.

## 🏁 Getting Started <a name = "getting_started"></a>

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See [deployment](#deployment) for notes on how to deploy the project on a live system.


### Installing

To use this code, dowload it from GitHub and execute pip install requirements.txt in your virtual environment.


## 🔧 Running the tests <a name = "tests"></a>

To test the system, run the associated test bench file.
For the Electric Field Calculator, comment out the three lines of code noted in the ElectricFieldPredictor.py file. Then run Electric_field_calculator_test_bench.py. This will test the Magnetic Field to Electric Field calculation and verify that the earth response is calcuated correctly with the 1D Quebec model. The paper that was used to do this is referneced within the code.

To see the test results of the MagneticFieldPrediction. Just run the Tysganenko_model_test_bench.py file with the B_field_prediction_2015_tsgk.csv file in the same directory. This file compares calcualted data with the predicted data from the same model on NASA's website. The data was collected and combined in this csv file. There is no way to see the test directly on the code becasue the data from NASA and the date output from the code are in significantly different formats so much data processing had to be done to format such that the data could be compared.

The NOAASolarStormDataMiner.py is easy to test. Just call it with the information described in the parent function and it will return the data from NOAA. 


## ✍️ Authors <a name = "authors"></a>

- [@kylelobo](https://github.com/kylelobo) - Idea & Initial work

See also the list of [contributors](https://github.com/kylelobo/The-Documentation-Compendium/contributors) who participated in this project.

## 🎉 Acknowledgements <a name = "acknowledgement"></a>

- References
  D. H. Boteler, R. J. Pirjola and L. Marti, "Analytic Calculation of 
  Geoelectric Fields Due to Geomagnetic Disturbances: A Test Case," 
  in IEEE Access, vol. 7, pp. 147029-147037, 2019, doi: 10.1109/ACCESS.2019.2945530.

  N. A. Tsyganenko and M. I. Sitnov, Modeling the dynamics of the inner magnetosphere during
  strong geomagnetic storms, J. Geophys. Res., v. 110 (A3), A03208, doi: 10.1029/2004JA010798, 2005
