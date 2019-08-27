FROM alpine:3.7

# Internals, you probably don't need to change these
ENV APP_DIR=/srv/app
ENV SRC_DIR=/srv/app/src
ENV CKAN_INI=${APP_DIR}/production.ini
ENV PIP_SRC=${SRC_DIR}
ENV CKAN_STORAGE_PATH=/var/lib/ckan
ENV GIT_URL=https://github.com/ckan/ckan.git
# CKAN version to build
ENV GIT_BRANCH=ckan-2.8.3
# Customize these on the .env file if needed
ENV CKAN_SITE_URL=${CKAN_SITE_URL}
#ENV CKAN_SITE_URL=http://localhost:5000
ENV CKAN__PLUGINS=${CKAN__PLUGINS}

WORKDIR ${APP_DIR}

# Install necessary packages to run CKAN
RUN apk add --no-cache tzdata \
        git \
        gettext \
#        postgresql-client \
               python \
        apache2-utils \
        libxml2 \
        libxslt \
        musl-dev \
        uwsgi \
        uwsgi-http \
        uwsgi-corerouter \
        uwsgi-python \
        py2-gevent \
        uwsgi-gevent \
        libmagic \
        curl \
        sudo && \
    # Packages to build CKAN requirements and plugins
    apk add --no-cache --virtual .build-deps \
#        postgresql-dev \
#	postgresql-client \
        gcc \
        make \
        g++ \
        autoconf \
        automake \
	libtool \
        python-dev \
        libxml2-dev \
        libxslt-dev \
        linux-headers && \
    # Create SRC_DIR
    mkdir -p ${SRC_DIR} && \
    # Install pip, supervisord and uwsgi
    curl -o ${SRC_DIR}/get-pip.py https://bootstrap.pypa.io/get-pip.py && \
    python ${SRC_DIR}/get-pip.py && \
    pip install pastescript && \
    pip install pastedeploy && \
    pip install supervisor && \
    mkdir /etc/supervisord.d && \
    pip install virtualenv && \
    #pip wheel --wheel-dir=/wheels uwsgi gevent && \
    rm -rf ${SRC_DIR}/get-pip.py

RUN virtualenv ${APP_DIR} && \
    ln -s ${APP_DIR}/bin/pip /usr/local/bin/ckan-pip && \
    ln -s ${APP_DIR}/bin/paster /usr/local/bin/ckan-paster

RUN echo "@postgres_latest http://dl-cdn.alpinelinux.org/alpine/v3.7/main/" >> /etc/apk/repositories && \
    apk add --update --no-cache postgresql-dev@postgres_latest postgresql-client@postgres_latest
    
RUN echo "@testing http://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories && \
    apk add --update --no-cache geos@testing geos-dev@testing py3-geos@testing

COPY setup/supervisord.conf /etc

# Install CKAN
RUN . ${APP_DIR}/bin/activate && cd ${APP_DIR}/src && \
    pip install -e git+${GIT_URL}@${GIT_BRANCH}#egg=ckan && \
    cd ${SRC_DIR}/ckan && \
    cp who.ini ${APP_DIR} && \
    # Workaround to solve https://github.com/psycopg/psycopg2/issues/594 in Alpine 3.7
#	sed -i -e "s/psycopg2==2.4.5/psycopg2==2.7.3.2/g" requirements.txt && \
    pip install --no-binary :all: -r requirements.txt && \
    pip install gevent

    # Install CKAN envvars to support loading config from environment variables
RUN . ${APP_DIR}/bin/activate && cd ${APP_DIR}/src && \
    pip install -e git+https://github.com/okfn/ckanext-envvars.git#egg=ckanext-envvars && \
    # Create and update CKAN config
    paster --plugin=ckan make-config ckan ${CKAN_INI} && \
    paster --plugin=ckan config-tool ${CKAN_INI} "ckan.plugins = ${CKAN__PLUGINS}" && \
    paster --plugin=ckan config-tool ${CKAN_INI} "ckan.site_url = ${CKAN_SITE_URL}"

# Create a local user and group to run the app
RUN addgroup -g 92 -S ckan && \
    adduser -u 92 -h /srv/app -H -D -S -G ckan ckan

# Create local storage folder
RUN mkdir -p $CKAN_STORAGE_PATH && \
    chown -R ckan:ckan $CKAN_STORAGE_PATH

# Copy Azure public Postgresql cert
RUN mkdir -p ${APP_DIR}/.postgresql && \
    chown -R ckan:ckan ${APP_DIR}
COPY setup/root.crt ${APP_DIR}/.postgresql/root.crt

COPY setup ${APP_DIR}
COPY setup/supervisor.worker.conf /etc/supervisord.d/worker.conf
COPY setup/uwsgi.conf /srv/app/uwsgi.conf

# Create entrypoint directory for children image scripts
ONBUILD RUN mkdir /docker-entrypoint.d

RUN chown -R ckan:ckan /srv/app

EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=5s --retries=5 CMD curl --fail http://localhost:5000/api/3/action/status_show || exit 1

CMD ["/srv/app/start_ckan.sh"]
