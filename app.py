#!/usr/bin/python3

""" ProxyWeb - A Proxysql Web user interface

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""

__author__ = "Miklos Mukka Szel"
__contact__ = "email@miklos-szel.com"
__license__ = "GPLv3"

import logging
from collections import defaultdict
from flask import Flask, render_template, request, session, url_for, flash, redirect
from functools import wraps
import re
import mdb

app = Flask(__name__)

config = "config/config.yml"


db = defaultdict(lambda: defaultdict(dict))

# read/apply the flask config from the config file
flask_custom_config = mdb.get_config(config)
for key in flask_custom_config['flask']:
    app.config[key] = flask_custom_config['flask'][key]


mdb.logging.debug(flask_custom_config)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('You must be logged in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()
    message=""
    admin_user = mdb.get_config(config)['auth']['admin_user']
    admin_password = mdb.get_config(config)['auth']['admin_password']

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if admin_user == username and admin_password == password:
            session['logged_in'] = True
            return redirect(url_for('render_list_dbs'))
        message="Invalid credentials!"
    return render_template("login.html", message=message)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def render_list_dbs():
    try:
        server = mdb.get_config(config)['global']['default_server']
        session['history'] = []
        session['server'] = server
        session['dblist'] = mdb.get_all_dbs_and_tables(db, server)
        session['servers'] = mdb.get_servers()
        session['read_only'] = mdb.get_read_only(server)
        session['misc'] = mdb.get_config(config)['misc']

        return render_template("list_dbs.html", server=server)
    except Exception as e:
        raise ValueError(e)

@app.route('/<server>/')
@app.route('/<server>/<database>/<table>/')
@login_required
def render_show_table_content(server, database="main", table="global_variables"):
    try:
        # refresh the tablelist if changing to a new server

        if server not in session['dblist']:
            session['dblist'].update(mdb.get_all_dbs_and_tables(db, server))

        session['servers'] = mdb.get_servers()
        session['server'] = server
        session['table'] = table
        session['database'] = database
        session['misc'] = mdb.get_config(config)['misc']
        session['read_only'] = mdb.get_read_only(server)
        content = mdb.get_table_content(db, server, database, table)
        mdb.process_table_content(table,content)
        return render_template("show_table_info.html", content=content)
    except Exception as e:
        raise ValueError(e)

@app.route('/<server>/<database>/<table>/sql/', methods=['GET', 'POST'])
@login_required
def render_change(server, database, table):
    try:
        error = ""
        message = ""
        ret = ""
        
        # Validate SQL input
        raw_sql = request.form.get("sql", "").strip()
        if not raw_sql:
            error = "SQL query cannot be empty"
            content = mdb.get_table_content(db, server, database, table)
            return render_template("show_table_info.html", content=content, error=error)
        
        session['sql'] = raw_sql


        mdb.logging.debug(session['history'])
        select = re.match(r'^SELECT.*FROM.*$', session['sql'], re.M | re.I)
        if select:
            content = mdb.execute_adhoc_query(db, server, session['sql'])
            content['order'] = 'true'
        else:
            ret = mdb.execute_change(db, server, session['sql'])
            content = mdb.get_table_content(db, server, database, table)

        if "ERROR" in ret:
            error = ret
        else:
            message = "Success"
        if session['sql'].replace("\r\n","") not in session['history'] and not error:
            session['history'].append(session['sql'].replace("\r\n",""))

        return render_template("show_table_info.html", content=content, error=error, message=message)
    except Exception as e:
        raise ValueError(e)

@app.route('/<server>/adhoc/')
@login_required
def adhoc_report(server):
    try:

        adhoc_results = mdb.execute_adhoc_report(db, server)
        return render_template("show_adhoc_report.html", adhoc_results=adhoc_results)
    except Exception as e:
        raise ValueError(e)


@app.route('/settings/<action>/', methods=['GET', 'POST'])
@login_required
def render_settings(action):
    try:
        config_file_content = ""
        message = ""
        if action == 'edit':
            with open(config, "r") as f:
                config_file_content = f.read()
        if action == 'save':
            # back it up first
            with open(config, "r") as src, open(config + ".bak", "w") as dest:
                dest.write(src.read())

            with open(config, "w") as f:
                f.write(request.form["settings"])
            message = "success"
        return render_template("settings.html", config_file_content=config_file_content, message=message)
    except Exception as e:
        raise ValueError(e)


@app.errorhandler(Exception)
def handle_exception(e):
    print(e)
    return render_template("error.html", error=e), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', use_debugger=False)
