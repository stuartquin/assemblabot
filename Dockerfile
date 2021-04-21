FROM python:3.9

RUN mkdir -p /app

ADD requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
WORKDIR /app
ADD bot.py /app/bot.py
ADD cached.py /app/cached.py
ADD assembla.py /app/assembla.py
ADD jira.py /app/jira.py

CMD python bot.py
