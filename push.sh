tar cvfz web.tar.gz web
scp web.tar.gz root@example.com:/var/www/
ssh root@example.com "cd /var/www && tar -xvf web.tar.gz --transform 's|^web/|fall_colors/|'"