# Use official Python image
FROM python:3.10-slim

# Install system packages required to build dlib and other dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-all-dev \
    python3-dev \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy all project files into the container
COPY . .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Collect static files (optional, for Django)
RUN python manage.py collectstatic --noinput || true

# Start the Django server using gunicorn
CMD ["gunicorn", "attendance_system.wsgi:application", "--bind", "0.0.0.0:8000"]
