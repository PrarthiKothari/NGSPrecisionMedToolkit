import os
import sys
from tools import run_command 

try:
    os.remove('.env')

except:
    print("An error occurred while resetting the environment.")
    sys.exit(1)

try:
    run_command('rm -rf applications')

except:
    print("An error occurred while resetting the environment.")
    sys.exit(1)