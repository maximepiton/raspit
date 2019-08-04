FROM ubuntu:bionic

RUN apt update && apt install -y gcc wget libhdf5-serial-dev netcdf-bin libnetcdf-dev

RUN wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
RUN bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
RUN rm Miniconda3-latest-Linux-x86_64.sh
ENV PATH="/root/miniconda/bin:${PATH}"
RUN conda install -y -c conda-forge netcdf4 wrf-python
RUN pip install --upgrade google-cloud-firestore google-cloud-storage protobuf flask \
    gunicorn click geohash2 flask-cors

RUN apt remove -y gcc wget libnetcdf-dev libhdf5-serial-dev && apt autoremove -y

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

COPY main.py /src/
COPY wsgi.py /src/
WORKDIR /src

CMD gunicorn --bind :$PORT --workers 1 --threads 8 wsgi:app
