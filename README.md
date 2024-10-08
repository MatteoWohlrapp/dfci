# Bias in MRI Reconstruction 

[Under construction] A modular framework for understanding (demographic) bias and generalization in MRI reconstruction.

## Dependencies 
To install the necessary dependencies, run `pip install -r requirements.txt`.

## Usage 
The classifiers and dataloader are structured around the UCSF-PDGM dataset. 

### Classifier 
Parameters for classifier training are configured through yaml files. Examples can be found in the `configuration` folder. There are different classifiers for different predictions, such as tumor type, tumor grade, or survival days. 
To train a classifier, run `python train_classifier -c <path to configuration file>`. You can visualize training logs with `tensorboard --logdir=./runs`.