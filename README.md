# AI Network Intrusion Detection System (AI-NIDS)

An AI-based Network Intrusion Detection System that monitors network traffic, generates network flows, extracts traffic features, detects anomalous activity using Isolation Forest, classifies suspicious traffic using Random Forest and XGBoost, and provides SHAP-based explanations through a Flask web dashboard.

---

## 1. Project Overview

The AI-NIDS is designed as a two-stage network intrusion detection pipeline.

The system continuously observes network traffic and processes it through the following stages:

```text
NETWORK ACTIVITY
       ↓
Packet Capture
       ↓
Flow Generation
       ↓
Feature Extraction
       ↓
Isolation Forest
       ↓
   ┌───┴────┐
 NORMAL   SUSPICIOUS
             ↓
      Random Forest
             +
         XGBoost
             ↓
       Attack Class
             ↓
           SHAP
             ↓
      Flask Dashboard

The first stage provides a fast anomaly check. Traffic identified as suspicious proceeds to the second stage, where supervised machine-learning models classify the traffic.

2. Objectives

The main objectives of the project are:

Capture live network packets.
Group packets into network flows.
Extract meaningful traffic features.
Detect anomalous traffic using Isolation Forest.
Classify suspicious traffic into attack categories.
Compare Random Forest and XGBoost predictions.
Explain attack predictions using SHAP.
Record detections in a CSV log.
Display detection information through a Flask dashboard.
Validate the system using automated tests and controlled samples.
3. System Architecture

The implemented architecture is:

Windows PC
    │
    │ Browser / VS Code
    │
    ▼
Ubuntu Virtual Machine
    │
    ▼
AI-NIDS Python Application
    │
    ├── Scapy
    │
    ├── Packet Capture
    │
    ├── Flow Generation
    │
    ├── Feature Extraction
    │
    ├── Isolation Forest
    │
    ├── Random Forest
    │
    ├── XGBoost
    │
    ├── SHAP Explainability
    │
    └── Flask Dashboard

VirtualBox provides the virtualized Ubuntu environment and network interface used for live traffic capture.

4. Technology Stack
Programming Language
Python 3.14
Network Monitoring
Scapy
VirtualBox
Ubuntu Linux
Machine Learning
Scikit-learn
Random Forest
Isolation Forest
XGBoost
Explainable AI
SHAP
Data Processing
Pandas
NumPy
Web Application
Flask
HTML
CSS
JavaScript
Testing
Pytest
5. Dataset

The project uses the CICIDS2017 dataset.

The dataset contains benign network traffic and multiple categories of malicious traffic.

The project processes the machine-learning CSV files and creates:

data/
└── processed/
    ├── train.csv
    ├── test.csv
    └── live_train.csv

The live dataset contains 15 traffic classes:

BENIGN
Bot
DDoS
DoS GoldenEye
DoS Hulk
DoS Slowhttptest
DoS slowloris
FTP-Patator
Heartbleed
Infiltration
PortScan
SSH-Patator
Web Attack - Brute Force
Web Attack - Sql Injection
Web Attack - XSS

Some of the rare attack classes contain very few samples. Therefore, performance for those classes should not be interpreted as statistically reliable.

6. Preprocessing

The original CICIDS2017 flow records contain many network traffic features.

The preprocessing pipeline:

Loads the CSV data.
Removes whitespace from column names.
Removes completely empty rows and columns.
Separates the Label column.
Keeps numeric features.
Replaces infinite values.
Handles missing values.
Encodes class labels.
Applies feature scaling.

The preprocessing implementation is located in:

preprocessing/preprocess.py
7. Live Feature Extraction

For live traffic, the system uses four features:

1. dst_port
2. packet_count
3. total_bytes
4. avg_packet_size
Destination Port

The destination port of the first packet in the flow.

Packet Count

The total number of packets belonging to the flow.

packet_count = number of packets
Total Bytes

The total size of all packets in the flow.

total_bytes = sum(packet sizes)
Average Packet Size
avg_packet_size = total_bytes / packet_count

The live feature extraction implementation is located in:

preprocessing/feature_extraction.py
8. Packet Capture

The live NIDS captures packets from the Ubuntu network interface:

enp0s3

The interface is detected using Scapy.

Packet capture is implemented in:

capture/interface.py
capture/packet_capture.py

The capture process groups packets into flows.

The current flow threshold is:

10 packets

When a flow reaches the threshold, it is sent to the detection pipeline.

9. Flow Generation

A network flow is represented using:

Source IP
Destination IP
Source Port
Destination Port
Protocol

The flow generator is implemented in:

capture/flow_generator.py

Packets are grouped using a flow key based on these network attributes.

10. Two-Stage AI Detection
Stage 1 — Isolation Forest

Isolation Forest performs the first-stage anomaly detection.

Its purpose is to provide a fast check before applying the more detailed classifiers.

The result is interpreted as:

1  → NORMAL
-1 → SUSPICIOUS

Normal traffic can therefore finish at the first stage.

Suspicious traffic continues to the second stage.

11. Stage 2 — Random Forest and XGBoost

Suspicious traffic is passed to two supervised classifiers:

Random Forest
       +
XGBoost

Both models classify the traffic into one of the supported traffic categories.

The XGBoost prediction is used as the final attack class when the traffic is determined to be an attack.

The system also records the Random Forest prediction so that the two model outputs can be compared.

12. Model Performance

The live models were evaluated using a held-out test set containing:

22,339 samples
Random Forest
Accuracy: 90.67%
Weighted F1: 0.93
Macro F1: 0.78
XGBoost
Accuracy: 94.42%
Weighted F1: 0.94
Macro F1: 0.81

XGBoost achieved the higher overall accuracy on this evaluation set.

However, overall accuracy should not be interpreted as uniform performance across all attack classes because several classes have very small numbers of samples.

13. SHAP Explainability

SHAP is used to explain the XGBoost attack prediction.

When an attack is detected, the system calculates the most influential features for that particular prediction.

The four live features can therefore receive different importance values for different attack classes.

For example, controlled tests produced:

DoS Hulk
dst_port          → 3.9576
packet_count      → 2.9310
avg_packet_size   → 0.6083
total_bytes       → 0.0077
DDoS
total_bytes       → 4.4886
dst_port          → 2.4492
avg_packet_size   → 1.1143
packet_count      → 0.2445
PortScan
total_bytes       → 6.9964
dst_port          → 2.0289
packet_count      → 1.5481
avg_packet_size   → 0.4537

These examples demonstrate that the explanation is generated for the individual prediction rather than being a fixed global feature ranking.

The SHAP implementation is located in:

explainability/shap_explainer.py
14. Flask Dashboard

The Flask application provides the web interface for the NIDS.

The dashboard displays:

System Status
System Running
Detection Summary
Normal detections
Suspicious detections
Attack detections
AI Detection Pipeline
Network Traffic
Flow Generation
Feature Extraction
Isolation Forest
Random Forest
XGBoost
SHAP
Detection Details

The dashboard displays the latest attack:

Status
Attack Class
Time
Source IP
Destination IP
SHAP Explanation

The dashboard displays the top features influencing the latest attack prediction.

Recent Detections

The dashboard displays recent detection records from:

logs/detections.csv
15. Detection Logging

All detections are recorded in:

logs/detections.csv

The log format is:

time
source_ip
destination_ip
status
attack_class

Example:

2026-09-08 00:26:39,
10.0.2.2,
10.0.2.15,
ATTACK,
DoS Hulk

Normal detections have an empty attack class:

NORMAL,
16. Project Structure
AI_NETWORK_INTRUSION_DETECTION/
│
├── app.py
├── README.md
├── requirements.txt
├── pytest.ini
│
├── capture/
│   ├── __init__.py
│   ├── interface.py
│   ├── packet_capture.py
│   └── flow_generator.py
│
├── preprocessing/
│   ├── __init__.py
│   ├── preprocess.py
│   ├── feature_extraction.py
│   ├── create_dataset.py
│   └── create_live_dataset.py
│
├── models/
│   ├── __init__.py
│   ├── live_detector.py
│   ├── predict.py
│   ├── evaluate_live_models.py
│   ├── train_isolation_forest.py
│   ├── train_random_forest.py
│   ├── train_xgboost.py
│   ├── train_live_isolation_forest.py
│   ├── train_live_random_forest.py
│   └── train_live_xgboost.py
│
├── saved_models/
│   ├── live_isolation_forest.pkl
│   ├── live_isolation_scaler.pkl
│   ├── live_random_forest.pkl
│   ├── live_random_forest_scaler.pkl
│   ├── live_random_forest_label_encoder.pkl
│   ├── live_xgboost.pkl
│   ├── live_xgboost_scaler.pkl
│   └── live_xgboost_label_encoder.pkl
│
├── explainability/
│   ├── __init__.py
│   └── shap_explainer.py
│
├── dashboard/
│   └── templates/
│       └── index.html
│
├── data/
│   └── processed/
│       ├── train.csv
│       ├── test.csv
│       └── live_train.csv
│
├── logs/
│   ├── __init__.py
│   ├── logger.py
│   ├── detections.csv
│   └── shap_results.json
│
└── tests/
    ├── test_capture.py
    ├── test_features.py
    └── test_prediction.py
17. Installation
17.1 Create the Python environment
python3 -m venv venv

Activate it:

source venv/bin/activate
17.2 Install dependencies
pip install -r requirements.txt
17.3 Verify Python
which python

The expected path is similar to:

/home/<username>/AI_NETWORK_INTRUSION_DETECTION/venv/bin/python
18. Running the Flask Dashboard

Start the Flask application:

python app.py

The application listens on:

0.0.0.0:5000

Open the dashboard from the host machine:

http://127.0.0.1:5000
19. Running Live Packet Capture

Activate the virtual environment:

source venv/bin/activate

Start packet capture:

sudo "$(which python)" -m capture.packet_capture

The NIDS captures traffic from:

enp0s3

The capture can be stopped using:

Ctrl+C
20. Testing

Run the complete automated test suite:

pytest -v

The final validation produced:

tests/test_capture.py::test_capture_file_exists PASSED
tests/test_features.py::test_preprocess_data PASSED
tests/test_prediction.py::test_live_detector PASSED

3 passed
21. Controlled Attack Testing

The live detector was also tested using controlled feature samples.

DoS Hulk
Status: ATTACK
Attack Class: DoS Hulk
RF: DoS GoldenEye
XGBoost: DoS Hulk
SHAP: Generated
DDoS
Status: ATTACK
Attack Class: DDoS
RF: DDoS
XGBoost: DDoS
SHAP: Generated
PortScan
Status: ATTACK
Attack Class: PortScan
RF: PortScan
XGBoost: PortScan
SHAP: Generated

These tests validate the model and explanation pipeline without generating actual malicious network traffic.

22. Real-Time Traffic Validation

The NIDS was also tested using actual network traffic captured from the Ubuntu VM.

Observed live flows included:

Destination Port: 22
Packet Count: 10
Total Bytes: 1372
Status: NORMAL

and:

Destination Port: 59982
Packet Count: 10
Total Bytes: 1596
Random Forest: BENIGN
XGBoost: BENIGN
Status: NORMAL

The captured traffic was successfully written to the detection log and appeared on the Flask dashboard.

23. Current Validation Status
Component	Status
Ubuntu VM	PASS
VirtualBox networking	PASS
Scapy packet capture	PASS
Flow generation	PASS
Feature extraction	PASS
CICIDS2017 preprocessing	PASS
Isolation Forest	PASS
Random Forest	PASS
XGBoost	PASS
15-class classification	PASS
SHAP explainability	PASS
Detection logging	PASS
Flask API	PASS
Dashboard	PASS
Real network traffic	PASS
Controlled DoS Hulk test	PASS
Controlled DDoS test	PASS
Controlled PortScan test	PASS
Automated tests	3/3 PASS
24. Limitations

The current implementation has several limitations:

The live detector uses four simplified traffic features rather than the complete CICIDS2017 feature set.
The live flow currently uses a packet-count threshold of 10 packets.
The CICIDS2017 dataset contains highly imbalanced classes.
Some attack classes have very few examples, so their individual evaluation metrics are not statistically reliable.
The controlled attack tests validate the machine-learning pipeline but do not represent real malicious traffic generation.
The current system is intended as a research/academic prototype rather than a production-grade enterprise IDS.
Network interface configuration may need to be changed when deploying the system in a different VirtualBox or physical network environment.
25. Future Improvements

Possible future improvements include:

Use more CICIDS2017 features for live traffic.
Improve bidirectional flow aggregation.
Add flow timeout handling.
Add packet and byte rates.
Add TCP flag statistics.
Improve handling of highly imbalanced attack classes.
Perform additional hyperparameter optimization.
Add confusion matrices and ROC/PR curves.
Add real-time charts to the dashboard.
Add alert notifications.
Add database storage instead of CSV logging.
Add authentication to the dashboard.
Containerize the application.
Test the system in a controlled network-security laboratory environment.
26. Conclusion

The implemented AI-NIDS provides an end-to-end network intrusion detection pipeline.

The system combines:

Network Monitoring
        +
Flow Generation
        +
Feature Extraction
        +
Isolation Forest
        +
Random Forest
        +
XGBoost
        +
SHAP
        +
Flask Dashboard

The implementation has been validated using automated tests, controlled attack samples, SHAP explanations, and real network traffic captured from the Ubuntu virtual machine.

The final system demonstrates how machine learning and explainable AI can be integrated into a practical network intrusion detection workflow.


### Now save it

Open:

```text
README.md
# AI-Based Network Intrusion Detection System (AI-NIDS)

