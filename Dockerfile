FROM python:3.12-bookworm
LABEL maintainer="email@miklos-szel.com"

# Set non-interactive frontend
ENV DEBIAN_FRONTEND=noninteractive

# Environment variables for configuration
ENV PROXYSQL_HOST=host.docker.internal
ENV PROXYSQL_PORT=16033
ENV PROXYSQL_USER=proxysql_user
ENV ADMIN_USER=proxyweb_admin

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

COPY . /app
RUN cp /app/misc/entry.sh /app/
RUN chmod 755 /app/entry.sh 


#  Install MySQL-client
RUN apt-get update -y && \
    apt-get install -y \
        wget \
        curl \
        ca-certificates \
        debsums \
        libncurses6 \
        libatomic1 \
        libaio1 \
        libnuma1 \
        gnupg \
        lsb-release && \
    wget https://dev.mysql.com/get/Downloads/MySQL-8.4/mysql-common_8.4.5-1debian12_amd64.deb && \
    wget https://dev.mysql.com/get/Downloads/MySQL-8.4/mysql-community-client-plugins_8.4.5-1debian12_amd64.deb && \
    wget https://dev.mysql.com/get/Downloads/MySQL-8.4/mysql-community-client-core_8.4.5-1debian12_amd64.deb && \
    wget https://cdn.mysql.com/Downloads/MySQL-8.4/mysql-community-client_8.4.5-1debian12_amd64.deb && \
    wget https://dev.mysql.com/get/Downloads/MySQL-8.4/mysql-client_8.4.5-1debian12_amd64.deb && \
    dpkg -i \
        mysql-common_8.4.5-1debian12_amd64.deb \
        mysql-community-client-core_8.4.5-1debian12_amd64.deb \
        mysql-community-client-plugins_8.4.5-1debian12_amd64.deb \
        mysql-community-client_8.4.5-1debian12_amd64.deb \
        mysql-client_8.4.5-1debian12_amd64.deb && \
    rm -f *.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*.deb

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/login || exit 1

ENTRYPOINT [ "./entry.sh" ]
CMD [ "app.py" ]

