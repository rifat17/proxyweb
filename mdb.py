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


import mysql.connector
import logging
import yaml
import subprocess
import os
from datetime import datetime

# Custom exceptions for better error handling
class ProxyWebError(Exception):
    """Base exception for ProxyWeb"""
    pass

class ConfigError(ProxyWebError):
    """Configuration related errors"""
    pass

class DatabaseError(ProxyWebError):
    """Database connection and query errors"""
    pass

class ValidationError(ProxyWebError):
    """Input validation errors"""
    pass

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

sql_get_databases = "show databases"
sql_show_table_content = "select * from %s.%s order by 1;"
sql_show_tables = "show tables from %s;"

def validate_sql(sql):
    """Basic SQL validation to prevent dangerous operations"""
    if not sql or not sql.strip():
        raise ValidationError("SQL query cannot be empty")
    
    sql_upper = sql.upper().strip()
    
    # Block dangerous operations
    dangerous_patterns = [
        'DROP ', 'TRUNCATE ', 'DELETE FROM mysql_', 'ALTER ', 'CREATE USER',
        'GRANT ', 'REVOKE ', 'FLUSH ', 'SHUTDOWN', 'KILL ', '--', '/*', '*/',
        'UNION SELECT', 'INFORMATION_SCHEMA', 'MYSQL.USER'
    ]
    
    for pattern in dangerous_patterns:
        if pattern in sql_upper:
            raise ValidationError(f"Dangerous SQL operation detected: {pattern}")
    
    # Limit query length
    if len(sql) > 5000:
        raise ValidationError("SQL query too long (max 5000 characters)")
    
    return sql.strip()

def get_config(config="config/config.yml"):
    logging.debug("Using file: %s" % (config))
    try:
        with open(config, 'r') as yml:
            cfg = yaml.safe_load(yml)
        if not cfg:
            raise ConfigError(f"Config file {config} is empty or invalid")
        
        # Override with environment variables
        _apply_env_overrides(cfg)
        return cfg
    except FileNotFoundError:
        raise ConfigError(f"Config file not found: {config}")
    except yaml.YAMLError as e:
        raise ConfigError(f"YAML parsing error in {config}: {str(e)}")
    except Exception as e:
        raise ConfigError(f"Error reading config file {config}: {str(e)}")

def _apply_env_overrides(cfg):
    """Apply environment variable overrides to configuration"""
    # Database connection overrides
    if 'PROXYSQL_HOST' in os.environ:
        cfg['servers']['proxysql']['dsn'][0]['host'] = os.environ['PROXYSQL_HOST']
    if 'PROXYSQL_PORT' in os.environ:
        cfg['servers']['proxysql']['dsn'][0]['port'] = os.environ['PROXYSQL_PORT']
    if 'PROXYSQL_USER' in os.environ:
        cfg['servers']['proxysql']['dsn'][0]['user'] = os.environ['PROXYSQL_USER']
    if 'PROXYSQL_PASSWORD' in os.environ:
        cfg['servers']['proxysql']['dsn'][0]['passwd'] = os.environ['PROXYSQL_PASSWORD']
    
    # Authentication overrides
    if 'ADMIN_USER' in os.environ:
        cfg['auth']['admin_user'] = os.environ['ADMIN_USER']
    if 'ADMIN_PASSWORD' in os.environ:
        cfg['auth']['admin_password'] = os.environ['ADMIN_PASSWORD']
    
    # Flask secret key override
    if 'SECRET_KEY' in os.environ:
        cfg['flask']['SECRET_KEY'] = os.environ['SECRET_KEY']


