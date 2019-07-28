FROM rasp-wrfv3:latest

ENV BASEDIR=/root/rasp/

WORKDIR /root/

RUN mkdir $BASEDIR/PYR2 && mkdir $BASEDIR/PYR3
RUN cp --preserve=links -r $BASEDIR/region.TEMPLATE/* $BASEDIR/PYR2/ && cp --preserve=links -r $BASEDIR/region.TEMPLATE/* $BASEDIR/PYR3/
COPY PYR2/* $BASEDIR/PYR2/
COPY PYR3/* $BASEDIR/PYR3/
RUN cp $BASEDIR/PYR2/namelist.input $BASEDIR/PYR2/namelist.input.template && cp $BASEDIR/PYR2/namelist.wps $BASEDIR/PYR2/namelist.wps.template
RUN cp $BASEDIR/PYR3/namelist.input $BASEDIR/PYR3/namelist.input.template && cp $BASEDIR/PYR3/namelist.wps $BASEDIR/PYR3/namelist.wps.template
COPY 3dayrun.sh $BASEDIR/
COPY kill_me.sh $BASEDIR/

WORKDIR /root/rasp/

CMD ./3dayrun.sh ; ./kill_me.sh
