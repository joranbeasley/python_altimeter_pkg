import os

import configparser

def load_config_dict(fname="/boot/software_ui.conf"):
    parser = configparser.ConfigParser()
    parser.read(fname)
    data = dict(parser.iteritems())
    for d in data:
        data[d] = dict(data[d].iteritems())
    return data

def load_ui_config(fname="/boot/software_ui.conf"):
    data = load_config_dict(fname)
    data.setdefault('csv',{})['output'] = [s.strip() for s in data['csv'].get('output').split(",")]
    data.setdefault('chart',{})['enabled'] = data['chart'].get('enabled','1') != '0'
    data.setdefault('gps',{})['chart'] = data['gps'].get('chart',"toggle")
    data.setdefault('gps', {})['display_height'] = data['gps'].get('display_height', "0") != "0"
    return data
