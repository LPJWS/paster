FROM python:3.11
ENV PYTHONUNBUFFERED 1
ENV C_FORCE_ROOT true
RUN mkdir /bot_tg
WORKDIR /bot_tg
COPY ./requirements.txt /bot_tg/
RUN pip install -r requirements.txt
EXPOSE 8000
EXPOSE 80
COPY . /bot_tg/