An AI-based Network Intrusion Detection System that monitors network traffic, generates network flows, extracts traffic features, detects anomalies using Isolation Forest, classifies suspicious traffic using Random Forest and XGBoost, and explains attack predictions using SHAP.

---

## 1. Project Overview

The system is designed to detect suspicious and malicious network activity using machine learning.

The implemented architecture is:

```text
Windows PC
    |
    v
VirtualBox
    |
    v
Ubuntu VM
    |
    v
Virtual Network Interface
    |
    v
Scapy Packet Capture
    |
    v
Flow Generation
    |
    v
Feature Extraction
    |
    v
Isolation Forest
    |
    +---- NORMAL --------------------+
    |                                |
    |                                v
    |                         Detection Log
    |
    +---- SUSPICIOUS
              |
              v
       Random Forest
              |
              v
          XGBoost
              |
        +-----+-----+
        |           |
      NORMAL      ATTACK
                    |
                    v
              SHAP Explanation
                    |
                    v
              Flask Dashboard
```

---

## 2. Main Features

- Live network packet capture using Scapy
- Flow-based traffic analysis
- Seven live traffic features
- Isolation Forest anomaly detection
- Random Forest attack classification
- XGBoost attack classification
- Two-stage detection architecture
- SHAP-based explainability
- JSON-based live flow logging
- CSV-based detection logging
- Flask web dashboard
- Automated unit/integration tests

