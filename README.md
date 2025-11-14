![Python](https://img.shields.io/badge/python-3.13-blue)
![Build Status](https://github.com/Human505-oatmeal/CloudAnnotator/actions/workflows/ci-cd.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)

# CloudAnnotator

Cloud Annotator is a serverless image-processing built on AWS Lambda and Amazon Rekognition. The system automatically analyzes images uploaded to S3, extracts object labels and bounding boxes using Rekognition, and annotates the image using a custom Pillow-based annotation layer. The annotated image and metadata are then stored back in S3 for downstream use.

> [!NOTE]
> This project was built as a demonstration for production-level serverless architecture, CI/CD automation with GitHub Actions, IAM least-privilege security practices, and modular Python design intended for scalability.

# Prerequisites
Before using CloudAnnotator, ensure you have the following installed or configured:

- **Python 3.13**
- **Docker** (for building the Pillow Lambda layer)
- **AWS CLI** configured with access to S3, Lambda, and SNS
- **Git** (to clone the repository)
- **Optional:** `virtualenv` or `venv` for Python dependency isolation


# Features
- Serverless image analysis pipeline using AWS Lambda
- Automatic object detection powered by Amazon Rekognition
- Bounding box and label drawing using Pillow
- Modular Python codebase with clear separation of concerns
- Minimal, secure IAM role design
- CI/CD using GitHub Actions for automated deployment
- Architecture diagram included
- SNS notifications for empty results or runtime errors
- CloudWatch logging and custom metrics

# Architecture Overview
![CloudAnnotator serverless architecture showing S3 bucket uploads, Lambda functions for Rekognition and annotation, and output storage back to S3](/docs/CloudAnnotator_Architecture.png)

# Showcase

Here's a visual example of CloudAnnotator in action:

**Sample Input Image**
![Sample Input](/docs/sample_images/sample_input.jpg)

**Sample Output Image**
![Sample Output](/docs/sample_images/sample_output.jpg)

**Animated Showcase**
![Project Showcase](/docs/showcase/project_showcase.gif)

# Project Structure

```ascii
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
│   ├── annotation.py
│   └── rekognition.py
│
├── tests/
│   ├── test_lambda_function.py
│   ├── test_utils.py
│   └── test_annotation.py
│
├── docs/
│   ├── architecture.drawio
│   ├── architecture.png
│   ├── sample_input.jpg
│   ├── sample_output.jpg
│   └── showcase/
│       └── project_showcase.gif
│
├── docker/
│   └── Dockerfile
│
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

# Technologies Used
- AWS Lambda (Python 3.13 runtime)
- Amazon Rekognition
- Amazon S3
- Amazon SNS
- CloudWatch Logs & Metrics
- GitHub Actions
- Python (Pillow, boto3)
- Docker (optional, for Pillow layer packaging)

# CI/CD Pipeline
This project uses GitHub Actions to automate deployment:
- Detect changes pushed to `main`
- Install dependencies and run unit tests
- Package Lambda function and layer
- Deploy to AWS using IAM OIDC (no long-lived credentials)
> [!NOTE]
> Secrets such as `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are stored securely in **GitHub Actions Secrets.**

# IAM Security
<details><summary>Deployment & Execution Roles (click to expand)</summary>
The deployment role assumes least-privilege IAM policy granting only:
- `lambda:UpdateFunctionCode`
- `iam:PassRole`
- Read access to Lambda configuration
- Write Access to update the specific lambda function

Execution role permissions include:
- `rekognition:DetectLabels`
- `s3:GetObject` from the source bucket
- `s3:PutObject` into the output prefix
- `sns:Publish` for notifications
- CloudWatch Logs write permissions
- `sts:GetCallerIdentity`

> **NOTE:** All permissions are scoped to specific ARNs

</details>

<details><summary>AWS Inline Policy JSON (click to expand)</summary>

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "S3Access",
            "Effect": "Allow",
            "Action": ["s3:GetObject", "s3:PutObject"],
            "Resource": ["arn:aws:s3:::amzn-s3-prj-img-rek/*"]
        },
        {
            "Sid": "RekognitionDetectLabels",
            "Effect": "Allow",
            "Action": ["rekognition:DetectLabels"],
            "Resource": "*"
        },
        {
            "Sid": "SNSPublishAlerts",
            "Effect": "Allow",
            "Action": ["sns:Publish"],
            "Resource": [
                "arn:aws:sns:us-east-2:905418313758:RekognitionTopic",
                "arn:aws:sns:us-east-2:905418313758:LambdaRuntimeErrors"
            ]
        },
        {
            "Sid": "STSIdentity",
            "Effect": "Allow",
            "Action": ["sts:GetCallerIdentity"],
            "Resource": "*"
        },
        {
            "Sid": "LogsAccess",
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:us-east-2:905418313758:*",
                "arn:aws:logs:us-east-2:905418313758:log-group:/aws/lambda/rekognition_label_lambda:*"
            ]
        }
    ]
}
```

> **NOTE:** Replace with your ARNs accordingly. This is what was used during the production of this project.

</details>

# Local Development

<details> <summary>Build Lambda Pillow Layer with Docker</summary>


> **NOTE:** To ensure Pillow is compatible with AWS Lambda’s Python 3.13 runtime, we use an Amazon Linux 2023 Docker container.

```dockerfile
FROM amazonlinux:2023
WORKDIR /var/task
RUN dnf install -y \
        python3 \
        python3-pip \
        python3-devel \
        gcc \
        gcc-c++ \
        libjpeg-turbo-devel \
        zlib-devel \
        freetype-devel \
        lcms2-devel \
        tcl-devel \
        tk-devel \
        zip \
    && dnf clean all
RUN mkdir -p /var/task/python
RUN pip3 install --target /var/task/python pillow
WORKDIR /var/task/python
RUN zip -r9 ../pillow-layer.zip .
CMD ["bash"]
```

```bash
# Step 1: Build Docker image
docker build -t pillow-lambda-layer ./docker

# Step 2: Run container to generate zip
docker run --name temp-pillow pillow-lambda-layer

# Step 3: Copy pillow_layer.zip to local layers folder
docker cp temp-pillow:/var/task/pillow-layer.zip ./layers/pillow_layer.zip

# Step 4: Remove temporary container
docker rm temp-pillow
```

> **NOTE:** The **pillow_layer.zip** is now in the **layers/** folder and can be attached as a Lambda layer.

</details>

# Running Locally

Install dependencies:
```bash
pip install -r requirements.txt
```

Run all tests:
```bash
pytest -v
```
