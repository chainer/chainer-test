import groovy.transform.Field

@Field def vm_name = ''

def get_free_slave () {
    def ret = sh (
        script: "python jobs/az_utils.py get-free-slave",
        returnStdout: true
    )
    return ret
}

def setup_docker_dir () {
    sh "python jobs/az_utils.py setup-docker-dir ${vm_name}"
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
                    vm_name = get_free_slave()
                }
            }
        }
        stage ('Mount azure file share') {
            steps {
                script {
                    setup_docker_dir()
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
