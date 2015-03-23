#!/usr/bin/env python

import boto.ec2, os, socket, urllib2, time
from datetime import datetime

block_device = '/dev/xvdf'
region = 'us-east-1'
volume_type = 'gp2'
volume_size = 1
az_url = 'http://169.254.169.254/latest/meta-data/placement/availability-zone'
tag = 'SERVER_BACKUP'

# find current AZ
response = urllib2.urlopen(az_url)
current_az = response.read()
now = datetime.now()
hostname = socket.gethostname()

print "Starting mount of latest %s snapshot on %s to device: %s %s" % (tag, hostname, block_device, now)

# connect to EC2 in this region
conn = boto.ec2.connect_to_region(region)
instance_id = boto.utils.get_instance_metadata()['instance-id']

# find all snapshots named tag
all_snapshots = conn.get_all_snapshots(filters={'tag:Name': tag})
if not all_snapshots:
  print "Error: No snapshots found tagged %s.", tag
  exit(1)

snap_sorted = sorted([(s.id, s.start_time) for s in all_snapshots], key=lambda k: k[1])

# create volume
print "Creating volume from snapshot: ", latest_snapshot
volume = all_snapshots[0].create_volume(current_az, size=None, volume_type=volume_type)
print "Volume: %s created from snapshot: %s" % (volume.id, latest_snapshot)

# poll volume status before moving on 
curr_vol = conn.get_all_volumes([volume.id])[0]
while curr_vol.status != 'available':
  curr_vol = conn.get_all_volumes([volume.id])[0]
  print 'Waiting for the new volume to become available...'
  time.sleep(2)
  print curr_vol.status

# mount voume to device
print "Volume is available, will now mount volume: %s to device: %s" % (volume.id, block_device)
conn.attach_volume (volume.id, instance_id, block_device)
