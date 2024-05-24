# Base image
FROM python:3.11

# Maintainer
LABEL org.opencontainers.image.authors="ensembl-webteam@ebi.ac.uk"

# Set Work Directory
WORKDIR /app

# Copy source code
COPY ./app /app/
COPY requirements.txt requirements.txt
# Install dependencies
RUN pip install  -r requirements.txt

# Expose Ports
ENV PORT 8080
EXPOSE 8080

# Run uvicorn server
CMD ["fastapi", "run", "main.py", "--port", "8080"]

