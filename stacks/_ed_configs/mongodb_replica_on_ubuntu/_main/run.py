def run(stackargs):

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="mongodb_hosts")
    stack.parse.add_required(key="mongodb_cluster")
    stack.parse.add_required(key="ssh_keyname")

    # This will be public_main/private_main
    stack.parse.add_required(key="mongodb_master_network",choices=["public_main","private_main"],default="public_main")

    stack.parse.add_optional(key="mongodb_username",default="null")
    stack.parse.add_optional(key="mongodb_password",default="null")
    stack.parse.add_optional(key="vm_username",default="ubuntu")

    # Add substack
    stack.add_substack('elasticdev:::create_mongodb_pem')
    stack.add_substack('elasticdev:::create_mongodb_keyfile')
    stack.add_substack('elasticdev:::_finalize_mongodb_replica_on_ubuntu')

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

    stack.unset_parallel(wait_all=True)

    # Finalize the mongodb replica set
    default_values = {"mongodb_cluster":stack.mongodb_cluster}
    default_values["ssh_keyname"] = stack.ssh_keyname
    default_values["mongodb_hosts"] = stack.mongodb_hosts
    default_values["vm_username"] = stack.vm_username
    default_values["mongodb_master_network"] = stack.mongodb_master_network
    if stack.mongodb_username: default_values["mongodb_username"] = stack.mongodb_username
    if stack.mongodb_password: default_values["mongodb_password"] = stack.mongodb_password

    inputargs = {"default_values":default_values}
    human_description = 'Finalizing mongodb replica set and init'
    inputargs["automation_phase"] = "infrastructure"
    inputargs["human_description"] = human_description

    stack._finalize_mongodb_replica_on_ubuntu.insert(display=True,**inputargs)

    return stack.get_results()
