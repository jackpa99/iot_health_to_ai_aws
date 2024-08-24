# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app
COPY ./tests /app/tests 

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install pytest and pytest-mock for running tests
RUN pip install pytest pytest-mock

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define environment variable
ENV NAME SageMakerTraining

# Run sagemaker_train.py when the container launches
CMD ["python", "sagemaker_train.py"]

# Command to run tests (commented out by default)
# CMD ["pytest", "tests/test_sagemaker_train.py"]