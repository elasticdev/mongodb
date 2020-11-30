def run(stackargs):

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="mongodb_cluster")
    stack.parse.add_required(key="num_of_replicas",default="1")

    stack.parse.add_optional(key="mongodb_username",default="null")
    stack.parse.add_optional(key="mongodb_password",default="null")

    stack.parse.add_optional(key="vm_username",default="null")
    stack.parse.add_optional(key="ssh_keyname",default="null")

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

    # Add substack
    stack.add_substack('elasticdev:::ec2_ubuntu')
    stack.add_substack('elasticdev:::mongodb_replica_on_ubuntu')

    # Initialize 
    stack.init_variables()
    stack.init_substacks()

    # reference pt
    description = "Checkpoint - {}".format(stack.random_id(size=8).lower())

    cmd = 'echo "{}"'.format(description)

    stack.add_external_cmd(cmd=cmd,
                           order_type="empty_stack::shellout",
                           human_description=description,
                           display=False,
                           role="external/cli/execute")

    stack.set_parallel()

    mongodb_hosts = []

    for num in range(int(stack.num_of_replicas)):

        hostname = "{}-replica-num-{}".format(stack.mongodb_cluster,num).replace("_","-")
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

        inputargs = {"default_values":default_values}
        human_description = "Creating hostname {} on ec2".format(hostname)
        inputargs["automation_phase"] = "infrastructure"
        inputargs["human_description"] = human_description
        stack.ec2_ubuntu.insert(display=True,**inputargs)

    # provide the mongodb_hosts and begin installing the mongo specific 
    # package and replication
    default_values = {"mongodb_cluster":stack.mongodb_cluster}
    default_values["ssh_keyname"] = stack.ssh_keyname
    default_values["mongodb_hosts"] = mongodb_hosts
    if stack.mongodb_username: default_values["mongodb_username"] = stack.mongodb_username
    if stack.mongodb_password: default_values["mongodb_password"] = stack.mongodb_password
    if stack.vm_username: default_values["vm_username"] = stack.vm_username

    inputargs = {"default_values":default_values}
    human_description = "Initialing Ubuntu specific actions"
    inputargs["automation_phase"] = "infrastructure"
    inputargs["human_description"] = human_description
    stack.mongodb_replica_on_ubuntu.insert(display=True,**inputargs)

    return stack.get_results()
