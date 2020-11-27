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
    stack.parse.add_required(key="stateful_id",default="_random")
    stack.parse.add_optional(key="docker_exec_env",default="elasticdev/ansible-run-env")

    # Add Execution Group
    stack.add_execgroup("elasticdev:::mongodb::ubuntu_vendor")

    # Initialize 
    stack.init_variables()
    stack.init_execgroups()

    # get ssh_key
    _lookup = {"must_exists":True}
    _lookup["resource_type"] = "ssh_key_pair"
    _lookup["name"] = stack.ssh_key_name
    private_key = list(stack.get_resource(**_lookup))[0]["private_key"]

    # get mongodb pem key
    _lookup = {"must_exists":True}
    _lookup["resource_type"] = "ssl_pem"
    _lookup["provider"] = "openssl"
    _lookup["name"] = "{}.pem".format(stack.name)
    mongodb_pem = list(stack.get_resource(**_lookup))[0]["contents"]

    # lookup mongodb keyfile needed for secure mongodb replication
    _lookup = {"must_exists":True}
    _lookup["provider"] = "openssl"
    _lookup["resource_type"] = "symmetric_key"
    _lookup["name"] = "{}_keyfile".format(stack.name)
    mongodb_keyfile = list(stack.get_resource(**_lookup))[0]["contents"]

    public_ips = []
    private_ips = []
    for dockerhost in stack.dockerhosts.split(","):
        _lookup = {"must_exists":True}
        _lookup["resource_type"] = "server"
        _lookup["hostname"] = dockerhost.strip()
        _host_info = list(stack.get_resource(**_lookup))[0]
        public_ips.append(_host_info["public_ip"])
        private_ips.append(_host_info["private_ip"])

    # Execute execgroup
    env_vars = {"MONGODB_PEM":mongodb_pem}
    env_vars["MONGODB_KEYFILE"] = mongodb_keyfile
    env_vars["MONGODB_PUBLIC_IPS"] = ",".join(public_ips)
    env_vars["MONGODB_PRIVATE_IPS"] = ",".join(private_ips)
    env_vars["ANSIBLE_PRV_KEY"] = private_key
    env_vars["stateful_id".upper()] = stack.stateful_id
    env_vars["docker_exec_env".upper()] = stack.docker_exec_env
    #env_vars["ANSIBLE_BUILD_DIR"] = "/var/tmp/build/ansible"
    env_vars["docker_exec_env".upper()] = stack.docker_exec_env
    env_vars["METHOD"] = "create"
    env_vars["USE_DOCKER"] = True
    env_vars["CLOBBER"] = True

    docker_env_fields_keys = env_vars.keys()
    docker_env_fields_keys.remove("METHOD")

    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)

    inputargs = {"display":True}
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["name"] = stack.name
    inputargs["stateful_id"] = stack.stateful_id
    inputargs["human_description"] = "Creating MongoDB Replica set {}".format(stack.name)
    stack.ubuntu_vendor.insert(**inputargs)

    return stack.get_results()