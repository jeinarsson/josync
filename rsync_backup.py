#!/usr/bin/env python
import json

# Read config file
with open('backup.cfg.json') as f:
    json_data=f.read()
    config = json.loads(json_data)

print config['sources']