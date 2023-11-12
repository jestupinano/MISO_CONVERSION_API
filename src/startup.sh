#!/bin/bash

# Navigate to your application directory
cd /home/saidnaderm/MISO_CONVERSION_API/docker-web-bucket || {
    echo "Failed to find application directory."
    exit 1
}

# Start your application using Docker Compose
sudo docker compose up || {
    echo "Docker Compose failed to start."
    exit 1
}
