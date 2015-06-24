FROM centos:7

RUN yum -y update
RUN yum -y install gcc python-devel
RUN curl -kL https://raw.github.com/pypa/pip/master/contrib/get-pip.py | python

RUN pip install numpy
