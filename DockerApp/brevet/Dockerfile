FROM python:3
MAINTAINER Andrew Werderman "awerderm@uoregon.edu"
RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential
COPY . /brevet
WORKDIR /brevet
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["flask_app.py"]