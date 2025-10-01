"""
AWS Lambda handler for agent2_ingestor FastAPI application.
This file adapts the FastAPI app to work with AWS Lambda and API Gateway.
"""

from mangum import Mangum
from main import app

# Create the Lambda handler
handler = Mangum(app, lifespan="off")