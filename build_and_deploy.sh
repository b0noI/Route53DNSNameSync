#!/bin/bash
# Script to stop, remove, and restart the route53-updater container

# Exit immediately if a command exits with a non-zero status
set -e

# --- Configuration ---
CONTAINER_NAME="route53-updater-daemon"
IMAGE_NAME="route53-updater"
ENV_FILE=".env" # Assuming your environment variables are in .env

# --- Script Logic ---

docker build -t "${IMAGE_NAME}" .

echo "Checking for existing container named '${CONTAINER_NAME}'..."

# Get the ID of the container if it exists (running or stopped)
# Using -q (quiet) only prints the ID if found
container_id=$(docker ps -a --filter "name=${CONTAINER_NAME}" -q)

# Check if the container_id variable is not empty
if [ -n "$container_id" ]; then
  echo "Container '${CONTAINER_NAME}' found (ID: $container_id)."

  # Stop the container if it's running
  # docker stop is graceful; will exit immediately if already stopped
  echo "Attempting to stop container ${CONTAINER_NAME}..."
  # Redirect output and error to /dev/null and use || true
  # so the script doesn't exit if stop fails because it's already stopped
  docker stop "$container_id" > /dev/null 2>&1 || true
  echo "Stop command sent."

  # Remove the container
  echo "Removing container ${CONTAINER_NAME}..."
  docker rm "$container_id"
  echo "Container removed successfully."
else
  echo "No existing container named '${CONTAINER_NAME}' found. Proceeding with run."
fi

echo "Starting new container '${CONTAINER_NAME}'..."

# Run the new container in detached mode (-d)
# Load environment variables from the .env file
# Set the container name
# Set the restart policy
docker run -d \
  --env-file "${ENV_FILE}" \
  --restart unless-stopped \
  --name "${CONTAINER_NAME}" \
  "${IMAGE_NAME}"

echo "Container '${CONTAINER_NAME}' started."
echo "Use 'docker ps -f name=${CONTAINER_NAME}' to check status."
echo "Use 'docker logs -f ${CONTAINER_NAME}' to view logs."

exit 0
