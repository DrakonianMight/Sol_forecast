FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY ./app.py /app/
COPY ./om_extract.py /app/
COPY ./siteList.csv /app/
COPY ./requirements.txt /app/
COPY ./.streamlit /app/.streamlit

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit with proper configuration
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.fileWatcherType=none"]
