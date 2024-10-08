import os
import argparse
import yaml
from typing import List, Optional
import numpy as np
import torch
import datetime
import pandas as pd

from src.model.classification.classification_network import ResNetClassifierNetwork
from src.model.classification.classification_model import (
    Classifier,
    TGradeBCEClassifier,
    TTypeBCEClassifier,
    NLLSurvClassifier,
)
from src.evaluation.prediction import process_patients
from src.evaluation.evaluation import evaluate_predictions


def load_metadata(metadata_path: str) -> pd.DataFrame:
    return pd.read_csv(metadata_path)

def load_classifier(classifier_type: str, network_type: str, model_path: str, device, config) -> Classifier:
    """Loads the appropriate classifier based on type and network."""
    # Classifier
    if classifier_type == 'TTypeBCEClassifier':
        model = TTypeBCEClassifier()
    elif classifier_type == 'TGradeBCEClassifier':
        model = TGradeBCEClassifier()
    elif classifier_type == 'NLLSurvClassifier':
        bin_size = config.get('bin_size', 1000)
        eps = config.get('eps', 1e-8)
        model = NLLSurvClassifier(bin_size=bin_size, eps=eps)
    else:
        raise ValueError(f"Unknown classifier type: {classifier_type}")

    model = model.to(device)

    # Model
    if network_type == 'ResNet18':
        network = ResNetClassifierNetwork(num_classes=model.target_size)
    elif network_type == 'ResNet50':
        network = ResNetClassifierNetwork(num_classes=model.target_size, resnet_version='resnet50')
    else:
        raise ValueError(f"Unknown network type: {network_type}")

    network = network.to(device)

    # Add network to classifier
    model.set_network(network)

    model.load_state_dict(torch.load(model_path))
    model.network.eval()

    return model


def main():
    parser = argparse.ArgumentParser(description="Evaluate classification models.")
    parser.add_argument("-c", "--config", type=str, required=True, help="Path to YAML configuration file.")
    args = parser.parse_args()

    # Load configuration from YAML file
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)

    # Extract paths and classifier information from the config
    data_root = config["data_root"]
    classifiers_config = config["classifiers"]
    output_dir = config["output_dir"]
    output_name = config["output_name"]
    reconstruction_model_path = config.get("reconstruction_model", None)

    # Create output directory for evaluation
    output_name = f"{output_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    output_path = os.path.join(output_dir, output_name)
    os.makedirs(output_path, exist_ok=True)

    # Load reconstruction model if provided
    reconstruction_model = None
    if reconstruction_model_path:
        reconstruction_model = torch.load(reconstruction_model_path)
        reconstruction_model.eval()

    # Device configuration
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Initialize classifiers
    classifiers = []
    for classifier_cfg in classifiers_config:
        classifier_type = classifier_cfg["type"]
        network_type = classifier_cfg["network"]
        model_path = classifier_cfg["model_path"]
        classifier = load_classifier(classifier_type, network_type, model_path, device, classifier_cfg)
        classifiers.append({"classifier": classifier, "name": classifier_type})

    # Load metadata
    metadata = load_metadata(data_root + "/metadata.csv")
    metadata = metadata[metadata["split_type"] == "test"]

    results = process_patients(metadata, classifiers, reconstruction_model)

    # Create DataFrame for results
    results_df = pd.DataFrame(results)

    # Save results to output directory
    results_df.to_csv(os.path.join(output_path, f"{output_name}_results.csv"), index=False)

    # Save config to output directory for reproducibility
    with open(os.path.join(output_path, "config.yaml"), "w") as f:
        yaml.dump(config, f)
    print(f"Results saved to {output_path}")

    # Evaluate predictions
    evaluate_predictions(results_df, classifiers, output_path)


if __name__ == "__main__":
    main()
