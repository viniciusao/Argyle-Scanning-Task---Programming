FROM python:3.8

WORKDIR /opt/argyle_test

COPY . /opt/argyle_test

RUN pip install flit

RUN FLIT_ROOT_INSTALL=1 flit install

ENTRYPOINT python /opt/argyle_test/src/spider.py
