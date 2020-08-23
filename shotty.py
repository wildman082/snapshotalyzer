import boto3
import click

session = boto3.Session(profile_name="acloudguru")
ec2 = session.resource('ec2')


def filter_instances(project):
    instances = []

    if project:
        projectFilter = [{'Name': 'tag:Project', 'Values': [project]}]
        instances = ec2.instances.filter(Filters=projectFilter)
    else:
        instances = ec2.instances.all()
    
    return instances


@click.group()
def cli():
    """Shotty manages snapshots"""

@cli.group('snapshots')
def snapshots():
    """Commands for snapshots"""

@snapshots.command('list')
@click.option('--project', default='acloud.guru', help="Only snapshots for project (tag Project:<name>)")
def list_snapshots(project):
    "List ec2 snapshots"
    
    instances = filter_instances(project)
    
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
    return

@cli.group('volumes')
def volumes():
    """Commands for volumes"""

@volumes.command('list')
@click.option('--project', default='acloud.guru', help="Only volumes for project (tag Project:<name>)")
def list_volumes(project):
    "List ec2 volumes"
    
    instances = filter_instances(project)
    
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
@click.option('--project', default='acloud.guru', help="Only instances for project (tag Project:<name>)")
def list_instances(project):
    "List ec2 instances"
    
    instances = filter_instances(project)
    
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
@click.option('--project', default='acloud.guru', help="Only instances for project (tag Project:<name>)")
def stop_instances(project):
    "Stop ec2 instances"
    
    instances = filter_instances(project)

    for i in instances:
        print("Stopping instance " + i.id + "...")
        i.stop()
    return


@instances.command('start')
@click.option('--project', default='acloud.guru', help="Only instances for project (tag Project:<name>)")
def start_instances(project):
    "Stop ec2 instances"
    
    instances = filter_instances(project)

    for i in instances:
        print("Starting instance " + i.id + "...")
        i.start()
    return

@instances.command('snapshot')
@click.option('--project', default='acloud.guru', help="Only instances for project (tag Project:<name>)")
def create_snapshots(project):
    "Snapshot ec2 instances"
    
    instances = filter_instances(project)

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
        for v in i.volumes.all():
            print("Creating snapshot of  " + v.id + "...")
            v.create_snapshot(Description='Created by shotty',TagSpecifications=tag)
    return


if __name__ == '__main__': 
    cli()
