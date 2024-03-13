# use one of the images from this repository: https://github.com/centreborelli/ipol-docker-images/
FROM registry.ipol.im/ipol:v1-py3.9

# copy the code to $bin
ENV bin /workdir/bin
RUN mkdir -p $bin
WORKDIR $bin
COPY . .

WORKDIR $bin/meaningfulscaleDemo
RUN cmake CMakeLists.txt
RUN make
WORKDIR $bin/meaningfulscaleDemo/bin 
RUN cp pgm2freeman $bin
WORKDIR $bin/meaningfulscaleDemo/demoIPOL
RUN cp meaningfulScaleEstim transformBG.sh $bin

# the execution will happen in the folder /workdir/exec
# it will be created by IPOL

# some QoL tweaks
ENV PYTHONDONTWRITEBYTECODE 1
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION python
ENV PATH $bin:$PATH

# $HOME is writable by the user `ipol`, but 
ENV HOME /home/ipol
# chmod 777 so that any user can use the HOME, in case the docker is run with -u 1001:1001
RUN groupadd -g 1000 ipol && useradd -m -u 1000 -g 1000 ipol -d $HOME && chmod -R 777 $HOME
RUN apt-get update && apt-get install -y ghostscript
USER ipol