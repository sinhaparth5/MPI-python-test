# Use Ubuntu as base image
FROM ubuntu:22.04

# Install required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    mpich \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install mpi4py numpy

# Create working directory
WORKDIR /app

#COPY Python scripts
COPY master_node.py .
COPY worker_node.py .

# Set environment variables for MPI
ENV OMPI_ALLOW_RUN_AS_ROOT=1
ENV OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1

CMD [ "python3", "master_node.py" ]