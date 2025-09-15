# Base image
FROM python:3.11

# Maintainer
LABEL org.opencontainers.image.authors="ensembl-webteam@ebi.ac.uk"

# Set Work Directory
WORKDIR /

# Copy source code
COPY ./app /app/
COPY requirements.txt requirements.txt

# Install dependencies
RUN pip install  -r requirements.txt

# Expose Ports
ENV PORT 8001
EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
