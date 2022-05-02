import logging
from threading import Event

from common.aws.aws_instance import AwsInstance
from common.aws.aws_service import AwsService
from common.cmd.aws.aws_cmd_runner import AwsCmdRunner
from common.cmd.cmd import Cmd
from common.cmd.cmd_runner import CmdRunner

logger = logging.getLogger(__name__)
AWS_INFO_FETCH_TIMEOUT = 10  # Seconds
aws_info_fetch_done = Event()


class RemoteRunAwsService:
    aws_instance = None

    def __init__(self):
        pass

    @staticmethod
    def init():
        """
        Initializes service. Subsequent calls to this function have no effect.
        Must be called at least once (in entire monkey lifetime) before usage of functions
        :return: None
        """
        if RemoteRunAwsService.aws_instance is None:
            RemoteRunAwsService.aws_instance = AwsInstance()
            aws_info_fetch_done.set()

    @staticmethod
    def run_aws_monkeys(instances, island_ip):
        """
        Runs monkeys on the given instances
        :param instances: List of instances to run on
        :param island_ip: IP of island the monkey will communicate with
        :return: Dictionary with instance ids as keys, and True/False as values if succeeded or not
        """
        return CmdRunner.run_multiple_commands(
            instances,
            lambda instance: RemoteRunAwsService._run_aws_monkey_cmd_async(
                instance["instance_id"],
                RemoteRunAwsService._is_linux(instance["os"]),
                island_ip,
            ),
            lambda _, result: result.is_success,
        )

    @staticmethod
    def is_running_on_aws():
        aws_info_fetch_done.wait(AWS_INFO_FETCH_TIMEOUT)
        return RemoteRunAwsService.aws_instance.is_instance

    @staticmethod
    def update_aws_region_authless():
        """
        Updates the AWS region without auth params (via IAM role)
        """
        AwsService.set_region(RemoteRunAwsService.aws_instance.region)

    @staticmethod
    def _run_aws_monkey_cmd_async(instance_id, is_linux, island_ip):
        """
        Runs a monkey remotely using AWS
        :param instance_id: Instance ID of target
        :param is_linux:    Whether target is linux
        :param island_ip:   IP of the island which the instance will try to connect to
        :return:            Cmd
        """
        cmd_text = RemoteRunAwsService._get_run_monkey_cmd_line(is_linux, island_ip)
        return RemoteRunAwsService._run_aws_cmd_async(instance_id, is_linux, cmd_text)

    @staticmethod
    def _run_aws_cmd_async(instance_id, is_linux, cmd_line):
        cmd_runner = AwsCmdRunner(is_linux, instance_id)
        return Cmd(cmd_runner, cmd_runner.run_command_async(cmd_line))

    @staticmethod
    def _is_linux(os):
        return "linux" == os

    @staticmethod
    def _get_run_monkey_cmd_linux_line(island_ip):
        return (
            r"wget --no-check-certificate https://"
            + island_ip
            + r":5000/api/agent/download/linux "
            + r"-O monkey-linux-64"
            + r"; chmod +x monkey-linux-64"
            + r"; ./monkey-linux-64"
            + r" m0nk3y -s "
            + island_ip
            + r":5000"
        )

    @staticmethod
    def _get_run_monkey_cmd_windows_line(island_ip):
        return (
            r"[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {"
            r"$true}; (New-Object System.Net.WebClient).DownloadFile('https://"
            + island_ip
            + r":5000/api/agent/download/windows'"
            + r"'.\\monkey.exe'); "
            r";Start-Process -FilePath '.\\monkey.exe' "
            r"-ArgumentList 'm0nk3y -s " + island_ip + r":5000'; "
        )

    @staticmethod
    def _get_run_monkey_cmd_line(is_linux, island_ip):
        return (
            RemoteRunAwsService._get_run_monkey_cmd_linux_line(island_ip)
            if is_linux
            else RemoteRunAwsService._get_run_monkey_cmd_windows_line(island_ip)
        )
