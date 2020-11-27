def run(stackargs):

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="name")
    stack.parse.add_required(key="num_of_replicas",default="1")

    stack.parse.add_required(key="vm_username",default="ubuntu")
    stack.parse.add_required(key="ssh_key_name",default="_random")
    stack.parse.add_required(key="mongodb_username",default="_random")
    stack.parse.add_required(key="mongodb_password",default="_random")

    # Testingyoyo
    #stack.parse.add_required(key="image")
    #stack.parse.add_required(key="aws_default_region",default="us-east-1")

    stack.parse.add_required(key="image",default="ami-06fb5332e8e3e577a")
    stack.parse.add_required(key="aws_default_region",default="ap-southeast-1")

    stack.parse.add_optional(key="security_groups",default="null")
    stack.parse.add_optional(key="vpc_name",default="null")
    stack.parse.add_optional(key="subnet",default="null")

    stack.parse.add_optional(key="tags",default="null")
    stack.parse.add_optional(key="labels",default="null")

    # Add substack
    stack.add_substack('elasticdev:::ec2_ubuntu')

    # Initialize 
    stack.init_substacks()

    # Testingyoyo
    for num in range(int(stack.num_of_replicas)):

        hostname = "{}-replica-num-{}".format(num).replace("_","-")
        default_values = {"hostname":hostname}
        default_values["key_name"] = stack.ssh_key_name
        default_values["image"] = stack.image
        default_values["aws_default_region"] = stack.aws_default_region
        default_values["security_groups"] = stack.security_groups
        default_values["vpc_name"] = stack.vpc_name
        default_values["subnet"] = stack.subnet

        inputargs = {"default_values":default_values}
        human_description = "Creating hostname {} on ec2".format(hostname)
        inputargs["automation_phase"] = "infrastructure"
        inputargs["human_description"] = human_description
        stack.ec2_ubuntu.insert(display=True,**inputargs)

    return stack.get_results()