---

## 3. Live Features

The live detector uses the following seven features:

| Feature | Description |
|---|---|
| `dst_port` | Destination port of the flow |
| `packet_count` | Number of packets in the flow |
| `total_bytes` | Total bytes observed in the flow |
| `avg_packet_size` | Average packet size |
| `flow_duration` | Duration of the flow in seconds |
| `packets_per_second` | Packet rate |
| `bytes_per_second` | Byte rate |

The same seven features are used by the live dataset, trained models, detector and SHAP explanation module.

---

## 4. Dataset

The project uses the CICIDS2017 dataset.

The dataset contains benign traffic and multiple attack categories, including:

- BENIGN
- DDoS
- PortScan
- DoS Hulk
- DoS GoldenEye
- DoS Slowhttptest
- DoS slowloris
- FTP-Patator
- SSH-Patator
- Bot
- Heartbleed
- Infiltration
- Web Attack Brute Force
- Web Attack XSS
- Web Attack SQL Injection

The live dataset is generated from CICIDS2017 using the seven features required by the live detector.

---

## 5. Project Structure

```text
AI_NETWORK_INTRUSION_DETECTION/
|
├── app.py
├── requirements.txt
├── README.md
├── pytest.ini
|
├── data/
│   ├── raw/
│   │   └── CSV/
│   └── processed/
│       ├── train.csv
│       ├── test.csv
│       └── live_train.csv
|
├── capture/
│   ├── interface.py
│   ├── packet_capture.py
│   └── flow_generator.py
|
├── preprocessing/
│   ├── preprocess.py
│   ├── feature_extraction.py
│   └── create_live_dataset.py
|
├── models/
│   ├── train_isolation_forest.py
│   ├── train_random_forest.py
│   ├── train_xgboost.py
│   ├── train_live_isolation_forest.py
│   ├── train_live_random_forest.py
│   ├── train_live_xgboost.py
│   └── live_detector.py
|
├── saved_models/
│   ├── live_isolation_forest.pkl
│   ├── live_isolation_scaler.pkl
│   ├── live_random_forest.pkl
│   ├── live_random_forest_scaler.pkl
│   ├── live_random_forest_label_encoder.pkl
│   ├── live_xgboost.pkl
│   ├── live_xgboost_scaler.pkl
│   └── live_xgboost_label_encoder.pkl
|
├── explainability/
│   └── shap_explainer.py
|
├── dashboard/
│   ├── templates/
│   │   └── index.html
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── dashboard.js
|
├── logs/
│   ├── detections.csv
│   ├── live_flows.json
│   └── shap_results.json
|
└── tests/
    ├── test_capture.py
    ├── test_features.py
    └── test_prediction.py
```

