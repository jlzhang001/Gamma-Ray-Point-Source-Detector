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
