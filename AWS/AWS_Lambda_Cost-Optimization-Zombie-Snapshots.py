import boto3
import json

# client = boto3.client('ec2')

# response = client.describe_volumes()
# s=0
# for vol in response["Volumes"]:
#     s+=vol["Size"]
#     print(vol["Size"])

# print("Tot size:",s)

# Get all active EC2 instance IDs not needed
# instances_response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
# active_instance_ids = set()

# for reservation in instances_response['Reservations']:
#     for instance in reservation['Instances']:
#         active_instance_ids.add(instance['InstanceId'])

# if len(active_instance_ids) > 0:
#     print("active_instance_ids:",active_instance_ids)

DELETE = False
# OR MOVE TO S3 Glacier

def delete_my_snapshot(ec2, snapshot_id, success_msg):
    if DELETE:
        ec2.delete_snapshot(SnapshotId=snapshot_id)
        print(success_msg)
        return 1
    else:
        print("DELETE set to False")
        print("\t-Reason for deleting was:", success_msg)
        return None

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')

    # Get all EBS snapshots
    snapshots_response = ec2.describe_snapshots(OwnerIds=['self'])


    tot_snapshots = 0
    tot_snapshots_to_delete = 0
    tot_snapshots_deleted = 0

    # Iterate through each snapshot and delete if it's not attached to any volume or the volume is not attached to a running instance
    for snapshot in snapshots_response['Snapshots']:
        tot_snapshots += 1
        snapshot_id = snapshot['SnapshotId']
        volume_id = snapshot.get('VolumeId')

        if not volume_id:
            print("Deleting orfaned snapshot {snapshot_id}...")
            # Delete the snapshot if it's not attached to any volume
            tot_snapshots_to_delete += 1
            if delete_my_snapshot(ec2,snapshot_id,f"[Type-1] Deleted EBS snapshot {snapshot_id} as it was not attached to any volume."):
                tot_snapshots_deleted += 1
        else:
            print(f"Analysing {snapshot_id} attached to {volume_id}")
            # Check if the volume still exists
            try:
                volume_response = ec2.describe_volumes(VolumeIds=[volume_id])
                if not volume_response['Volumes'][0]['Attachments']:
                    tot_snapshots_to_delete += 1
                    if delete_my_snapshot(ec2,snapshot_id,f"[Type-2] Deleted EBS snapshot {snapshot_id} as it was taken from a volume not attached to any instance."):
                        tot_snapshots_deleted += 1
                else:
                    print(f"\t-Snapshot is associated with an attached volume, no action need!")

            except ec2.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'InvalidVolume.NotFound':
                    # The volume associated with the snapshot is not found (it might have been deleted)
                    tot_snapshots_to_delete += 1
                    if delete_my_snapshot(ec2,snapshot_id,f"[Type-3] Deleted EBS snapshot {snapshot_id} as its associated volume was not found."):
                        tot_snapshots_deleted += 1
    print()
    status = f"Snapshot Deleted: {tot_snapshots_deleted},\nSnapshot need to be Deleted: {tot_snapshots_to_delete},\nTot Snapshots: {tot_snapshots}."
    print(status)
lambda_handler(None,None)