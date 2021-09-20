FROM python:3.8
ENV PYTHONUNBUFFERED 1
ENV C_FORCE_ROOT true
RUN mkdir /site
WORKDIR /site
RUN rm -f /site/celerybeat.pid
COPY ./requirements.txt /site/
RUN pip install -r requirements.txt
EXPOSE 8000
EXPOSE 80
COPY . /site/