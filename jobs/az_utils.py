#!/usr/bin/env python
# # -*- coding: utf-8 -*-

import argparse
import json
import os
import re
import subprocess

RESOURCE_GROUP = ''
IMAGE_NAME = ''
VM_SIZE = ''


def run(cmd, silent=False):
    ret = subprocess.check_output(cmd, shell=True)
    ret = ret.decode('utf-8')
    if not silent:
        print('+', cmd)
        print(ret)
    return ret


def run_on_vm(name, cmd, silent=False):
    cmd = """ \
    ssh -o StrictHostKeyChecking=no \
    jenkins@{name} \"{cmd}\"
    """.format(name=name, cmd=cmd)
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
    ret = json.loads(run(cmd, silent=silent))

    cmd = """ \
    az disk create -g {resource_group} -n {name} --size-gb 512 --sku Standard_LRS
    """.format(
        resource_group=RESOURCE_GROUP,
        name=name,
    )
    run(cmd, silent=silent)

    cmd = """ \
    az vm disk attach -g {resource_group} --disk {name} --vm-name {name}
    """.format(
        resource_group=RESOURCE_GROUP,
        name=name,
    )
    run(cmd, silent=silent)

    with open('make_partition.sh', 'w') as fp:
        fp.write(""" \
        #!/bin/sh
        echo \"n
        p
        l


        w
        \" | sudo fdisk /dev/sdc
        sudo mkfs.ext4 /dev/sdc
        sudo mkdir /cache
        sudo mount -t ext4 /dev/sdc /cache
        sudo chown -R jenkins:jenkins /cache
        echo "/dev/sdc  /cache  ext4    defaults,nofail 0   0" | sudo tee -a /etc/fstab
        """)
    run("rm -rf ~/.ssh/known_hosts", silent=silent)
    run("scp -o StrictHostKeyChecking=no make_partition.sh {name}:/home/jenkins".format(name=name), silent=silent)
    run_on_vm(name, "sh make_partition.sh", silent=silent)

    return ret


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
    run("az disk delete -g {resource_group} -n {disk_name} -y".format(
        resource_group=RESOURCE_GROUP, disk_name=disk_name))
    run("az disk delete -g {resource_group} -n {name} -y".format(
        resource_group=RESOURCE_GROUP, name=name))
    run("az network nic delete -g {resource_group} -n {nic_name}".format(
        resource_group=RESOURCE_GROUP, nic_name=nic_name))
    run("az network nsg delete -g {resource_group} -n {nsg_name}".format(
        resource_group=RESOURCE_GROUP, nsg_name=nsg_name))


def deallocate_vm(name, silent=False):
    cmd = """ \
    az vm deallocate -g {resource_group} -n {name} -o json
    """.format(
        resource_group=RESOURCE_GROUP,
        name=name,
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


def get_vm_ip(name, silent=False, resource_group=None):
    if resource_group is None:
        resource_group = RESOURCE_GROUP
    cmd = """ \
    az vm list-ip-addresses -g {resource_group} -n {name} \
    --query \"[0].virtualMachine.network.privateIpAddresses[0]\" -o tsv
    """.format(resource_group=resource_group, name=name)
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


def setup_docker_dir(name, storage_driver):
    os.remove('/home/jenkins/.ssh/known_hosts')
    run_on_vm(name, 'sudo nvidia-smi -pm 1', silent=True)
    run_on_vm(name, "sudo service docker stop", silent=True)
    run_on_vm(name, "sudo rm -rf /var/lib/docker", silent=True)
    run_on_vm(name, "if [ ! -d /cache/docker ]; then sudo mkdir -p /cache/docker; fi", silent=True)
    run_on_vm(name, "sudo ln -s /cache/docker /var/lib/docker", silent=True)
    run_on_vm(name, "sudo sed -i -E 's/ --storage-driver=\w+//g' /lib/systemd/system/docker.service", silent=True)
    run_on_vm(
        name, "sudo sed -i -E 's/dockerd/dockerd --storage-driver={sd}/g' /lib/systemd/system/docker.service".format(
            sd=storage_driver), silent=True)
    run_on_vm(name, "sudo systemctl daemon-reload", silent=True)
    run_on_vm(name, "sudo service docker start", silent=True)
    run_on_vm(name, "sudo docker images")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--resource-group', '-g', type=str, default='chainer-jenkins')
    parser.add_argument('--image', '-n', type=str, default='slave-image')
    parser.add_argument('--size', '-s', type=str, default='Standard_NC12')

    subparsers = parser.add_subparsers(dest='cmd')

    parser_get_free_slave = subparsers.add_parser('get-slaves-list')
    parser_get_free_slave = subparsers.add_parser('get-free-slave')

    parser_setup_docker_dir = subparsers.add_parser('setup-docker-dir')
    parser_setup_docker_dir.add_argument('vm_name', type=str)
    parser_setup_docker_dir.add_argument('--storage-driver', '-d', type=str, default='overlay2')

    parser_create_vm = subparsers.add_parser('create-vm')
    parser_create_vm.add_argument('vm_name', type=str)

    parser_deallocate_vm = subparsers.add_parser('deallocate-vm')
    parser_deallocate_vm.add_argument('vm_name', type=str)

    paraser_delete_vm = subparsers.add_parser('delete-vm')
    paraser_delete_vm.add_argument('vm_name', type=str)

    parser_get_vm_ip = subparsers.add_parser('get-vm-ip')
    parser_get_vm_ip.add_argument('vm_name', type=str)

    args = parser.parse_args()

    RESOURCE_GROUP = args.resource_group
    IMAGE_NAME = args.image
    VM_SIZE = args.size

    if args.cmd == 'get-slaves-list':
        get_slaves_list()
    elif args.cmd == 'get-free-slave':
        vm_name = get_free_slave(silent=True)
        print(vm_name)
    elif args.cmd == 'setup-docker-dir':
        setup_docker_dir(args.vm_name, args.storage_driver)
    elif args.cmd == 'create-vm':
        create_vm(args.vm_name)
    elif args.cmd == 'deallocate-vm':
        deallocate_vm(args.vm_name)
    elif args.cmd == 'delete-vm':
        delete_vm(args.vm_name)
    elif args.cmd == 'get-vm-ip':
        get_vm_ip(args.vm_name)
