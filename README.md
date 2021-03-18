# Gamma-Ray-Point-Source-Detector
Localization and classification of gamma-ray point sources using Machine Learning

![alt text](https://github.com/bapanes/Gamma-Ray-Point-Source-Detector/blob/main/figures/full-pipeline-high-lat-pie.png)

The material in this repoistory can be used to run a test example of the the pipeline developed in the paper arXiv:2102.02XXX in inference mode. Also, it includes routines to evaluate the test run and produce similar plots. 

Codes to run patch generation, UNEK predictions and localization evaluations

```
from-cats-to-locnet-input.py

from-locnet-input-to-unek-output.py

from-unek-output-to-locnet-evaluation.py
```

Codes to visualize localization and classification results

```
localization-plots.ipynb

classification-plots.ipynb

full-pipeline-piechart.ipynb
```

Codes to train localization and classificatoin algorithms

```
localization-net-training.py

classification-net-training.py
```

The data that is used to run the previous two codes can be found in the zenodo.org dataset associated to this repository, see details below

## ZENODO datasets for training and test

Along with this GitHub repository we also realease a dataset in the zenodo.org platform. This data includes thousand of patches, with their corresponding CSV files, which are useful to train new localization and classification algorithms. Also, we made available five blind data sets for tests, which can be used to make comparisons between different algorithms. All this material is available in the following link

[ZENODO page: Gamma-ray Point Sources Detection and Classification Project](https://zenodo.org/record/4587205#.YFOKBSPhD_Q)

Notice that compressed files (.tgz) must be extracted by using the following command

```
tar -xjvf file_name.tgz 
```

