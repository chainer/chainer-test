#!/usr/bin/env python
# # -*- coding: utf-8 -*-

import json
import re
import subprocess
import argparse

RESOURCE_GROUP = 'chainer-jenkins'
IMAGE_NAME = 'slave-image'
VM_SIZE = 'Standard_NC12'


def run(cmd, silent=False):
    ret = subprocess.check_output(cmd, shell=True)
    ret = ret.decode('utf-8')
    if not silent:
        print('+', cmd)
        print(ret)
    return ret


def run_on_vm(ip, cmd, silent=False):
    cmd = """ \
    ssh -o StrictHostKeyChecking=no \
    jenkins@{ip} \"{cmd}\"
    """.format(ip=ip, cmd=cmd)
    ret = subprocess.check_output(cmd, shell=True)
    ret = ret.decode('utf-8')
    if not silent:
        print('+', cmd)
        print(ret)
    return ret


def get_slaves_list(silent=False):
    cmd = """ \
    az vm list -g {resource_group} --show-details \
    --query \"[?contains(name, 'slave')].[name, powerState]\" \
    -o json
    """.format(
        resource_group=RESOURCE_GROUP
    )
    return json.loads(run(cmd, silent=silent))


def create_vm(name, silent=False):
    cmd = """ \
    az vm create -g {resource_group} -n {name} \
    --image {image_name} --public-ip-address \"\" \
    --admin-username jenkins --generate-ssh-keys \
    --size {vm_size} -o json
    """.format(
        resource_group=RESOURCE_GROUP,
        name=name,
        image_name=IMAGE_NAME,
        vm_size=VM_SIZE,
    )
    return json.loads(run(cmd, silent=silent))


def get_nic_info(nic_name, silent=False):
    cmd = """ \
    az network nic show -n {nic_name} -g {resource_group} -o json
    """.format(nic_name=nic_name, resource_group=RESOURCE_GROUP)
    return json.loads(run(cmd, silent=silent))


def delete_vm(name):
    cmd = """ \
    az vm get-instance-view -g {resource_group} -n {name}
    """.format(resource_group=RESOURCE_GROUP, name=name)
    vm_info = json.loads(run(cmd, silent=True))

    nic_name = vm_info['networkProfile']['networkInterfaces'][0]['id'].split('/')[-1]
    disk_name = vm_info['storageProfile']['osDisk']['name']
    nic_info = get_nic_info(nic_name, silent=True)
    nsg_name = nic_info['networkSecurityGroup']['id'].split('/')[-1]

    run("az vm delete -g {resource_group} -n {name} -y".format(resource_group=RESOURCE_GROUP, name=name))
    run("az disk delete -g {resource_group} -n {disk_name} -y".format(resource_group=RESOURCE_GROUP, disk_name=disk_name))
    run("az network nic delete -g {resource_group} -n {nic_name}".format(
        resource_group=RESOURCE_GROUP, nic_name=nic_name))
    run("az network nsg delete -g {resource_group} -n {nsg_name}".format(
        resource_group=RESOURCE_GROUP, nsg_name=nsg_name))


def deallocate_vm(name, silent=False):
    cmd = """ \
    az vm deallocate -g {resource_group} -n {name} -o json
    """.format(
        resource_group=RESOURCE_GROUP,
        name=name
    )
    return json.loads(run(cmd, silent=silent))


def start_vm(name, silent=False):
    cmd = """ \
    az vm start -g {resource_group} -n {name} -o json
    """.format(
        resource_group=RESOURCE_GROUP,
        name=name
    )
    return json.loads(run(cmd, silent=silent))


def get_vm_ip(name, silent=False):
    cmd = """ \
    az vm list-ip-addresses -g {resource_group} -n {name} \
    --query \"[0].virtualMachine.network.privateIpAddresses[0]\" -o tsv
    """.format(resource_group=RESOURCE_GROUP, name=name)
    return run(cmd, silent=silent).strip()


def get_free_slave(silent=False):
    slaves = get_slaves_list(silent=silent)

    # If there is no created slave VM
    if len(slaves) == 0:
        vm_name = 'slave0'
        create_vm(vm_name, silent=silent)
        return vm_name

    # If there is a deallocated slave VM
    for vm_name, state in slaves:
        if 'deallocated' in state:
            start_vm(vm_name, silent=silent)
            return vm_name

    # If all slave VMs are running
    max_id = max([int(re.search('slave([0-9]+)', n).groups()[0]) for n, _ in slaves])
    vm_name = 'slave' + str(max_id + 1)
    create_vm(vm_name, silent=silent)
    return vm_name


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='cmd')

    parser_get_free_slave = subparsers.add_parser('get-slaves-list')
    parser_get_free_slave = subparsers.add_parser('get-free-slave')

    parser_deallocate_vm = subparsers.add_parser('deallocate-vm')
    parser_deallocate_vm.add_argument('vm_name', type=str)

    paraser_delete_vm = subparsers.add_parser('delete-vm')
    paraser_delete_vm.add_argument('vm_name', type=str)

    parser_get_vm_ip = subparsers.add_parser('get-vm-ip')
    parser_get_vm_ip.add_argument('vm_name', type=str)

    args = parser.parse_args()

    if args.cmd == 'get-slaves-list':
        get_slaves_list()
    elif args.cmd == 'get-free-slave':
        vm_name = get_free_slave(silent=True)
        print(vm_name)
    elif args.cmd == 'deallocate-vm':
        deallocate_vm(args.vm_name)
    elif args.cmd == 'delete-vm':
        delete_vm(args.vm_name)
    elif args.cmd == 'get-vm-ip':
        get_vm_ip(args.vm_name)
