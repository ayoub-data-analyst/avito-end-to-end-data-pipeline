import os

# Run BI pipeline
os.system("python warehouse/bi_pipeline.py")

# Run ML pipeline
os.system("python warehouse/ml_pipeline.py")