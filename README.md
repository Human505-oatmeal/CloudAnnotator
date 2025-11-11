# CloudAnnotator

Cloud Annotator is a serverless image-processing built on AWS Lambda and Amazon Rekognition. The system automatically analyzed images uploaded to S3, extracts object labels and bounding boxes using Rekognition, and annotates the image using a custom Pillow-based annotation layer. The annotated image and metadata are then stored back in S3 for downstream use.

This project was built as a demonstration for production-level serverless architecture, CI/CD automation with GitHub Actions, IAM least-privilege security practices, and modular Python design intended for scalability.

# Features
- Serverless image analysis pipeline using AWS Lambda
- Automatic object detection powered by Amazon Rekognition
- Bounding box and label drawing using Pillow
- Modular Python codebase with clear separation of concerns
- Minimal, secure IAM role design.
- CI/CD using GitHub Actions for automated deployment.
- Architecture diagram included

# Architecture Overview
![Architecture](../CloudAnnotator/docs/CloudAnnotator%20Architecture.png)

# Project Structure

```ASCII
CloudAnnotator/
│
├── .github/
│   └── workflows/
│       └── ci-cd.yml
│
├── layers/
│   └── pillow_layer.zip
│
├── src/
│   ├── lambda_function.py
│   ├── utils.py
│   └── annotation.py
│
├── tests/
│   ├── test_lambda_function.py
│   ├── test_utils.py
│   └── test_annotation.py
│
├── docs/
│   ├── architecture.drawio
│   ├── architecture.png
│   └── README.md
│
├── requirements.txt
├── .gitignore
└── README.md
```

# Technologies Used
- AWS Lambda (Python 3.13 runtime)
- Amazon Rekognition
- Amazon S3
- Cloudwatch Logs
- GitHub Actions
- Python (Pillow, boto3)

# CI/CD Pipeline
This project uses GitHub Actions to automate deployment:
- Detect changes pushed to `main`
- Install dependencies and run unit tests
- Package lambda function and layer
- Deploy to AWS using IAM OIDC (no long-lived credentials)
> [!NOTE]
> Secrets such as `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are stored securely in **Github Actions Secrets.**

# IAM Security
The deployment role assumes least-privilege IAM policy granting only:
- `lambda:UpdateFunctionCode`
- `iam:PassRole`
- Read access to Lambda configuration
- Write Access to update the specific lambda function

Execution role permissions include:
- `rekognition:DetectLabels`
- `s3:GetObject` from the source bucket
- `s3:PutObject` into the output prefix
- CloudWatch Logs write permissions
> [!NOTE]
> All permissions are scoped to specific ARNs
# Local Development
Install dependencies:
```
pip install -r requirements.txt
```
Run all tests:
```
pytest -v
```