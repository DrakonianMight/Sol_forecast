FROM python:3.10
ENV DASH_DEBUG_MODE True

COPY ./app.py /app.py
COPY ./assets /assets
COPY ./siteList.csv /siteList.csv
COPY ./om_extract.py /om_extract.py
COPY ./requirements.txt /requirements.txt

WORKDIR /

RUN set -ex && \
    pip install -r requirements.txt
EXPOSE 8050
CMD ["python", "app.py"]