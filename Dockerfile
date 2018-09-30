FROM python:2.7.13-slim

RUN apt-get update -y && apt-get install telnet -y
RUN pip install lxml urllib3 pymongo

WORKDIR /opt/investing_scrapping
ADD *.py /opt/investing_scrapping/
ADD *.ini /opt/investing_scrapping/
