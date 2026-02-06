FROM python:3.10

COPY ./app.py /app.py
COPY ./assets /assets
COPY ./siteList.csv /siteList.csv
COPY ./om_extract.py /om_extract.py
COPY ./requirements.txt /requirements.txt
COPY ./.streamlit /.streamlit

WORKDIR /

RUN set -ex && \
    pip install -r requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501", "--server.headless", "true"]