# ProxyWeb
Open Source Web UI for [ProxySQL](https://proxysql.com/)

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Setup](#setup)
  - [Install ProxyWeb next to ProxySQL](#install-proxyweb-next-to-proxysql)
  - [Install it as a systemd service (Ubuntu)](#install-it-as-a-systemd-service-ubuntu)
  - [Install ProxyWeb to work with remote ProxySQL servers](#install-proxyweb-to-work-with-remote-proxysql-servers)


![ProxyWeb ui](misc/images/ProxyWeb_main.jpg)

## Introduction
ProxyWeb is a modern, lightweight web-based interface for ProxySQL, the popular high-performance MySQL proxy. Designed for simplicity and full control, ProxyWeb allows administrators to manage ProxySQL servers, users, query rules, and variables—all through an intuitive web UI.

## Features:
- Clean and responsive design
- [Multi-server support](misc/images/ProxyWeb_servers.jpg)
- [Configurable reporting](misc/images/ProxyWeb_report.jpg)
- Global and per-server options
- Hide unused tables (global or per-server basis)
- Sort content by any column (asc/desc)
- Online config editor
- Narrow-down content search
- Paginate content
- Command history and SQL dropdown menu 
- Adhoc MySQL queries
- **Enhanced Security Features**:
  - SQL injection protection
  - Input validation and sanitization
  - Dangerous operation blocking
  - Secure authentication
- **Environment Variable Configuration**
- **Docker Health Checks**
- **Improved Error Handling**


# Setup

## Prerequisites

- Docker installed on your system
- Git installed
- Basic understanding of ProxySQL and MySQL

## Install ProxyWeb next to ProxySQL

### Quick Start with Docker:
```bash
docker run -h proxyweb --name proxyweb --network="host" -d proxyweb/proxyweb:latest
```

### Secure Installation with Environment Variables:
```bash
# Create environment file
cp .env.example .env
# Edit .env with your credentials

# Run with custom configuration
docker run -h proxyweb --name proxyweb --network="host" \
  -e PROXYSQL_PASSWORD="your_secure_password" \
  -e ADMIN_PASSWORD="your_admin_password" \
  -e SECRET_KEY="your_random_secret_key" \
  -d proxyweb/proxyweb:latest

# Or use environment file
docker run -h proxyweb --name proxyweb --network="host" \
  --env-file .env -d proxyweb/proxyweb:latest
```
## Install it as a systemd service (Ubuntu)
```
git clone https://github.com/miklos-szel/proxyweb
cd proxyweb
make install
```
Visit  [http://ip_of_the_host:5000/setting/edit](http://ip_of_the_host:5000/setting/edit) first and adjust the credentials if needed.
The default connection is the local one with the default credentials.


## Install ProxyWeb to work with remote ProxySQL servers
### Configure ProxySQL for remote admin access

ProxySQL only allows local admin connections by default.

In order to enable remote connections you have to enable it in ProxySQL:

```
set admin-admin_credentials="admin:admin;radmin:radmin";
load admin variables to runtime; save admin variables to disk;
```

After this we can connect to the ProxySQL with:
- username: radmin
- password: radmin
- port: 6032 (default)

Run:
```
docker run -h proxyweb --name proxyweb -p 5000:5000 -d proxyweb/proxyweb:latest
```

Visit [http://ip_of_the_host:5000/setting/edit](http://ip_of_the_host:5000/setting/edit) first and edit the `servers`
section.

## Environment Variables

ProxyWeb supports configuration via environment variables for secure deployment:

| Variable | Description | Default |
|----------|-------------|----------|
| `PROXYSQL_HOST` | ProxySQL server hostname | `host.docker.internal` |
| `PROXYSQL_PORT` | ProxySQL server port | `16033` |
| `PROXYSQL_USER` | ProxySQL username | `proxysql_user` |
| `PROXYSQL_PASSWORD` | ProxySQL password | *Required* |
| `ADMIN_USER` | Web interface username | `proxyweb_admin` |
| `ADMIN_PASSWORD` | Web interface password | *Required* |
| `SECRET_KEY` | Flask secret key | *Required* |

### Example .env file:
```bash
PROXYSQL_HOST=localhost
PROXYSQL_PORT=6032
PROXYSQL_USER=radmin
PROXYSQL_PASSWORD=your_secure_password
ADMIN_USER=admin
ADMIN_PASSWORD=your_admin_password
SECRET_KEY=your_random_secret_key_here
```

## Security

⚠️ **Important Security Notes:**
- **Change default credentials** before deployment
- **Use strong passwords** for both ProxySQL and web interface
- **Generate a random SECRET_KEY** for Flask sessions
- **Use environment variables** instead of hardcoded credentials
- ProxyWeb includes **SQL injection protection** and **input validation**

---

## Recent Improvements

- ✅ **Enhanced Security**: SQL injection protection, input validation, dangerous operation blocking
- ✅ **Environment Variable Support**: Secure configuration management
- ✅ **Docker Health Checks**: Container monitoring and reliability
- ✅ **Improved Error Handling**: Specific exceptions and better debugging
- ✅ **Stable Python Version**: Production-ready Python 3.12

### Features on the roadmap
- Connection pooling for better performance
- Rate limiting and CSRF protection
- Table editing capabilities
- Advanced query builder
- Audit logging

---
### Credits:

- Thanks for René Cannaò and the SysOwn team  [ProxySQL](https://proxysql.com/).
- Tripolszky 'Tripy' Zsolt


