# pupmodver
Check for new versions of installed puppet modules

# Usage
1. python3 -m venv venv
1. venv/bin/pip install -U pip
1. venv/bin/pip install -r requirements.txt
1. venv/bin/python pupmodver.py -h

## Update all modules in a single environment
1. `ENV=test; venv/bin/python pupmodver.py -ut -e $ENV | xargs -n1 puppet module upgrade --environment $ENV`

# Puppet Environment Isolation
1. Update all environments
   1. `ls $(puppet config print environmentpath) | xargs -n1 puppet generate types --force --environment`