---

## 6. Requirements

Recommended environment:

- Ubuntu Linux
- Python 3
- VirtualBox
- Scapy
- Npcap/packet capture support
- Flask
- Pandas
- NumPy
- Scikit-learn
- XGBoost
- SHAP
- Joblib
- Pytest

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

---

## 7. Python Virtual Environment

Create the virtual environment:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 8. Dataset Preparation

Place the CICIDS2017 CSV files inside:

```text
data/raw/CSV/
```

Generate the live seven-feature dataset:

```bash
python preprocessing/create_live_dataset.py
```

The generated dataset is:

```text
data/processed/live_train.csv
```

---

## 9. Train Isolation Forest

Run:

```bash
python models/train_live_isolation_forest.py
```

The trained model and scaler are saved to:

```text
saved_models/live_isolation_forest.pkl
saved_models/live_isolation_scaler.pkl
```

The Isolation Forest is used as the first-stage anomaly detector.

---

## 10. Train Random Forest

Run:

```bash
python models/train_live_random_forest.py
```

The following files are generated:

```text
saved_models/live_random_forest.pkl
saved_models/live_random_forest_scaler.pkl
saved_models/live_random_forest_label_encoder.pkl
```

---

## 11. Train XGBoost

Run:

```bash
python models/train_live_xgboost.py
```

