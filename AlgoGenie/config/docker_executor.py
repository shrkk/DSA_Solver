from autogen_ext.code_executors.docker import DockerCommandLineCodeExecutor 
from config.constant import TIMEOUT

def get_docker_executor():
    docker_executor = DockerCommandLineCodeExecutor(

        work_dir= 'temp',
        timeout=TIMEOUT
    )
    return docker_executor