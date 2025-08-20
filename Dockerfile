# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY app/requirements.txt .

# Install any needed packages specified in requirements.txt
# We also install 'build-essential' for packages that might need compilation
# and 'dictionaries-common' to get the /usr/share/dict/words file.
RUN apt-get update && apt-get install -y build-essential dictionaries-common && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y build-essential && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code into the container at /app
COPY ./app .

# Define the command to run your application
CMD ["python", "run_experiments.py"]