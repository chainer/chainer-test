import groovy.transform.Field
import groovy.json.JsonSlurperClassic
import groovy.json.JsonOutput

@Field def resource_group = 'chainer-jenkins'
@Field def vm_name = ''
@Field def storage_account = 'slavedata'
@Field def image_name ='slave-image'
@Field def key_path = '/home/jenkins/.ssh/id_rsa.pub'
@Field def secret_key_path = '/home/jenkins/.ssh/id_rsa'
@Field def vm_size = 'Standard_NC12'
@Field def ip = ''

def get_vm_name_list () {
    def res = sh (
        script: "az vm list -g ${resource_group} --query \"[].name\"",
        returnStdout: true
    )
    return res
}

def get_nic_info (nic_name) {
    def res = sh (
        script: "az network nic show -n ${nic_name} -g ${resource_group}",
        returnStdout: true
    )
    return new groovy.json.JsonSlurperClassic().parseText(res)
}

def get_vm_ips () {
    def res = sh (
        script: "az vm list-ip-addresses -g ${resource_group} --query \"[].[virtualMachine.name, virtualMachine.network.privateIpAddresses[0]]\" -o json",
        returnStdout: true
    )
    return new groovy.json.JsonSlurperClassic().parseText(res)
}

def get_vm_ip (name) {
    echo "Get IP of VM: ${name}"
    def res = sh (
        script: "az vm list-ip-addresses -g ${resource_group} -n ${name} --query \"[0].virtualMachine.network.privateIpAddresses[0]\" -o tsv",
        returnStdout: true
    )
    return res.replaceAll("[\r\n]+", "")
}

def create_vm (name) {
    echo "Creating VM: ${name}"
    sh  "az vm create -g ${resource_group} -n ${name} --image ${image_name} --public-ip-address \"\" --admin-username jenkins --ssh-key-value ${key_path} --size ${vm_size}"
    ip = get_vm_ip(vm_name)
    replace_docker_dir(ip)
}

def start_vm (name) {
    echo "Starting VM: ${name}"
    sh "az vm start -g ${resource_group} -n ${name}"

    sleep 60
}

def delete_vm (name) {
    echo "Deleting VM: ${name}"
    def res = sh (
        script: "az vm get-instance-view -g ${resource_group} -n ${name}",
        returnStdout: true
    )
    def vm_info = new groovy.json.JsonSlurperClassic().parseText(res)
    def nic_name = vm_info.networkProfile.networkInterfaces[0].id.split('/')[-1]
    def disk_name = vm_info.storageProfile.osDisk.name
    def nic = get_nic_info(nic_name)
    // def public_ip_name = nic.ipConfigurations[0].publicIpAddress.id.split('/')[-1]
    def nsg_name = nic.networkSecurityGroup.id.split('/')[-1]

    echo "Deleting VM: ${name}"
    sh "az vm delete -g ${resource_group} -n ${name} -y"
    echo "Deleting disk: ${disk_name}"
    sh "az disk delete -g ${resource_group} -n ${disk_name} -y"
    echo "Deleting nic: ${nic_name}"
    sh "az network nic delete -g ${resource_group} -n ${nic_name}"
    echo "Deleting nsg: ${nsg_name}"
    sh "az network nsg delete -g ${resource_group} -n ${nsg_name}"
    // sh "az network public-ip delete -g ${resource_group} -n ${public_ip_name}"
}

def deallocate_vm (name) {
    echo "Deallocating VM: ${name}"
    sh "az vm deallocate -g ${resource_group} -n ${name}"
}

def get_slave_state () {
    def res = sh (
        script: "az vm list -g ${resource_group} --show-details --query \"[?contains(name, 'slave')].[name, powerState]\"",
        returnStdout: true
    )
    return new groovy.json.JsonSlurperClassic().parseText(res)
}

def get_free_slaves () {
    def res = sh (
        script: "az vm list -g ${resource_group} --show-details --query \"[?contains(name, 'slave') && contains(powerState, 'deallocated')].[name, powerState]\"",
        returnStdout: true
    )
    return new groovy.json.JsonSlurperClassic().parseText(res)
}

