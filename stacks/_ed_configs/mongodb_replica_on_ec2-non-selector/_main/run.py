def run(stackargs):

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="mongodb_cluster")
    stack.parse.add_required(key="num_of_replicas",default="1")
    stack.parse.add_required(key="ssh_keyname")

    stack.parse.add_required(key="image",default="ami-06fb5332e8e3e577a")

    stack.parse.add_optional(key="aws_default_region",default="us-east-1")

    # This will be public_main/private_main
    stack.parse.add_optional(key="config_network",choices=["public","private"],default="public")

    stack.parse.add_optional(key="mongodb_username",default="null")
    stack.parse.add_optional(key="mongodb_password",default="null")
    stack.parse.add_optional(key="vm_username",default="null")

    # We will enable random suffix to add to the hostname
    stack.parse.add_optional(key="hostname_random",default="null")

    stack.parse.add_optional(key="bastion_security_groups",default="bastion")
    stack.parse.add_optional(key="bastion_subnet",default="private")
    stack.parse.add_optional(key="bastion_image",default="ami-06fb5332e8e3e577a")

    # destroy bastion config
    stack.parse.add_optional(key="bastion_config_destroy",default="null")

    stack.parse.add_optional(key="security_groups",default="null")
    stack.parse.add_optional(key="vpc_name",default="null")
    stack.parse.add_optional(key="subnet",default="null")
    stack.parse.add_optional(key="instance_type",default="t3.micro")
    stack.parse.add_optional(key="disksize",default="20")
    stack.parse.add_optional(key="ip_key",default="private_ip")

    stack.parse.add_optional(key="tags",default="null")
    stack.parse.add_optional(key="labels",default="null")

    # data disk
    stack.parse.add_optional(key="volume_size",default=100)
    stack.parse.add_optional(key="volume_mountpoint",default="/var/lib/mongodb")
    stack.parse.add_optional(key="volume_fstype",default="xfs")

    # Add substack
    stack.add_substack('elasticdev:::ec2_ubuntu')

    stack.add_substack('elasticdev:::create_mongodb_pem')
    stack.add_substack('elasticdev:::create_mongodb_keyfile')

    stack.add_substack('elasticdev:::_mongodb_replica_on_ubuntu_by_bastion_config')

    # Initialize 
    stack.init_variables()
    stack.init_substacks()

    stack.set_parallel()

    # lookup mongodb pem file needed for ssl/tls connection
    _lookup = {"must_exists":None}
    _lookup["resource_type"] = "ssl_pem"
    _lookup["provider"] = "openssl"
    _lookup["name"] = "{}.pem".format(stack.mongodb_cluster)
    if not stack.get_resource(**_lookup):
        default_values = {"basename":stack.mongodb_cluster}
        inputargs = {"default_values":default_values}
        stack.create_mongodb_pem.insert(display=True,**inputargs)

    # lookup mongodb keyfile needed for secure mongodb replication
    _lookup = {"must_exists":None}
    _lookup["provider"] = "openssl"
    _lookup["resource_type"] = "symmetric_key"
    _lookup["name"] = "{}_keyfile".format(stack.mongodb_cluster)
    if not stack.get_resource(**_lookup):
        default_values = {"basename":stack.mongodb_cluster}
        inputargs = {"default_values":default_values}
        stack.create_mongodb_keyfile.insert(display=True,**inputargs)

    mongodb_hosts = []

    if stack.hostname_random:
        hostname_base = "{}-replica-{}".format(stack.mongodb_cluster,stack.random_id(size=3).lower())
    else:
        hostname_base = "{}-replica".format(stack.mongodb_cluster)

    # Set up bastion configuration host
    stack.set_variable("bastion_hostname","{}-config".format(hostname_base))

    default_values = {"vpc_name":stack.vpc_name}
    default_values["keyname"] = stack.ssh_keyname
    default_values["aws_default_region"] = stack.aws_default_region
    default_values["size"] = stack.instance_type
    default_values["disksize"] = stack.disksize

    overide_values = {"hostname":stack.bastion_hostname}
    overide_values["register_to_ed"] = True
    overide_values["subnet"] = stack.bastion_subnet
    overide_values["security_groups"] = stack.bastion_security_groups
    overide_values["image"] = stack.bastion_image

    inputargs = {"default_values":default_values,
                 "overide_values":overide_values}

    human_description = "Creating bastion config hostname {} on ec2".format(stack.bastion_hostname)
    inputargs["automation_phase"] = "infrastructure"
    inputargs["human_description"] = human_description
    stack.ec2_ubuntu.insert(display=True,**inputargs)

    # Create mongodb ec2 instances
    for num in range(int(stack.num_of_replicas)):

        hostname = "{}-num-{}".format(hostname_base,num).replace("_","-")
        mongodb_hosts.append(hostname)

        default_values = {"hostname":hostname}
        default_values["keyname"] = stack.ssh_keyname
        default_values["image"] = stack.image
        default_values["aws_default_region"] = stack.aws_default_region
        default_values["security_groups"] = stack.security_groups
        default_values["vpc_name"] = stack.vpc_name
        default_values["subnet"] = stack.subnet
        default_values["size"] = stack.instance_type
        default_values["disksize"] = stack.disksize
        default_values["register_to_ed"] = None
        default_values["volume_size"] = stack.volume_size
        # ref 45304958324
        default_values["volume_name"] = "{}-{}".format(hostname,stack.volume_mountpoint).replace("/","-").replace(".","-")

        inputargs = {"default_values":default_values}
        human_description = "Creating hostname {} on ec2".format(hostname)
        inputargs["automation_phase"] = "infrastructure"
        inputargs["human_description"] = human_description
        stack.ec2_ubuntu.insert(display=True,**inputargs)

    stack.unset_parallel(wait_all=True)

    # provide the mongodb_hosts and begin installing 
    # the mongo specific package and replication
    default_values = {"mongodb_cluster":stack.mongodb_cluster}
    default_values["ssh_keyname"] = stack.ssh_keyname
    default_values["mongodb_hosts"] = mongodb_hosts
    default_values["config_network"] = stack.config_network
    default_values["aws_default_region"] = stack.aws_default_region

    if stack.mongodb_username: default_values["mongodb_username"] = stack.mongodb_username
    if stack.mongodb_password: default_values["mongodb_password"] = stack.mongodb_password
    if stack.vm_username: default_values["vm_username"] = stack.vm_username

    default_values["bastion_hostname"] = stack.bastion_hostname
    default_values["volume_mountpoint"] = stack.volume_mountpoint
    default_values["volume_fstype"] = stack.volume_fstype

    inputargs = {"default_values":default_values}
    human_description = "Initialing Ubuntu specific actions mongodb_username and mongodb_password"
    inputargs["automation_phase"] = "infrastructure"
    inputargs["human_description"] = human_description
    stack._mongodb_replica_on_ubuntu_by_bastion_config.insert(display=True,**inputargs)

    # destroy bastion config after replica completes
    # Testingyoyo
    #if stack.bastion_config_destroy:

    #    _destroy_values = { "hostname":stack.bastion_hostname,
    #                        "resource_type":"server",
    #                        "region":"server",
    #                        "must_exists":True }

    #    stack.remove_resource(ref_only=None,**_destroy_values)

    return stack.get_results()