The following files are generated:

```text
saved_models/live_xgboost.pkl
saved_models/live_xgboost_scaler.pkl
saved_models/live_xgboost_label_encoder.pkl
```

---

## 12. Model Performance

Using the implemented live seven-feature dataset and the configured held-out test split:

### Random Forest

```text
Accuracy : 96.38%
Macro F1 : 0.82
Weighted F1 : 0.98
```

### XGBoost

```text
Accuracy : 98.89%
Macro F1 : 0.85
Weighted F1 : 0.99
```

These values are held-out split results from the implemented training procedure.

The dataset is highly imbalanced. Some rare attack classes have very small numbers of test samples. Therefore, the accuracy values should not be interpreted as uniform performance across every attack class.

---

## 13. Live Detection

The live detector uses a two-stage architecture.

### Stage 1 — Isolation Forest

Network traffic is first evaluated by Isolation Forest.

If the flow is considered normal:

```text
Isolation Forest
       |
       v
NORMAL
```

No second-stage classification or SHAP explanation is required.

### Stage 2 — Attack Classification

If Isolation Forest considers the flow suspicious:

```text
Isolation Forest
       |
       v
SUSPICIOUS
       |
       +----------+
       |          |
       v          v
Random Forest   XGBoost
       |          |
       +-----+----+
             |
             v
       Final Decision
```

If both classifiers identify the traffic as benign, the final result is NORMAL.

Otherwise, the XGBoost classification is used as the reported attack class.

---

## 14. SHAP Explainability

For traffic classified as an attack, SHAP is used to identify the features contributing most to the XGBoost prediction.

Example:

```text
dst_port
total_bytes
avg_packet_size
flow_duration
bytes_per_second
packet_count
packets_per_second
```

The SHAP results are stored in:

```text
logs/shap_results.json
```

---

## 15. Live Packet Capture

Find the Ubuntu network interface:

```bash
ip -br addr
```

For the current VirtualBox NAT configuration, the expected interface is:

```text
enp0s3
```

Start live packet capture using:

