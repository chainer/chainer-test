#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sqlite3


parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(dest='cmd')

parser_create_db = subparsers.add_parser('create_table')

parser_get_num_vms = subparsers.add_parser('get_num_vms')
parser_get_free_vm = subparsers.add_parser('get_free_vm')

parser_add_vm = subparsers.add_parser('add_vm')
parser_add_vm.add_argument('--vm_name', '-n', type=str)

parser_stop_vm = subparsers.add_parser('stop_vm')
parser_stop_vm.add_argument('--vm_name', '-n', type=str)

parser_start_vm = subparsers.add_parser('start_vm')
parser_start_vm.add_argument('--vm_name', '-n', type=str)

args = parser.parse_args()

conn = sqlite3.connect('vm.db')
c = conn.cursor()

if args.cmd == 'create_table':
    try:
        c.execute('''
        create table vm (
            id integer primary key autoincrement,
            vm_name text unique,
            running boolean,
            modified_time datetime default current_timestamp
        )''')
    except Exception as e:
        print(str(type(e)), e)    

elif args.cmd == 'get_num_vms':
    c.execute('select count(*) from vm')
    print(c.fetchone()[0])

elif args.cmd == 'get_free_vm':
    c.execute('select count(*) from vm where running = 0')
    num_free_vms = c.fetchone()[0]
    if num_free_vms == 0:
        print('0')
    else:
        c.execute('select vm_name from vm where running = 0')
        print(c.fetchone()[0])

elif args.cmd == 'add_vm':
    c.execute("""
    insert into vm (vm_name, running, modified_time)
    values ('{}', 1, current_timestamp)
    """.format(args.vm_name))

elif args.cmd == 'stop_vm':
    c.execute("""
    update vm set running = 0, modified_time = current_timestamp where vm_name = '{}'
    """.format(args.vm_name))

elif args.cmd == 'start_vm':
    c.execute("""
    update vm set running = 1, modified_time = current_timestamp where vm_name = '{}'
    """.format(args.vm_name))


conn.commit()
conn.close()
