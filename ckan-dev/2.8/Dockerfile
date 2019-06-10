FROM ckan-base:2.8

MAINTAINER John Kolesar

ENV APP_DIR=/srv/app
ENV SRC_EXTENSIONS_DIR=/srv/app/src_extensions

# Install packages needed by the dev requirements
RUN apk add --no-cache libffi-dev

# Install CKAN dev requirements
RUN . $APP_DIR/bin/activate && cd $APP_DIR/src && \
    pip install --no-binary :all: -r https://raw.githubusercontent.com/ckan/ckan/${GIT_BRANCH}/dev-requirements.txt

# Create folder for local extensions sources
RUN mkdir $SRC_EXTENSIONS_DIR

COPY setup/start_ckan_development.sh ${APP_DIR}


CMD ["/srv/app/start_ckan_development.sh"]
