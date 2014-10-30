#!/usr/bin/python

import locale
import socket
from datetime import datetime
from flask import Flask, render_template


locale.setlocale(locale.LC_ALL, '')
app = Flask(__name__)


STATES = ['OK', 'Warning', 'Critical', 'Unknown']


def query(get, columns=None, filters=None):
    query_string = 'GET %s\n' % get
    if columns:
        query_string += 'Columns: %s\n' % (' '.join(columns))
    for filter_ in filters or ():
        query_string += 'Filter: %s\n' % filter_

    query_string += 'OutputFormat: python\n'
    socket_ = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    socket_.connect('/var/lib/nagios/rw/live')
    socket_.send(query_string.encode('utf-8'))
    socket_.shutdown(socket.SHUT_WR)
    answer_string = ''
    while True:
        part = socket_.recv(1024)
        if not part:
            break
        answer_string += part.decode('utf-8')

    return [
        {columns[i]: item for i, item in enumerate(line)}
        for line in eval(answer_string)]


@app.route('/')
def index():
    hosts = query(get='hosts', columns=('host_name', 'alias'))
    return render_template('index.html.jinja2', hosts=hosts)


@app.route('/status')
@app.route('/status/<host_name>')
def status(host_name=None):
    services = query(
        get='services',
        columns=('host_name', 'host_alias', 'display_name', 'state'),
        filters=('host_name = %s' % host_name,) if host_name else None)
    return render_template(
        'status.html.jinja2', services=services, STATES=STATES)


@app.route('/status/<host_name>/<service>')
def service(host_name, service):
    services = query(
        get='services',
        columns=(
            'host_name', 'host_alias', 'display_name', 'state', 'last_check',
            'plugin_output'),
        filters=('host_name = %s' % host_name, 'display_name = %s' % service))
    return render_template(
        'service.html.jinja2', service=services[0], STATES=STATES)


@app.template_filter('date')
def date(timestamp):
    return datetime.fromtimestamp(timestamp).strftime('%x %X')



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
