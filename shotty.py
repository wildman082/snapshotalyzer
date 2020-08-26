import boto3
import botocore
import click


def filter_instances(project, instance): 
    instances = []
    if instance and not project:
        instanceFilter = [{'Name': 'instance-id', 'Values': [instance]}]
        instances = ec2.instances.filter(Filters=instanceFilter)
    elif project and instance:
        projectFilter = [{'Name': 'tag:Project', 'Values': [project]},{'Name': 'instance-id', 'Values': [instance]}]
        instances = ec2.instances.filter(Filters=projectFilter)
    elif project:
        projectFilter = [{'Name': 'tag:Project', 'Values': [project]}]
        instances = ec2.instances.filter(Filters=projectFilter)
    else:
        instances = ec2.instances.all()
    
    return instances

def has_pending_snapshot(volume):
    snapshots = list(volume.snapshots.all())
    return snapshots and snapshots[0].state == 'pending'


@click.group('cli')
@click.option('--profile', default='acloudguru', help="Specify AWS CLI profile")
def cli(profile):
    """Shotty manages snapshots"""
    session = boto3.Session(profile_name=profile)
    global ec2
    ec2 = session.resource('ec2')

@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--instance', default=None, help="specify a single instance")
@click.option('--project', default='acloud.guru', help="Only snapshots for project (tag Project:<name>)")
@click.option('--all', 'list_all', default=False, is_flag=True, help="list all snapshots, not just the most recent")
def list_snapshots(project, list_all, instance):
    "List ec2 snapshots"
    
    instances = filter_instances(project, instance)
    
    for i in instances:
        for v in i.volumes.all():
            for s in v.snapshots.all():
                print(", ".join((
                    s.id,
                    v.id,
                    i.id,
                    s.state,
                    s.progress,
                    s.start_time.strftime("%c") + " UTC")))  
                if s.state == 'completed' and not list_all: break
    return

@cli.group('volumes')
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--instance', default=None, help="specify a single instance")
@click.option('--project', default='acloud.guru', help="Only volumes for project (tag Project:<name>)")
def list_volumes(project, instance):
    "List ec2 volumes"
    
    instances = filter_instances(project, instance)
    
    for i in instances:
        for v in i.volumes.all():
            print(", ".join((
                v.id,
                i.id,
                v.state,
                str(v.size) + "GiB",
                v.encrypted and "Encrypted" or "Not Encrypted")))  
    return

@cli.group('instances')
def instances():
    """Commands for instances"""


@instances.command('list')
@click.option('--instance', default=None, help="specify a single instance")
@click.option('--project', help="Only snapshots for project (tag Project:<name>)")
@click.option('--force', 'all_instances', default=False, is_flag=True, help="all ec2 instances, no tag specified")
def list_instances(project, all_instances, instance):
    "List ec2 instances"
    
    if project:
        instances = filter_instances(project, instance)
    elif all_instances:
        instances = ec2.instances.all()
    else:
        print("Must use --force switch if no project specified")
        exit(1)
    
    for i in instances:
        tags = { t['Key']: t['Value'] for t in i.tags or [] }
        print(", ".join((
            i.id,
            i.instance_type,
            i.placement['AvailabilityZone'],
            i.state['Name'],
            i.public_dns_name,
            tags.get('Project', '<none>'))))  
    return


@instances.command('stop')
@click.option('--instance', default=None, help="specify a single instance")
@click.option('--project', default='acloud.guru', help="Only instances for project (tag Project:<name>)")
def stop_instances(project, instance):
    "Stop ec2 instances"
    
    instances = filter_instances(project, instance)

    for i in instances:
        print("Stopping instance " + i.id + "...")
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print("Can not stop instance " + i.id + "\n" + str(e))
            continue
    return


@instances.command('start')
@click.option('--instance', default=None, help="specify a single instance")
@click.option('--project', default='acloud.guru', help="Only instances for project (tag Project:<name>)")
def start_instances(project, instance):
    "Stop ec2 instances"
    
    instances = filter_instances(project, instance)

    for i in instances:
        print("Starting instance " + i.id + "...")
        try:
            i.start()
        except botocore.exceptions.ClientError as e:
            print("Can not start instance " + i.id + "\n" + str(e))
            continue
    return

@instances.command('reboot')
@click.option('--instance', default=None, help="specify a single instance")
@click.option('--project', default='acloud.guru', help="Only instances for project (tag Project:<name>)")
def reboot_instances(project, instance):
    "Reboot ec2 instances"
    
    instances = filter_instances(project, instance)

    for i in instances:
        print("Rebooting instance " + i.id + "...")
        try:
            i.stop()
        except botocore.exceptions.ClientError as e:
            print("Can not start instance " + i.id + "\n" + str(e))
            continue
        i.wait_until_stopped()
        try:
            i.start()
            
        except botocore.exceptions.ClientError as e:
            print("Can not start instance " + i.id + "\n" + str(e))
            continue
    return

@instances.command('snapshot')
@click.option('--instance', default=None, help="specify a single instance")
@click.option('--project', default='acloud.guru', help="Only instances for project (tag Project:<name>)")
def create_snapshots(project, instance):
    "Snapshot ec2 instances"
    
    instances = filter_instances(project, instance)

    tag = [
        {
            'ResourceType': 'snapshot',
            'Tags': [
                {
                    'Key': 'Project',
                    'Value': 'acloud.guru'
                },
            ]
        },
    ]

    for i in instances:
        wasRunning = True if i.state['Name'] == "running" else False
        if wasRunning:
            print("Stopping instance " + i.id + "...")
            i.stop()
        i.wait_until_stopped()
        for v in i.volumes.all():
            if has_pending_snapshot(v):
                print("Skipping "+ v.id + ", snapshot already in progress")
            else:
                print("Creating snapshot of " + v.id + "...")
                try:
                    v.create_snapshot(Description='Created by shotty',TagSpecifications=tag)
                except botocore.exceptions.ClientError as e:
                    print("Can not snapshot instance " + i.id + "\n" + str(e))
        if wasRunning:
            print("Starting instance " + i.id + "...")
            i.start()
            i.wait_until_running()
    
    print("Done!")
    return


if __name__ == '__main__': 
    cli()
