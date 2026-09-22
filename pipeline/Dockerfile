# Use python:3.13 as based image
FROM python:3.13

# Set /app folder is working directory
WORKDIR /app

# Install necessary libraries first
# To prevents Docker from rebuilding your entire library cache every time you modify a single line of application code
COPY requirement.txt .
# --no-cache-dir means do not store pip download cache data after installing libraries, to reduce the size of the Image that be built from this Dockerfile
RUN pip install --no-cache-dir -r requirement.txt

# Copy local files and folders of the entire application
COPY . .

# When a Container is started from this Image, this is the default command I want it to execute
CMD ["python", "runpipeline.py"]