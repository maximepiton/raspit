FROM ubuntu:bionic

RUN apt update && apt install -y gcc wget libhdf5-serial-dev netcdf-bin libnetcdf-dev

RUN wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
RUN bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
RUN rm Miniconda3-latest-Linux-x86_64.sh
ENV PATH="/root/miniconda/bin:${PATH}"
RUN conda install -y -c conda-forge netcdf4 wrf-python google-cloud-storage click

RUN conda install -y -c conda-forge google-cloud-sdk

COPY wrf_to_json.py /src/