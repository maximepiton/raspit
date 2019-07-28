FROM ubuntu:bionic

RUN apt update && apt install -y gcc wget libhdf5-serial-dev netcdf-bin libnetcdf-dev

RUN wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
RUN bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
RUN rm Miniconda3-latest-Linux-x86_64.sh
ENV PATH="/root/miniconda/bin:${PATH}"
RUN conda install -y -c eklitzke google-cloud-datastore google-cloud-storage  
RUN conda install -y -c conda-forge netcdf4 wrf-python click

WORKDIR /root/
RUN curl -o gcsdk.tar.gz https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-215.0.0-linux-x86_64.tar.gz
RUN tar zxvf gcsdk.tar.gz && rm gcsdk.tar.gz
ENV PATH="/root/google-cloud-sdk/bin:${PATH}"

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

COPY kill_me.sh /src/
COPY wrf_to_json.py /src/
WORKDIR /src

CMD python wrf_to_json.py ; ./kill_me.sh