def run_cmd_hidden (ip, cmd) {
    sh "set +x && ssh -o StrictHostKeyChecking=no -i ${secret_key_path} jenkins@${ip} ${cmd}"
}

def run_cmd (ip, cmd) {
    sh "ssh -o StrictHostKeyChecking=no -i ${secret_key_path} jenkins@${ip} ${cmd}"
}

def replace_docker_dir (ip) {
    echo "Replacing docker dir"
    def key = sh (
        script: "az storage account keys list -g ${resource_group} -n ${storage_account} --query \"[0].value\" -o tsv",
        returnStdout: true
    )
    key = key.trim()

    run_cmd(ip, "sudo nvidia-smi -pm 1")
    run_cmd(ip, "sudo nvidia-smi")

    run_cmd(ip, "\"if [ ! -d /mnt/data ]; then sudo mkdir /mnt/data; fi\"")
    run_cmd_hidden(ip, "\"sudo mount -t cifs //slavedata.file.core.windows.net/docker-cache /mnt/data -o vers=3.0,username=${storage_account},password=${key},dir_mode=0777,file_mode=0777,sec=ntlmssp,mfsymlinks\"")
    run_cmd(ip, "\"if [ ! -d /mnt/data/docker ]; then sudo mkdir /mnt/data/docker; fi\"")
    run_cmd(ip, "sudo service docker stop")
    run_cmd(ip, "sudo rm -rf /var/lib/docker")
    run_cmd(ip, "sudo ln -s /mnt/data/docker /var/lib/docker")
    run_cmd(ip, "\"if ! grep -q 'devicemapper' /lib/systemd/system/docker.service; then sudo sed -E -i \"s/dockerd/dockerd --storage-driver=devicemapper/g\" /lib/systemd/system/docker.service; fi\"")
    run_cmd(ip, "sudo systemctl daemon-reload")
    run_cmd(ip, "sudo service docker start")

    run_cmd(ip, "sudo docker images")
}

def start_test(test) {
    script {
        run_cmd(ip, "\"rm -rf ${test} && mkdir ${test} && cd ${test} && git clone -b gules https://github.com/mitmul/chainer-test.git && cd chainer-test && git clone -b master https://github.com/chainer/chainer.git && ./run_test.py --test ${test} --coveralls-repo=chainer --coveralls-branch=master --clone-cupy\"")
    }
}

pipeline {
    agent {
        label 'master'
    }
    stages {
        stage ('Allocate VM') {
            steps {
                script {
                    def vm_list = get_vm_name_list()
                    def slave_list = vm_list.findAll('slave[0-9]+')
                    def free_slaves = get_free_slaves()
                    // If no slave exists
                    if (slave_list?.empty) {
                        vm_name = 'slave0'
                        create_vm(vm_name)
                    }
                    // If there are slaves but no deallocated slaves
                    else if (free_slaves.size() == 0) {
                        // Increment the last slave ID
                        def slave_ids = slave_list.join('').findAll { it =~ /([0-9]+)/ }
                        def max_id = slave_ids.collect { it.toInteger() }.max()
                        vm_name = 'slave' + (max_id + 1)
                        create_vm(vm_name)
                    }
                    // If there is a free slave
                    else {
                        start_vm(free_slaves[0][0])
                        vm_name = free_slaves[0][0]
                    }
                }
            }
        }
        stage ('Mount azure file share') {
            steps {
                script {
                    ip = get_vm_ip(vm_name)
                    replace_docker_dir(ip)
                }
            }
        }
        stage ('Run tests') {
            steps {
                parallel (
                    'chainer-py2': {
                        start_test('chainer-py2')
                    },
                    'chainer-py3': {
                        start_test('chainer-py3')
                    },
                    'chainer-py35': {
                        start_test('chainer-py35')
                    },
                    'chainer-example': {
                        start_test('chainer-example')
                    },
                    'chainer-prev_example': {
                        start_test('chainer-prev_example')
                    },
                    'chainer-doc': {
                        start_test('chainer-doc')
                    }
                )
            }
        }
    }
    post {
        always {
            deallocate_vm(vm_name)
        }
        success {
            echo 'Success'
        }
        failure {
            echo 'Failure'
        }
    }
}