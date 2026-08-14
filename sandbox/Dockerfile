FROM python:3.11-slim

# Install pandas and numpy
RUN pip install --no-cache-dir pandas numpy

# Create a workspace directory
WORKDIR /sandbox

# Define entrypoint to run Python code from standard input
ENTRYPOINT ["python"]
