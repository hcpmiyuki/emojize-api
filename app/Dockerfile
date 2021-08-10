FROM ubuntu:latest

# mecabとmecab-ipadic-NEologdの導入
RUN apt-get update \
    && apt-get install -y mecab \
    && apt-get install -y libmecab-dev \
    && apt-get install -y mecab-ipadic-utf8 \
    && apt-get install -y git \
    && apt-get install -y make \
    && apt-get install -y curl \
    && apt-get install -y xz-utils \
    && apt-get install -y file \
    && apt-get install -y sudo \
    && apt-get install -y python3.7 \
    && apt-get install -y python3-pip

RUN git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git \
    && cd mecab-ipadic-neologd \
    && bin/install-mecab-ipadic-neologd -n -y

RUN echo "dicdir=/usr/lib/x86_64-linux-gnu/mecab/dic/mecab-ipadic-neologd">/etc/mecabrc

WORKDIR /app

ADD ./app/ /app/

RUN pip3 install --upgrade pip && \
  pip3 install -r requirements.txt

EXPOSE 8080

CMD gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b :8080 --timeout 900