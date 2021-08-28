FROM alpine

ENV FLASK_APP=app

RUN apk add python3 py3-pip 

COPY src/requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY src /app

EXPOSE 5000

ENTRYPOINT ["flask", "run", "--host=0.0.0.0"]