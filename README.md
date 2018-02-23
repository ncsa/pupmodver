# pupmodver
Check for new versions of installed puppet modules

# Usage
1. yum install python-virtualenv
1. virtualenv venv
1. venv/bin/pip install -r requirements.txt
1. venv/bin/python pupmodver/pupmodver.py -h

# Puppet Environment Isolation
1. Update all environments
   1. `ls /etc/puppetlabs/code/environments/ | xargs -n1 puppet generate types --force --environment`
