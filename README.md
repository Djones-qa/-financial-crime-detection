# Financial Crime Detection 🕵️‍♂️💸

![CI Status](https://github.com/Djones-qa/-financial-crime-detection/actions/workflows/crime-detection-tests.yml/badge.svg)

A comprehensive Python-based engine designed to simulate and detect complex financial crime patterns. This intelligent suite leverages behavioral analysis and statistical anomaly detection to identify suspicious activities in synthetic transaction datasets.

## 🌟 Key Features

- **Synthetic Data Generation**: Produce highly realistic, multi-national transaction logs along with corresponding customer profiles and network mappings.
- **Velocity Abuse Detection**: Automatically identifies accounts with abnormally rapid transaction patterns indicative of automated activities.
- **Geographic Anomaly Detection**: Highlights transactions that conflict with an account's registered location or established IP history.
- **Amount Anomaly Detection**: Utilizes Z-score analysis to find statistical outliers in transaction amounts compared to historical user behavior.
- **Structuring (Smurfing)**: Detects intentional avoidance of regulatory reporting thresholds (e.g., repeatedly trading amounts just under $10K).
- **Composite Risk Scoring**: Calculates a weighted risk level for each account, categorizing them from "Low" to "Critical" to prioritize financial investigations.

## 🚀 Setup & Installation

It is recommended to run this project in a virtual environment.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Djones-qa/-financial-crime-detection.git
   cd -financial-crime-detection
   ```

2. **Install dependencies:**
   Ensure you have Python 3.11 installed (as specified by workflow requirements).
   ```bash
   pip install -r requirements.txt
   ```

## 🧪 Testing

This project uses `pytest` for rigorous functional and unit testing.

To run the complete test suite:
```bash
python -m pytest tests/
```

This will concurrently evaluate the data generators, visualization pipelines, and core financial detection logic to ensure analytical consistency. 

## 📊 Visualizations

Insights regarding transaction behavior, risk score distributions, and detection flagging percentages are generated and saved dynamically to the `visuals/` directory upon suite execution.

## ⚙️ CI/CD Integration

Continuous integration is managed automatically via an integrated **GitHub Actions** workflow (`.github/workflows/crime-detection-tests.yml`). This reliably validates application health upon push or PR directly to the `main` or `master` branch. Data visualizations output by tests are uploaded as verified artifacts in GitHub Actions for inspection.
