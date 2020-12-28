def run(stackargs):

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="mongodb_cluster")
    stack.parse.add_required(key="num_of_replicas",default="1")
    stack.parse.add_required(key="ssh_keyname")

    # Testingyoyo
    # This will be public_main/private_main
    stack.parse.add_optional(key="config_network",choices=["public","private"],default="public")

    stack.parse.add_optional(key="mongodb_username",default="null")
    stack.parse.add_optional(key="mongodb_password",default="null")
    stack.parse.add_optional(key="vm_username",default="null")

    # We will enable random suffix to add to the hostname
    stack.parse.add_optional(key="hostname_random",default="null")

    # if bastion_config, then bastion_config will create a bastion_hostname
    # used to configure the mongodb cluster
    stack.parse.add_optional(key="bastion_config",default="null")
    stack.parse.add_optional(key="bastion_security_groups",default="bastion")
    stack.parse.add_optional(key="bastion_subnet",default="private")
    stack.parse.add_optional(key="bastion_image",default="ami-06fb5332e8e3e577a")

    # Testingyoyo
    #stack.parse.add_required(key="image")
    #stack.parse.add_required(key="aws_default_region",default="us-east-1")

    stack.parse.add_required(key="image",default="ami-06fb5332e8e3e577a")
    stack.parse.add_required(key="aws_default_region",default="ap-southeast-1")

    stack.parse.add_optional(key="security_groups",default="null")
    stack.parse.add_optional(key="vpc_name",default="null")
    stack.parse.add_optional(key="subnet",default="null")
    stack.parse.add_optional(key="size",default="t3.micro")
    stack.parse.add_optional(key="disksize",default="20")
    stack.parse.add_optional(key="ip_key",default="private_ip")

    stack.parse.add_optional(key="tags",default="null")
    stack.parse.add_optional(key="labels",default="null")

    # extra disk
    stack.parse.add_optional(key="volume_name",default="null")
    stack.parse.add_optional(key="volume_size",default="null")
    stack.parse.add_optional(key="volume_mountpoint",default="/var/lib/mongodb")
    stack.parse.add_optional(key="volume_fstype",default="xfs")

    # Add substack
    stack.add_substack('elasticdev:::ec2_ubuntu')
    stack.add_substack('elasticdev:::mongodb_replica_on_ubuntu')

    # Initialize 
    stack.init_variables()
    stack.init_substacks()

    stack.set_parallel()

    mongodb_hosts = []

    if stack.hostname_random:
        hostname_base = "{}-replica-{}".format(stack.mongodb_cluster,stack.random_id(size=3).lower())
    else:
        hostname_base = "{}-replica".format(stack.mongodb_cluster)

    # Testingyoyo
    # set bastion config and hostname
    if stack.bastion_config:

        stack.set_variable("bastion_hostname","{}-config".format(hostname_base))

        default_values = {"vpc_name":stack.vpc_name}
        default_values["keyname"] = stack.ssh_keyname
        default_values["aws_default_region"] = stack.aws_default_region
        default_values["size"] = stack.size
        default_values["disksize"] = stack.disksize

        overide_values = {"register_to_ed":True}
        overide_values["subnet"] = stack.bastion_subnet
        overide_values["security_groups"] = stack.bastion_security_groups
        overide_values["image"] = stack.bastion_image
        overide_values = {"hostname":stack.bastion_hostname}

        # Testingyoyo
        inputargs = {"default_values":default_values,
                     "overide_values":overide_values}

        # Testingyoyo
        default_values["register_to_ed"] = True
        default_values["subnet"] = stack.bastion_subnet
        default_values["security_groups"] = stack.bastion_security_groups
        default_values["image"] = stack.bastion_image
        default_values = {"hostname":stack.bastion_hostname}
        inputargs = {"default_values":default_values}

        human_description = "Creating bastion config hostname {} on ec2".format(stack.bastion_hostname)
        inputargs["automation_phase"] = "infrastructure"
        inputargs["human_description"] = human_description
        stack.ec2_ubuntu.insert(display=True,**inputargs)
    else:
        stack.set_variable("bastion_hostname",None)

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
        default_values["size"] = stack.size
        default_values["disksize"] = stack.disksize
        default_values["register_to_ed"] = None

        # extra disk
        if stack.volume_size: default_values["volume_size"] = stack.volume_size
        if stack.volume_name: default_values["volume_name"] = stack.volume_name

        # if bastion_config, then the workers cannot access the hosts unless 
        # using a bastion hosts to do so
        if not stack.bastion_config:
            if stack.volume_mountpoint: default_values["volume_mountpoint"] = stack.volume_mountpoint
            if stack.volume_fstype: default_values["volume_fstype"] = stack.volume_fstype

        inputargs = {"default_values":default_values}
        human_description = "Creating hostname {} on ec2".format(hostname)
        inputargs["automation_phase"] = "infrastructure"
        inputargs["human_description"] = human_description
        stack.ec2_ubuntu.insert(display=True,**inputargs)

    stack.unset_parallel(wait_all=True)

    # provide the mongodb_hosts and begin installing the mongo specific 
    # package and replication
    default_values = {"mongodb_cluster":stack.mongodb_cluster}
    default_values["ssh_keyname"] = stack.ssh_keyname
    default_values["mongodb_hosts"] = mongodb_hosts
    default_values["config_network"] = stack.config_network
    if stack.mongodb_username: default_values["mongodb_username"] = stack.mongodb_username
    if stack.mongodb_password: default_values["mongodb_password"] = stack.mongodb_password
    if stack.vm_username: default_values["vm_username"] = stack.vm_username

    # if bastion_hostname, we will configure it through the bastion_hostname
    if stack.bastion_hostname: 

        default_values["bastion_hostname"] = stack.bastion_hostname
        if stack.volume_mountpoint: default_values["volume_mountpoint"] = stack.volume_mountpoint
        if stack.volume_fstype: default_values["volume_fstype"] = stack.volume_fstype

    inputargs = {"default_values":default_values}
    human_description = "Initialing Ubuntu specific actions mongodb_username {} mongodb_password {}".format(stack.mongodb_username,stack.mongodb_password)
    inputargs["automation_phase"] = "infrastructure"
    inputargs["human_description"] = human_description
    stack.mongodb_replica_on_ubuntu.insert(display=True,**inputargs)

    return stack.get_results()
