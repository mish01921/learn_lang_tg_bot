# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set the working directory in the container
WORKDIR /app

# Create a non-root user for security
RUN groupadd -r botgroup && useradd -r -g botgroup -d /app -s /sbin/nologin botuser

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Upgrade pip and install needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Change ownership of /app to non-root user
RUN chown -R botuser:botgroup /app

# Switch to non-root user
USER botuser

# Run src/main.py when the container launches
CMD ["python", "src/main.py"]