def db_connect(db, server, autocommit=False, buffered=False, dictionary=True):
    try:
        db['cnf'] = get_config()
        
        if server not in db['cnf']['servers']:
            raise DatabaseError(f"Server '{server}' not found in configuration")
        
        if 'dsn' not in db['cnf']['servers'][server] or not db['cnf']['servers'][server]['dsn']:
            raise DatabaseError(f"No DSN configuration found for server '{server}'")

        config = db['cnf']['servers'][server]['dsn'][0]
        logging.debug(db['cnf']['servers'][server]['dsn'][0])
        
        db['cnf']['servers'][server]['conn'] = mysql.connector.connect(
            **config, raise_on_warnings=True, get_warnings=True, connection_timeout=3
        )

        if db['cnf']['servers'][server]['conn'].is_connected():
            logging.debug("Connected successfully to %s as %s db=%s" % (
                config['host'], config['user'], config['db']))

        db['cnf']['servers'][server]['conn'].autocommit = autocommit
        db['cnf']['servers'][server]['conn'].get_warnings = True

        db['cnf']['servers'][server]['cur'] = db['cnf']['servers'][server]['conn'].cursor(
            buffered=buffered, dictionary=dictionary)
        logging.debug("buffered: %s, dictionary: %s, autocommit: %s" % (buffered, dictionary, autocommit))

    except mysql.connector.Error as e:
        raise DatabaseError(f"MySQL connection error for server '{server}': {str(e)}")
    except KeyError as e:
        raise ConfigError(f"Missing configuration key for server '{server}': {str(e)}")


def get_all_dbs_and_tables(db, server):
    all_dbs = {server: {}}
    try:

        db_connect(db, server=server)
        db['cnf']['servers'][server]['cur'].execute(sql_get_databases)
        table_exception_list = []

        if 'hide_tables' not in db['cnf']['servers'][server]:
            #it there is a global hide_tables defined and there is no local one:
            if len(db['cnf']['global']['hide_tables']) > 0:
                table_exception_list = db['cnf']['global']['hide_tables']
        else:
                table_exception_list = db['cnf']['servers'][server]['hide_tables']

        for i in db['cnf']['servers'][server]['cur'].fetchall():

            all_dbs[server][i['name']] = []

            db['cnf']['servers'][server]['cur'].execute(sql_show_tables % i['name'])
            for table in db['cnf']['servers'][server]['cur'].fetchall():
                # hide tables as per global or per server config
                if table['tables'] not in table_exception_list:
                    all_dbs[server][i['name']].append(table['tables'])
        db['cnf']['servers'][server]['cur'].close()
        return all_dbs
    except (mysql.connector.Error, mysql.connector.Warning) as e:
        raise DatabaseError(f"Database error: {str(e)}")
    finally:
        try:
            if 'cur' in db['cnf']['servers'][server]:
                db['cnf']['servers'][server]['cur'].close()
        except:
            pass


def get_table_content(db, server, database, table):
    '''returns with a dict with two keys "column_names" = list and  rows = tuples '''
    content = {}
    try:
        logging.debug("server: {} - db: {} - table:{}".format(server, database, table))
        db_connect(db, server=server, dictionary=False)
        data = (database, table)

        string = (sql_show_table_content % data)
        logging.debug("query: {}".format(string))

        db['cnf']['servers'][server]['cur'].execute(string)

        content['rows'] = db['cnf']['servers'][server]['cur'].fetchall()
        content['column_names'] = [i[0] for i in db['cnf']['servers'][server]['cur'].description]
        content['misc'] = get_config()['misc']
        return content
    except (mysql.connector.Error, mysql.connector.Warning) as e:
        raise DatabaseError(f"Database error getting table content: {str(e)}")
    finally:
        try:
            if 'conn' in db['cnf']['servers'][server]:
                db['cnf']['servers'][server]['conn'].close()
        except:
            pass

def process_table_content(table, content):
    """
    Processes content rows by converting time-based fields to UTC datetime strings.
    """
    # Define time-based fields and their units
    time_fields = {
        'first_seen': 's',
        'last_seen': 's',
        'time_start_us': 'us',
        'success_time_us': 'us'
    }

    # Get indices for the target columns
    col_names = content.get('column_names', [])
    field_indices = {field: idx for field, unit in time_fields.items() if field in col_names for idx, name in enumerate(col_names) if name == field}

    if field_indices:
        new_rows = []
        for row in content.get('rows', []):
            row = list(row)  # Convert tuple to list for mutation
            for field, idx in field_indices.items():
                try:
                    value = int(row[idx])
                    if time_fields[field] == 'us':
                        # Convert microseconds to seconds
                        value /= 1_000_000
                    row[idx] = datetime.utcfromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError, OverflowError):
                    # Leave the value as is if it's invalid
                    pass
            new_rows.append(tuple(row))  # Convert back to tuple
        content['rows'] = new_rows

    return content

