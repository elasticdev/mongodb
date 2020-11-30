def run(stackargs):

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="mongodb_hosts")
    stack.parse.add_required(key="mongodb_cluster")
    stack.parse.add_required(key="vm_username",default="ubuntu")
    stack.parse.add_required(key="ssh_keyname",default="_random")
    stack.parse.add_required(key="mongodb_username",default="_random")
    stack.parse.add_required(key="mongodb_password",default="_random")

    # Add substack
    stack.add_substack('elasticdev:::create_mongodb_pem')
    stack.add_substack('elasticdev:::create_mongodb_keyfile')
    stack.add_substack('elasticdev:::_finalize_mongodb_replica_on_vm')

    # Initialize 
    stack.init_substacks()

    # lookup mongodb pem file needed for ssl/tls connection
    _lookup = {"must_exists":None}
    _lookup["resource_type"] = "ssl_pem"
    _lookup["provider"] = "openssl"
    _lookup["name"] = "{}.pem".format(stack.mongodb_cluster)
    if not list(stack.get_resource(**_lookup)):
        inputargs = {"name":stack.mongodb_cluster}
        stack.create_mongodb_pem.insert(display=True,**inputargs)

    # lookup mongodb keyfile needed for secure mongodb replication
    _lookup = {"must_exists":None}
    _lookup["provider"] = "openssl"
    _lookup["resource_type"] = "symmetric_key"
    _lookup["name"] = "{}_keyfile".format(stack.mongodb_cluster)
    if not list(stack.get_resource(**_lookup)):
        inputargs = {"name":stack.mongodb_cluster}
        stack.create_mongodb_keyfile.insert(display=True,**inputargs)

    # Finalize the mongodb replica set
    default_values = {"mongodb_cluster":stack.mongodb_cluster}
    default_values["ssh_keyname"] = stack.ssh_keyname
    default_values["mongodb_hosts"] = stack.mongodb_hosts
    if stack.mongodb_username: default_values["mongodb_username"] = stack.mongodb_username
    if stack.mongodb_password: default_values["mongodb_password"] = stack.mongodb_password
    if stack.vm_username: default_values["vm_username"] = stack.vm_username

    inputargs = {"default_values":default_values}
    human_description = 'Finalizing mongodb replica set and init'
    inputargs["automation_phase"] = "infrastructure"
    inputargs["human_description"] = human_description

    stack._finalize_mongodb_replica_on_vm.insert(display=True,**inputargs)

    return stack.get_results()
