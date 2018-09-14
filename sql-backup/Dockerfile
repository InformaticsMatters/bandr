FROM python:3.7.0-alpine3.8

ENV APP_ROOT /code
ENV HOME /root
WORKDIR ${APP_ROOT}

# Install stuff including PostgreSQL and MySQL clients
RUN apk add --no-cache \
        mysql-client \
        openssh \
        postgresql-client \
        rsync \
        sshpass \
        tzdata && \
    rm -rf /var/cache/apk/*
# Set the Alpine image timezone...
ENV TZ=UTC

# Populate the image...
COPY backup.py ${APP_ROOT}/
COPY pgpass ${HOME}/.pgpass
RUN chmod 755 ${APP_ROOT}/backup.py && \
    chmod 600 ${HOME}/.pgpass && \
    mkdir ${HOME}/.ssh && \
    chmod 700 ${HOME}/.ssh

# Force the binary layer of the stdout and stderr streams
# to be unbuffered
ENV PYTHONUNBUFFERED 1

CMD [ "./backup.py" ]
