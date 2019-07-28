FROM ubuntu:bionic

RUN apt update && apt install -y gcc wget libhdf5-serial-dev netcdf-bin libnetcdf-dev

RUN wget https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh
RUN bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda
RUN rm Miniconda3-latest-Linux-x86_64.sh
ENV PATH="/root/miniconda/bin:${PATH}"
RUN conda install -y -c conda-forge netcdf4 wrf-python click
RUN pip install --upgrade google-cloud-firestore google-cloud-storage protobuf

RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list &&\
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - &&\
    apt-get update && apt-get -y install google-cloud-sdk

ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

COPY kill_me.sh /src/
COPY wrf_to_json.py /src/
WORKDIR /src

CMD python wrf_to_json.py ; ./kill_me.sh
