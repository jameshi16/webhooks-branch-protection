FROM ubuntu:bionic
SHELL ["/bin/bash", "-c"]
RUN apt-get update && apt-get full-upgrade -y && apt-get install -y apache2 libapache2-mod-wsgi-py3 python3-pip git
RUN echo $'<VirtualHost *> \n\
    ServerName branch-protection \n\
    WSGIScriptAlias / /var/www/branch-protection/branch-protection.wsgi \n\
    <Directory /var/www/branch-protection> \n\
        Order deny,allow \n\
        Allow from all \n\
    </Directory> \n\
</VirtualHost>' > /etc/apache2/sites-available/000-default.conf
COPY --chown=www-data:www-data *.py /var/www/branch-protection/
COPY --chown=www-data:www-data branch-protection.wsgi /var/www/branch-protection/branch-protection.wsgi
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt
RUN touch /var/www/branch-protection/config.json && mkdir /var/.ssh
RUN echo $'#!/bin/bash \n\
service apache2 start \n\
mkdir -p /home/www-data \n\
cp -r /var/.ssh /var/www/.ssh \n\
chown -R www-data:www-data /var/www/.ssh \n\
tail -f /var/log/apache2/error.log /var/log/apache2/other_vhosts_access.log' > /var/start_script.sh
RUN chmod +x /var/start_script.sh
ENTRYPOINT /var/start_script.sh
