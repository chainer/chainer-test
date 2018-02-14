#!/usr/bin/env python
# # -*- coding: utf-8 -*-

import json
import re
import subprocess
import argparse

RESOURCE_GROUP = 'chainer-jenkins'
STORAGE_ACCOUNT = 'slavedata'
IMAGE_NAME = 'slave-image'
PUBLIC_KEY_PATH = '/home/jenkins/.ssh/id_rsa.pub'
SECRET_KEY_PATH = '/home/jenkins/.ssh/id_rsa'
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
    ssh -i {secret_key_path} -o StrictHostKeyChecking=no \
    jenkins@{ip} \"{cmd}\"
    """.format(secret_key_path=SECRET_KEY_PATH, ip=ip, cmd=cmd)
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
    --admin-username jenkins --ssh-key-value {public_key_path} \
    --size {vm_size} -o json
    """.format(
        resource_group=RESOURCE_GROUP,
        name=name,
        image_name=IMAGE_NAME,
        public_key_path=PUBLIC_KEY_PATH,
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


def setup_docker_dir(ip):
    cmd = """ \
    az storage account keys list -g {resource_group} \
    -n {storage_account} --query \"[0].value\" -o tsv
    """.format(
        resource_group=RESOURCE_GROUP,
        storage_account=STORAGE_ACCOUNT
    )
    key = run(cmd, silent=True).strip()

    run_on_vm(ip, 'sudo nvidia-smi -pm 1')
    run_on_vm(ip, 'sudo nvidia-smi')
    run_on_vm(ip, 'if [ ! -d /mnt/data ]; then sudo mkdir /mnt/data; fi')
    run_on_vm(ip, "sudo mount -t cifs //slavedata.file.core.windows.net/docker-cache /mnt/data -o vers=3.0,username={storage_account},password={key},dir_mode=0777,file_mode=0777,sec=ntlmssp,mfsymlinks".format(
        storage_account=STORAGE_ACCOUNT, key=key), silent=True)
    run_on_vm(ip, "if [ ! -d /mnt/data/docker ]; then sudo mkdir /mnt/data/docker; fi")
    run_on_vm(ip, "sudo service docker stop")
    run_on_vm(ip, "sudo rm -rf /var/lib/docker")
    run_on_vm(ip, "sudo ln -s /mnt/data/docker /var/lib/docker")
    run_on_vm(ip, "if ! grep -q 'devicemapper' /lib/systemd/system/docker.service; then sudo sed -E -i \"s/dockerd/dockerd --storage-driver=devicemapper/g\" /lib/systemd/system/docker.service; fi")
    run_on_vm(ip, "sudo systemctl daemon-reload")
    run_on_vm(ip, "sudo service docker start")
    run_on_vm(ip, "sudo docker images")


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

    parser_setup_docker_dir = subparsers.add_parser('setup-docker-dir')
    parser_setup_docker_dir.add_argument('vm_name', type=str)

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
    elif args.cmd == 'setup-docker-dir':
        ip = get_vm_ip(args.vm_name)
        setup_docker_dir(ip)
    elif args.cmd == 'deallocate-vm':
        deallocate_vm(args.vm_name)
    elif args.cmd == 'delete-vm':
        delete_vm(args.vm_name)
    elif args.cmd == 'get-vm-ip':
        get_vm_ip(args.vm_name)
