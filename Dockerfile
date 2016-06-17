FROM debian:jessie
MAINTAINER dustyfresh, https://github.com/dustyfresh
RUN apt-get update && apt-get install --yes vim less build-essential python-setuptools python-pip python-dev supervisor curl mongodb-server libgeoip1 libgeoip-dev
RUN mkdir -pv /data/db /opt/honeypress/logs
RUN ln -s /data/db /opt/honeypress/db
ADD src/templates /opt/honeypress/templates
ADD src/config.py /opt/honeypress/config.py
ADD src/honeypress.py /opt/honeypress/honeypress.py
ADD src/requirements.txt /opt/honeypress/requirements.txt
RUN pip install -r /opt/honeypress/requirements.txt && chmod +x /opt/honeypress/honeypress.py
ADD conf/supervise-honeypress.conf /etc/supervisor/conf.d/supervise-honeypress.conf
ADD conf/supervise-mongod.conf /etc/supervisor/conf.d/supervise-mongod.conf
CMD ["/usr/bin/supervisord", "-n"]
