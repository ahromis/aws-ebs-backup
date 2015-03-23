#!/usr/bin/env python

import boto.ec2, os, socket
from datetime import datetime

max_snapshots = 10   # Number of snapshots to keep
block_device = '/dev/xvdf'
now = datetime.now()
hostname = socket.gethostname()
tag = 'SERVER_BACKUP'

# Connect to EC2 in this region
region = boto.utils.get_instance_metadata()['placement']['availability-zone'][:-1]
conn = boto.ec2.connect_to_region(region)
instance_id = boto.utils.get_instance_metadata()['instance-id']

print "Starting backup %s - %s %s" % (hostname, block_device, now)

# Get a list of volume attached to block_device
volume_id = conn.get_all_volumes(filters={'attachment.instance-id': instance_id, 'attachment.device': block_device})

# Create snapshot
description = "Backup: %s - %s %s" % (hostname, block_device, now)
snapshot = conn.create_snapshot(volume_id[0].id, description)
print "Adding tag \"Name: %s\" to snapshot: %s" % (tag, snapshot.id)
snapshot.add_tags({'Name': tag})

# Find all snapshots tagged "tag" and keep the last 10
all_snapshots = conn.get_all_snapshots(filters={'tag:Name': tag})

snap_sorted = sorted([(s.id, s.start_time) for s in all_snapshots], key=lambda k: k[1])

if len(all_snapshots) > max_snapshots:
  print "Deleting older snapshots that are more than the retention of %s" % max_snapshots
  for s in snap_sorted[:-max_snapshots]:
    print "Deleting snapshot", s[0]
    conn.delete_snapshot(s[0])

