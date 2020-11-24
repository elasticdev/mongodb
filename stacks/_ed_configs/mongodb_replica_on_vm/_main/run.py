def run(stackargs):

    import json

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="dockerhosts")
    stack.parse.add_required(key="name")
    stack.parse.add_required(key="ssh_key_name")
    stack.parse.add_required(key="vm_username",default="ubuntu")
    stack.parse.add_required(key="mongodb_username",default="_random")
    stack.parse.add_required(key="mongodb_password",default="_random")

    # Add shelloutconfig dependencies
    stack.add_shelloutconfig('elasticdev:::mongodb::create_keys')

    # Add substack
    stack.add_substack('elasticdev:::finalize_mongodb_replica_on_vm')

    # Initialize 
    stack.init_substacks()
    stack.init_shelloutconfigs()

    # Create mongodb_keyfile for MongoDb replication
    env_vars = {"INSERT_IF_EXISTS":True}
    env_vars["NAME"] = stack.name
    env_vars["METHOD"] = "create"

    inputargs = {"display":True}
    inputargs["human_description"] = 'Create mongodb_keyfile for MongoDb replication'
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["automation_phase"] = "infrastructure"
    stack.create_keys.resource_exec(**inputargs)

    # Create mongodb.pem for MongoDb SSL
    env_vars = {"INSERT_IF_EXISTS":True}
    env_vars["NAME"] = stack.name
    env_vars["METHOD"] = "create_ssl"

    inputargs = {"display":True}
    inputargs["human_description"] = 'Create mongodb.pem for MongoDb SSL'
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["automation_phase"] = "infrastructure"
    stack.create_keys.resource_exec(**inputargs)

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
