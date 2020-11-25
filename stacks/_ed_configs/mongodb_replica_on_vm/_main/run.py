def run(stackargs):

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="dockerhosts")
    stack.parse.add_required(key="name")

    stack.parse.add_required(key="vm_username",default="ubuntu")
    stack.parse.add_required(key="ssh_key_name",default="_random")
    stack.parse.add_required(key="mongodb_username",default="_random")
    stack.parse.add_required(key="mongodb_password",default="_random")

    # Add substack
    stack.add_substack('elasticdev:::create_mongodb_pem')
    stack.add_substack('elasticdev:::create_mongodb_keyfile')
    stack.add_substack('elasticdev:::finalize_mongodb_replica_on_vm')

    # Initialize 
    stack.init_substacks()

    # lookup mongodb pem file needed for ssl/tls connection
    _lookup = {"must_exists":None}
    _lookup["resource_type"] = "ssl_pem"
    _lookup["provider"] = "openssl"
    _lookup["name"] = "{}.pem".format(stack.name)
    if not list(stack.get_resource(**_lookup)):
        inputargs = {"name":stack.name}
        stack.create_mongodb_pem.insert(display=True,**inputargs)

    # lookup mongodb keyfile needed for secure mongodb replication
    _lookup = {"must_exists":None}
    _lookup["provider"] = "openssl"
    _lookup["resource_type"] = "symmetric_key"
    _lookup["name"] = "{}_keyfile".format(stack.name)
    if not list(stack.get_resource(**_lookup)):
        inputargs = {"name":stack.name}
        stack.create_mongodb_keyfile.insert(display=True,**inputargs)

    # Finalize the mongodb replica set
    default_values = {"dockerhosts":stack.dockerhosts}
    default_values["ssh_key_name"] = stack.ssh_key_name
    default_values["vm_username"] = stack.vm_username
    default_values["mongodb_username"] = stack.mongodb_username
    default_values["mongodb_password"] = stack.mongodb_password
    default_values["name"] = stack.name

    inputargs = {"default_values":default_values}
    human_description = 'Finalizing mongodb replica set and init'
    inputargs["automation_phase"] = "infrastructure"
    inputargs["human_description"] = human_description
    stack.finalize_mongodb_replica_on_vm.insert(display=True,**inputargs)

    return stack.get_results()
