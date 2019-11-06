FROM python:3.6

RUN mkdir -p /app

ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
WORKDIR /app
ADD bot.py /app/bot.py

CMD python bot.py
