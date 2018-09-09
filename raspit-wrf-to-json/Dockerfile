FROM ubuntu:bionic

RUN apt update && apt install -y gcc wget

RUN wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
RUN bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
RUN export PATH="$HOME/miniconda/bin:$PATH"
RUN pip install netCDF4
RUN conda install -c conda-forge wrf-python
