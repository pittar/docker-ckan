# If building all from local environment chage to 
#FROM ckan-base:2.8
FROM ckancontainerreg.azurecr.io/base/ckan-base:2.8.3
MAINTAINER John Kolesar

#Install extra system packages needed by registry

# Set timezone
ARG TZ
RUN echo $TZ > /etc/timezone
RUN cp /usr/share/zoneinfo/$TZ /etc/localtime

# Install any extensions needed by your CKAN instance
# (Make sure to add the plugins to CKAN__PLUGINS in the .env file)
# For instance:
#RUN pip install -e git+https://github.com/ckan/ckanext-pages.git#egg=ckanext-pages && \
#    pip install -e git+https://github.com/ckan/ckanext-dcat.git@v0.0.6#egg=ckanext-dcat && \
#    pip install -r https://raw.githubusercontent.com/ckan/ckanext-dcat/v0.0.6/requirements.txt
RUN . $APP_DIR/bin/activate && cd $APP_DIR/src && \
    pip install PyYAML && \
    pip install ckanapi && \
    pip install geojson && \
    pip install geomet && \
    pip install -e git+https://github.com/aafc-ckan/ckanext-scheming.git#egg=ckanext-scheming && \
    pip install -e git+https://github.com/ckan/ckanext-fluent.git#egg=ckanext-fluent && \
    pip install -e git+https://github.com/aafc-ckan/ckanext-aafc.git#egg=ckanext-aafc && \
    pip install -r https://raw.githubusercontent.com/aafc-ckan/ckanext-aafc/master/requirements.txt && \
    pip install -e git+https://github.com/ckan/ckanext-spatial.git#egg=ckanext-spatial && \
    pip install -r https://raw.githubusercontent.com/ckan/ckanext-spatial/master/pip-requirements.txt && \
    pip install -e git+https://github.com/ckan/ckanext-geoview.git#egg=ckanext-geoview && \
    pip install -r https://raw.githubusercontent.com/ckan/ckanext-geoview/master/pip-requirements.txt

# Update CKAN config with AAFC registry values (Should all be set in the .env file)
RUN . $APP_DIR/bin/activate && cd $APP_DIR/src && \
    paster --plugin=ckan config-tool ${CKAN_INI} ckan.locale_order=${CKAN__LOCALE_ORDER} && \
    paster --plugin=ckan config-tool ${CKAN_INI} ckan.locales_offered=${CKAN__LOCALES_OFFERED} && \
    paster --plugin=ckan config-tool ${CKAN_INI} scheming.dataset_schemas=${CKAN___SCHEMING__DATASET_SCHEMAS} && \
    paster --plugin=ckan config-tool ${CKAN_INI} scheming.presets=${CKAN___SCHEMING__PRESETS} && \
    paster --plugin=ckan config-tool ${CKAN_INI} scheming.dataset_fallback=${CKAN___SCHEMING__DATASET_FALLBACK} && \
    paster --plugin=ckan config-tool ${CKAN_INI} ckan.search.show_all_types=${CKAN__SEARCH__SHOW_ALL_TYPES} && \
    paster --plugin=ckan config-tool ${CKAN_INI} licenses_group_url=${CKAN___LICENSES__GROUP__URL} && \
    paster --plugin=ckan config-tool ${CKAN_INI} ckan.views.default_views=${CKAN__VIEWS__DEFAULT_VIEWS} && \
    paster --plugin=ckan config-tool ${CKAN_INI} ckanext.geoview.ol_viewer.formats=${CKAN___CKANEXT__GEOVIEW__OL_VIEWER__FORMATS} && \
    paster --plugin=ckan config-tool ${CKAN_INI} licenses_group_url=${CKAN___LICENSES_GROUP_URL} && \
    paster --plugin=ckan config-tool ${CKAN_INI} ckan.root_path=${CKAN__ROOT_PATH}


# Install the extension(s) you wrote for your own project
# RUN pip install -e git+https://github.com/your-org/ckanext-your-extension.git@v1.0.0#egg=ckanext-your-extension

# Apply any patches needed to CKAN core or any of the built extensions (not the
# runtime mounted ones)
# See https://github.com/okfn/docker-ckan#applying-patches
COPY patches ${APP_DIR}/patches

RUN for d in $APP_DIR/patches/*; do \
        if [ -d $d ]; then \
            for f in `ls $d/*.patch | sort -g`; do \
                cd $SRC_DIR/`basename "$d"` && echo "$0: Applying patch $f to $SRC_DIR/`basename $d`"; patch -p1 < "$f" ; \
            done ; \
        fi ; \
    done
