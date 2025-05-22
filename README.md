# ProxyWeb
Open Source Web UI for [ProxySQL](https://proxysql.com/)

> [!WARNING]  
> Basic authentication is turned on by default in the latest version, default creds are admin/admin42, can be changed by editing the config file.


![ProxyWeb ui](misc/images/ProxyWeb_main.jpg)


**Current features include**:
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
- Basic authentication



# Setup

## Install ProxyWeb next to ProxySQL
With Docker:
```
docker run -h proxyweb --name proxyweb --network="host" -d proxyweb/proxyweb:latest
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

or

git clone https://github.com/miklos-szel/proxyweb.git
cd proxyweb
make  proxyweb-run
```

Visit [http://ip_of_the_host:5000/setting/edit](http://ip_of_the_host:5000/setting/edit) first and edit the `servers`
section.

---




### Features on the roadmap
- ability to edit tables
- more advanced input validation
---
### Credits:

Thanks for Rene Cannao and the SysOwn team for the wonderful [ProxySQL](https://proxysql.com/).

ProxyWeb is using the following projects:
- Percona Server 5.7
- Bootstrap 4.4.1
- Mdbootstrap 4.16
- Font Awesome 5.8.2
- Google Fonts
- goss
- sysbench 