def execute_adhoc_query(db, server, sql):
    '''returns with a dict with two keys "column_names" = list and  rows = tuples '''
    content = {}
    try:
        sql = validate_sql(sql)
        logging.debug("server: {} - sql: {}".format(server, sql))
        db_connect(db, server=server, dictionary=False)

        logging.debug("query: {}".format(sql))

        db['cnf']['servers'][server]['cur'].execute(sql)

        content['rows'] = db['cnf']['servers'][server]['cur'].fetchall()
        content['column_names'] = [i[0] for i in db['cnf']['servers'][server]['cur'].description]

        return content
    except (mysql.connector.Error, mysql.connector.Warning) as e:
        raise DatabaseError(f"Database error executing query: {str(e)}")
    except ValidationError:
        raise
    finally:
        try:
            if 'conn' in db['cnf']['servers'][server]:
                db['cnf']['servers'][server]['conn'].close()
        except:
            pass

def execute_adhoc_report(db, server):
    '''returns with a dict with two keys "column_names" = list and  rows = tuples '''
    adhoc_results = []
    result = {}
    try:
        db_connect(db, server=server, dictionary=False)

        config = get_config()
        if 'adhoc_report' in config['misc']:
            for item in config['misc']['adhoc_report']:
                logging.debug("query: {}".format(item))
                db['cnf']['servers'][server]['cur'].execute(item['sql'])

                result['rows'] = db['cnf']['servers'][server]['cur'].fetchall()
                result['title'] = item['title']
                result['sql'] = item['sql']
                result['info'] = item['info']
                result['column_names'] = [i[0] for i in db['cnf']['servers'][server]['cur'].description]
                adhoc_results.append(result.copy())
        else:
            pass

        return adhoc_results
    except (mysql.connector.Error, mysql.connector.Warning) as e:
        raise DatabaseError(f"Database error executing report: {str(e)}")
    finally:
        try:
            if 'conn' in db['cnf']['servers'][server]:
                db['cnf']['servers'][server]['conn'].close()
        except:
            pass


def get_servers():
    try:
        servers_dict = get_config()
        if 'servers' not in servers_dict:
            raise ConfigError("No 'servers' section found in configuration")
        return list(servers_dict['servers'].keys())
    except ConfigError:
        raise
    except Exception as e:
        raise ConfigError(f"Cannot get server list from config file: {str(e)}")

def get_read_only(server):
    try:
        config = get_config()
        if server not in config['servers']:
            raise ConfigError(f"Server '{server}' not found in configuration")
        
        if 'read_only' not in config['servers'][server]:
            if 'global' in config and 'read_only' in config['global']:
                return config['global']['read_only']
            else:
                return False  # Default to read-write
        else:
            return config['servers'][server]['read_only']
    except ConfigError:
        raise
    except Exception as e:
        raise ConfigError(f"Cannot get read_only status for server '{server}': {str(e)}")



def execute_change(db, server, sql):
    try:
        sql = validate_sql(sql)
        # this is a temporary solution as using the  mysql.connector for certain writes ended up with weird results, ProxySQL
        # is not a MySQL server after all. We're investigating the issue.
        db_connect(db, server=server, dictionary=False)
        logging.debug(sql)
        logging.debug(server)
        dsn = get_config()['servers'][server]['dsn'][0]
        cmd = ('mysql -h{} -P{} -u{} -p{} -e "{}"'.format(
            dsn['host'], dsn['port'], dsn['user'], dsn['passwd'], sql))
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            return "ERROR: " + result.stderr
        else:
            return result.stdout
            
    except ValidationError as e:
        return f"VALIDATION ERROR: {str(e)}"
    except DatabaseError as e:
        return f"DATABASE ERROR: {str(e)}"
    except Exception as e:
        return f"ERROR: {str(e)}"
    finally:
        try:
            db['cnf']['servers'][server]['conn'].close()
        except:
            pass

