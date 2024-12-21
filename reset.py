import os
import sys
from tools import run_command, run_command_out 

try:
    os.remove('.env')

except:
    print("An error occurred while resetting the environment.")
    sys.exit(1)

try:
    run_command('rm -rf applications')
    # run_command("sudo apt-get remove docker docker-engine docker.io containerd runc")
    # run_command("sudo apt-get autoremove")

    # Stop the Docker service
    run_command_out("sudo systemctl stop docker")

    # Remove Docker packages and configuration files
    run_command_out("sudo apt-get purge docker-ce docker-ce-cli containerd.io -y")

    # Clean up unused dependencies
    run_command_out("sudo apt-get autoremove --purge -y")

    # Remove remaining Docker directories
    run_command_out("sudo rm -rf /etc/docker")
    run_command_out("sudo rm -rf /var/lib/docker")
    run_command_out("sudo rm -rf /var/lib/containerd")

    # # Optionally remove the Docker group
    # run_command_out("sudo groupdel docker")

    # Verify if Docker is removed
    run_command_out("sudo systemctl status docker")


except:
    print("An error occurred while resetting the environment.")
    sys.exit(1)