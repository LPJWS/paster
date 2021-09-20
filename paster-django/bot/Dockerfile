FROM python:3.8
ENV PYTHONUNBUFFERED 1
ENV C_FORCE_ROOT true
RUN mkdir /bot
WORKDIR /bot
COPY ./requirements.txt /bot/
RUN pip install -r requirements.txt
EXPOSE 8000
EXPOSE 80
COPY . /bot/