```bash
sudo env PYTHONPATH=/home/shreeraksha/AI_NETWORK_INTRUSION_DETECTION \
/home/shreeraksha/AI_NETWORK_INTRUSION_DETECTION/venv/bin/python \
-m capture.packet_capture
```

The capture process generates flow information and writes it to:

```text
logs/live_flows.json
```

---

## 16. Generate Normal Traffic

While packet capture is running, normal traffic can be generated using:

```bash
curl https://example.com
```

or:

```bash
curl https://www.google.com
```

Captured flows are processed by the AI-NIDS pipeline.

---

## 17. Flask Dashboard

Start the Flask application:

```bash
python app.py
```

The application runs on:

```text
http://127.0.0.1:5000
```

The dashboard provides:

- System status
- Detection statistics
- Live network activity
- Attack classifications
- SHAP explanation information
- Recent detections

---

## 18. Flask API Endpoints

### Health

```text
/health
```

### Detection data

```text
/detections
```

### SHAP data

```text
/shap
```

### Live flows

```text
/live-flows
```

---

## 19. Controlled Detection Test

A controlled test can be executed using a real attack sample from the generated live dataset.

Example:

```bash
python -c "import pandas as pd; from models.live_detector import test_attack_sample; df=pd.read_csv('data/processed/live_train.csv'); row=df[df['Label']!='BENIGN'].iloc[0]; print(row['Label']); print(test_attack_sample(dst_port=int(row['dst_port']), packet_count=int(row['packet_count']), total_bytes=float(row['total_bytes']), avg_packet_size=float(row['avg_packet_size']), flow_duration=float(row['flow_duration'])))"
```

A verified DDoS sample produced:

```text
Random Forest : DDoS
XGBoost       : DDoS

FINAL AI-NIDS DECISION
Status       : ATTACK
Attack Class : DDoS
```

SHAP also successfully generated seven feature importance values for this prediction.

---

## 20. Testing

Run the automated tests:

```bash
python -m pytest -q
```

Current project verification:

```text
3 passed
```

The tests cover:

- Packet/flow capture functionality
- Feature extraction
- Prediction functionality

---

## 21. VirtualBox Network Configuration

The current project uses an Ubuntu virtual machine inside VirtualBox.

Network configuration:

```text
Windows Host
     |
     v
VirtualBox NAT
     |
     v
Ubuntu VM
     |
     v
enp0s3
```

The Ubuntu VM uses:

```text
10.0.2.15
```

Port forwarding is configured for Flask:

```text
Windows Host 5000
       |
       v
Ubuntu Guest 5000
```

SSH forwarding is configured as:

```text
Windows Host 2222
       |
       v
Ubuntu Guest 22
```

---

## 22. Limitations

The current implementation has several limitations:

1. The live detector currently observes traffic visible to the Ubuntu VM network interface.
2. The VirtualBox NAT configuration does not represent an entire physical LAN.
3. The current flow key is directional.
4. Some rare CICIDS2017 attack classes contain very few samples.
5. Random held-out splitting can produce optimistic results when similar flows occur across train and test sets.
6. Live traffic does not necessarily have the same distribution as the CICIDS2017 training data.

---

## 23. Future Improvements

Possible future improvements include:

- Bidirectional flow construction
- More complete CICFlowMeter-compatible feature extraction
- Time-based or PCAP-based evaluation
- Additional network datasets
- Real-time packet visualizations
- Alert notifications
- Database-backed detection storage
- More advanced ensemble classification
- Deployment on a dedicated monitoring network
- Improved handling of rare attack classes

---

## 24. Project Verification Summary

The implemented system has been verified through:

```text
7-feature extraction                  PASS
Isolation Forest                      PASS
Random Forest                         PASS
XGBoost                               PASS
Two-stage detection                   PASS
SHAP explainability                   PASS
Real CICIDS2017 DDoS classification   PASS
Live Scapy flow capture               PASS
Flask application startup             PASS
Automated tests                       3/3 PASS
```

The project therefore demonstrates an end-to-end AI-assisted network intrusion detection workflow from packet capture through machine-learning-based classification and explainability.

---

## 25. Authors

**ANKITHA HIREMATH**  
**B SHRAVANI**  
**SHREERAKSHA M R**  
**VANITHA S H**  
**DEEPTI N N**

Department of Computer Science and Engineering  
Rajiv Gandhi Institute of Technology  
Bengaluru, India