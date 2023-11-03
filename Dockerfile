# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# # Explicitly copy the config
# COPY OAI_CONFIG_LIST /app/OAI_CONFIG_LIST


# Install the required packages
RUN pip install --trusted-host pypi.python.org pyautogen beautifulsoup4 docker
# Uncomment the line below if you need blendsearch
# RUN pip install --trusted-host pypi.python.org "pyautogen[blendsearch]"

# Specify the command to run on container start
CMD ["python", "summarize.py"]
