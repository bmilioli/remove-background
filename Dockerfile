FROM ubuntu:22.04

RUN ln -fs /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime
RUN apt update \
 && apt upgrade -y \
 && apt-get install -y wget \
 && apt install curl -y

WORKDIR /app

RUN apt install -y -q build-essential python3-pip python3-dev

RUN pip3 install -U pip setuptools wheel

RUN pip3 install gunicorn uvloop httptools

COPY requirements.txt /app/requirements.txt

RUN pip3 install -r /app/requirements.txt
		

COPY ./ /app
ENV YDEVD_DISABLE_FILE_VALIDATION=1
ENV PYARROW_IGNORE_TIMEZONE=1

EXPOSE 80
EXPOSE 4041

CMD gunicorn main:app \
    -w 4 \
    --timeout 0 \
    -b 0.0.0.0:80 \
    --graceful-timeout 0 \
    -k uvicorn.workers.UvicornWorker

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]