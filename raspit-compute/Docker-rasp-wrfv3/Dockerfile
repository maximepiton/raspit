FROM fedora:25

ENV BASEDIR=/root/rasp

RUN mkdir $BASEDIR

# Required packages
RUN dnf -y update \
  && dnf -y install netcdf-fortran libpng15 iproute-tc tcp_wrappers-libs sendmail procmail psmisc procps-ng mailx \
  findutils ImageMagick perl-CPAN ncl netcdf libpng libjpeg-turbo which patch vim less lftp python

# Configure CPAN and install required modules
RUN (echo y;echo o conf prerequisites_policy follow;echo o conf commit) | cpan \
  && cpan install Proc/Background.pm

# Fix dependencies
RUN ln -s libnetcdff.so.6 /lib64/libnetcdff.so.5 \
  && ln -s libnetcdf.so.11 /lib64/libnetcdf.so.7


WORKDIR /root/

#
# Unpack software packages
# Assuming you have downloaded these files from here: http://rasp-uk.uk/SOFTWARE/WRFV3.x/
#
ADD raspGM.tgz $BASEDIR
ADD raspGM-bin.tgz $BASEDIR
ADD rangs.tgz $BASEDIR

# Patch files with fixes
COPY GM-master.pl.patch /root/
RUN cd $BASEDIR/bin \
  && patch GM-master.pl < ~/GM-master.pl.patch \
  && rm ~/GM-master.pl.patch
ENV PATH="${BASEDIR}/bin:${PATH}"

#
# Google cloud sdk install
#
WORKDIR /root/
RUN curl -o gcsdk.tar.gz https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-215.0.0-linux-x86_64.tar.gz
RUN tar zxvf gcsdk.tar.gz && rm gcsdk.tar.gz
ENV PATH="/root/google-cloud-sdk/bin:${PATH}"

# Cleanup
RUN dnf clean all
RUN rm -rf ~/rasp/GM

CMD ["bash"]
