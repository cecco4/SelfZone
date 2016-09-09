echo "init mysql database, please install these dependecies before init:"
echo "  python2.7"
echo "  mysql-server"
echo "  libmysqlclient-dev"
echo "  virtualenv"
read -p "press enter to continue"

echo -e "DROP DATABASE IF EXISTS dbselfzone; CREATE DATABASE dbselfzone;\
\nCREATE USER 'cecco'@'localhost' IDENTIFIED BY 'cecco';\
\nGRANT ALL PRIVILEGES ON dbselfzone.* TO 'cecco'@'localhost' WITH GRANT OPTION;\
\nGRANT ALL PRIVILEGES ON test_dbselfzone.* TO 'cecco'@'localhost' WITH GRANT OPTION; " > init.sql

echo "mysql access"
mysql --user=root -p < init.sql
rm init.sql
echo "sql server created with permission on user: cecco, pwd: cecco"

echo "create virtualenv"
virtualenv -p python2.7 env
echo "enter virtualenv"
source env/bin/activate
echo "install dependencies"
pip install -r requirements.txt

echo "make migrations"
python manage.py makemigrations
echo "migrate"
python manage.py migrate
