# Selfzone
Selfzone is a image ranking online platform

#### Set up enviroment
execute the script "init_database.sh" or follow the coming steps

##### Dependencies
Check your mysql DBMS, then install dependencies; on Debian:
~~~bash
apt install python2.7 mysql-server libmysqlclient-dev virtualenv
~~~

##### Prepare DBMS
this project uses mysql, so you have to enable all privileges
to your user.
From terminal log as admin in mysql and execute this commands
~~~mysql
DROP DATABASE IF EXISTS dbselfzone; CREATE DATABASE dbselfzone;
CREATE USER 'cecco'@'localhost' IDENTIFIED BY 'cecco';
GRANT ALL PRIVILEGES ON dbselfzone.* TO 'cecco'@'localhost' WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON test_dbselfzone.* TO 'cecco'@'localhost' WITH GRANT OPTION;
~~~

##### Virtualenv
For avoid version errors is recommended to use virtualenv
~~~bash
virtualenv -p python2.7 env
source env/bin/activate
~~~

##### Requirements
Install python requirements for the project
~~~bash
pip install -r requirements.txt
~~~

##### Build database
~~~bash
python manage.py makemigrations
python manage.py migrate
~~~

##### Start server
~~~bash
python manage.py runserver 8000
~~~