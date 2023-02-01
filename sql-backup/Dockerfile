FROM python:3.10.9-slim-buster

ENV APP_ROOT /code
ENV HOME /root
WORKDIR ${APP_ROOT}

# Install core packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gnupg \
        lsb-release \
        openssh-client \
        rsync \
        s3fs \
        sshpass \
        tzdata \
        wget
# Install database client.
# At PostgreSQL 13 we concounter problems with LOCALE when re-creating the DB.
# The v13 backup creates the SQL (containing the LACALE option) but the v12 server
# (being restored to) does not. Consequently we stop at v12, whcih _should_ be
# able to restore to a v13+ server.
#
# For a discussion of the promlem see https://stackoverflow.com/questions/66052693
RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' && \
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    apt-get update && \
    apt-get -y install \
        postgresql-client-12

# Set the image timezone...
ENV TZ=UTC

# Populate the image...
RUN /usr/local/bin/python -m pip install --upgrade pip && \
    pip install boto3==1.14.32

COPY backup.py ${APP_ROOT}/
COPY docker-entrypoint.sh ${APP_ROOT}/
COPY pgpass ${HOME}/.pgpass
RUN chmod 755 ${APP_ROOT}/*.py && \
    chmod 755 ${APP_ROOT}/*.sh && \
    chmod 600 ${HOME}/.pgpass && \
    mkdir ${HOME}/.ssh && \
    chmod 700 ${HOME}/.ssh

# Force the binary layer of the stdout and stderr streams
# to be unbuffered
ENV PYTHONUNBUFFERED 1

CMD [ "./docker-entrypoint.sh" ]
