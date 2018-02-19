import groovy.transform.Field

@Field def vm_name = ''

def start_test (test) {
    withCredentials([string(credentialsId: 'CHAINER_TEST_COVERALLS_CHAINER_TOKEN', variable: 'coveralls_token')]) {
        sh "python jobs/chainer_master.py --build_id ${BUILD_NUMBER} --test ${test} --vm_name ${vm_name} --coveralls_token ${coveralls_token}"
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
                    sleep 90
                }
            }
        }
        stage ('Mount NFS for Docker dir') {
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
