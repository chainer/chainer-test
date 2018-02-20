import groovy.transform.Field

@Field def vm_name = ''

def start_test (test, gpu_id=0) {
    ansiColor('xterm') {
        withCredentials([string(credentialsId: 'CHAINER_TEST_COVERALLS_CHAINER_TOKEN', variable: 'coveralls_token')]) {
            sh "python jobs/chainer_master.py --coveralls_token ${coveralls_token} --gpu-id ${gpu_id} --build_id ${BUILD_NUMBER} --test ${test} --vm_name ${vm_name}"
        }
    }
}

def try_ssh (name) {
    def ip = sh (script: "python jobs/az_utils.py get-vm-ip ${name}", returnStdout: true)
    ip = ip.trim()
    for (int i = 0; i < 3; i++) {
        catchError {
            sh "echo ${i}"
            sh "ssh -o StrictHostKeyChecking=no jenkins@${ip} ls"
        }
        sleep 5
    }
}

pipeline {
    agent {
        label 'master'
    }
    stages {
        stage ('Clone Azure utils') {
            steps {
                git url: 'https://github.com/mitmul/chainer-test.git', branch: 'jenkins-script'
            }
        }
        stage ('Allocate VM') {
            steps {
                script {
                    vm_name = sh (
                        script: "python jobs/az_utils.py get-free-slave",
                        returnStdout: true
                    )
                    try_ssh(vm_name)
                }
            }
        }
        stage ('Setup Docker dir') {
            steps {
                script {
                    sh "python jobs/az_utils.py setup-docker-dir ${vm_name}"
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
                        start_test('chainer-example', 0)
                    },
                    'chainer-prev_example': {
                        start_test('chainer-prev_example', 1)
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
            sh "python jobs/az_utils.py deallocate-vm ${vm_name}"
        }
        success {
            echo 'Success'
        }
        failure {
            echo 'Failure'
        }
    }
} 
