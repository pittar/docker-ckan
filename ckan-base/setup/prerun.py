import os
import sys
import subprocess
import psycopg2
import urllib2
import time
import re


ckan_ini = os.environ.get('CKAN_INI', '/srv/app/production.ini')

RETRY = 5

def init_organizations():
    url_is_set = os.environ.get('CKAN_SITE_URL')
    if not url_is_set:
        print '[prerun] CKAN_SITE_URL not defined skipping organization initialization'
        return
    cmd = 'mkdir -p /var/lib/ckan/storage/uploads/groups && \
           cd /var/lib/ckan/storage/uploads/groups && \
           curl https://raw.githubusercontent.com/aafc-ckan/ckanext-aafc/master/imports/group-photos.tar.gz > /var/lib/ckan/storage/uploads/groups/group-photos.tar.gz && \
           tar -xzvf group-photos.tar.gz && \
           rm group-photos.tar.gz && \
           mkdir -p ${APP_DIR}/temp && \
           cd  ${APP_DIR}/temp && \
           curl https://raw.githubusercontent.com/aafc-ckan/ckanext-aafc/master/imports/org_data.json.gz > ${APP_DIR}/temp/org_data.json.gz && \
           gunzip org_data.json.gz && \
           . $APP_DIR/bin/activate && cd $APP_DIR/temp && \
           ckanapi load organizations -I org_data.json -c /${APP_DIR}/production.ini && \
           rm -rf ${APP_DIR}/temp'
    results = subprocess.run(
           cmd, shell=TRUE, universal_newlines=True, check=True)
    print(results.stdout)

def check_main_db_connection(retry=None):

    conn_str = os.environ.get('CKAN_SQLALCHEMY_URL')
    if not conn_str:
        print '[prerun] CKAN_SQLALCHEMY_URL not defined, not checking db'
    return check_db_connection(conn_str, retry)


def check_datastore_db_connection(retry=None):

    conn_str = os.environ.get('CKAN_DATASTORE_WRITE_URL')
    if not conn_str:
        print '[prerun] CKAN_DATASTORE_WRITE_URL not defined, not checking db'
    return check_db_connection(conn_str, retry)


def check_db_connection(conn_str, retry=None):

    if retry is None:
        retry = RETRY
    elif retry == 0:
        print '[prerun] Giving up after 5 tries...'
        sys.exit(1)

    try:
        connection = psycopg2.connect(conn_str)

    except psycopg2.Error as e:
        print str(e)
        print '[prerun] Unable to connect to the database, waiting...'
        time.sleep(10)
        check_db_connection(conn_str, retry=retry - 1)
    else:
        connection.close()


def check_solr_connection(retry=None):

    if retry is None:
        retry = RETRY
    elif retry == 0:
        print '[prerun] Giving up after 5 tries...'
        sys.exit(1)

    url = os.environ.get('CKAN_SOLR_URL', '')
    search_url = '{url}/select/?q=*&wt=json'.format(url=url)
    try:
        connection = urllib2.urlopen(search_url)
    except urllib2.URLError as e:
        print str(e)
        print '[prerun] Unable to connect to solr, waiting...'
        time.sleep(10)
        check_solr_connection(retry=retry - 1)
    else:
        eval(connection.read())


def init_db():

    db_command = ['paster', '--plugin=ckan', 'db',
                  'init', '-c', ckan_ini]
    print '[prerun] Initializing or upgrading db - start'
    try:
        subprocess.check_output(db_command, stderr=subprocess.STDOUT)
        print '[prerun] Initializing or upgrading db - end'
    except subprocess.CalledProcessError, e:
        if 'OperationalError' in e.output:
            print e.output
            print '[prerun] Database not ready, waiting a bit before exit...'
            time.sleep(5)
            sys.exit(1)
        else:
            print e.output
            raise e


def init_datastore_db():

    conn_str = os.environ.get('CKAN_DATASTORE_WRITE_URL')
    if not conn_str:
        print '[prerun] Skipping datastore initialization'
        return

    datastore_perms_command = ['paster', '--plugin=ckan', 'datastore',
                               'set-permissions', '-c', ckan_ini]

    connection = psycopg2.connect(conn_str)
    cursor = connection.cursor()

    print '[prerun] Initializing datastore db - start'
    try:
        datastore_perms = subprocess.Popen(
            datastore_perms_command,
            stdout=subprocess.PIPE)

        perms_sql = datastore_perms.stdout.read()
        print perms_sql
        # Remove internal pg command as psycopg2 does not like it
        perms_sql = re.sub('\\\\connect \"(.*)\"', '', perms_sql)
        # Strip the fully qualified Postgresql user name for database script"
#        perms_sql = re.sub('(%40([^"]|"")*")', '"', perms_sql)
        perms_sql = perms_sql.replace("ckan%40isb-postgresql-ckan-dev","ckan")
        perms_sql = perms_sql.replace("datastore_ro%40isb-postgresql-ckan-dev","datastore_ro")
        print perms_sql
        cursor.execute(perms_sql)
        for notice in connection.notices:
            print notice

        connection.commit()

        print '[prerun] Initializing datastore db - end'
        print datastore_perms.stdout.read()
    except psycopg2.Error as e:
        print '[prerun] Could not initialize datastore'
        print str(e)

    except subprocess.CalledProcessError, e:
        if 'OperationalError' in e.output:
            print e.output
            print '[prerun] Database not ready, waiting a bit before exit...'
            time.sleep(5)
            sys.exit(1)
        else:
            print e.output
            raise e
    finally:
        cursor.close()
        connection.close()


def create_sysadmin():

    name = os.environ.get('CKAN_SYSADMIN_NAME')
    password = os.environ.get('CKAN_SYSADMIN_PASSWORD')
    email = os.environ.get('CKAN_SYSADMIN_EMAIL')

    if name and password and email:

        # Check if user exists
        command = ['paster', '--plugin=ckan', 'user', name, '-c', ckan_ini]

        out = subprocess.check_output(command)
        if 'User:None' not in re.sub(r'\s', '', out):
            print '[prerun] Sysadmin user exists, skipping creation'
            return

        # Create user
        command = ['paster', '--plugin=ckan', 'user', 'add',
                   name,
                   'password=' + password,
                   'email=' + email,
                   '-c', ckan_ini]

        subprocess.call(command)
        print '[prerun] Created user {0}'.format(name)

        # Make it sysadmin
        command = ['paster', '--plugin=ckan', 'sysadmin', 'add',
                   name,
                   '-c', ckan_ini]

        subprocess.call(command)
        print '[prerun] Made user {0} a sysadmin'.format(name)


if __name__ == '__main__':

    maintenance = os.environ.get('MAINTENANCE_MODE', '').lower() == 'true'

    if maintenance:
        print '[prerun] Maintenance mode, skipping setup...'
    else:
        check_main_db_connection()
        check_datastore_db_connection()
        check_solr_connection()
        init_db()
        init_datastore_db()
        create_sysadmin()
        init_organizations()
