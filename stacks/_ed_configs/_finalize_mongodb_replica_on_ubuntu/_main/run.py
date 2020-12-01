def run(stackargs):

    import json

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="mongodb_hosts")
    stack.parse.add_required(key="mongodb_cluster")
    stack.parse.add_required(key="ssh_keyname")

    stack.parse.add_optional(key="mongodb_username",default="_random")
    stack.parse.add_optional(key="mongodb_password",default="_random")
    stack.parse.add_optional(key="vm_username",default="ubuntu")

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
    _lookup["name"] = stack.ssh_keyname
    private_key = list(stack.get_resource(**_lookup))[0]["private_key"]

    # get mongodb pem key
    _lookup = {"must_exists":True}
    _lookup["resource_type"] = "ssl_pem"
    _lookup["provider"] = "openssl"
    _lookup["name"] = "{}.pem".format(stack.mongodb_cluster)
    mongodb_pem = list(stack.get_resource(**_lookup))[0]["contents"]

    # lookup mongodb keyfile needed for secure mongodb replication
    _lookup = {"must_exists":True}
    _lookup["provider"] = "openssl"
    _lookup["resource_type"] = "symmetric_key"
    _lookup["name"] = "{}_keyfile".format(stack.mongodb_cluster)
    mongodb_keyfile = list(stack.get_resource(**_lookup))[0]["contents"]

    #stack.set_parallel(wait_all=True)

    public_ips = []
    private_ips = []

    for mongodb_host in stack.to_list(stack.mongodb_hosts):

        _lookup = {"must_exists":True}
        _lookup["resource_type"] = "server"
        _lookup["hostname"] = mongodb_host.strip()
        _host_info = list(stack.get_resource(**_lookup))[0]
        public_ips.append(_host_info["public_ip"])
        private_ips.append(_host_info["private_ip"])

    # Execute execgroup
    env_vars = {"MONGODB_PEM":mongodb_pem}
    env_vars["MONGODB_KEYFILE"] = mongodb_keyfile
    env_vars["MONGODB_PUBLIC_IPS"] = ",".join(public_ips)
    env_vars["MONGODB_PRIVATE_IPS"] = ",".join(private_ips)
    env_vars["MONGODB_MAIN_IPS"] = ",".join(private_ips)
    env_vars["ANSIBLE_PRV_KEY"] = private_key
    env_vars["ANSIBLE_EXEC_YMLS"] = "install-python.yml,mongo-setup.yml,mongo-init-replica.yml,mongo-add-slave-replica.yml"

    env_vars["mongodb_username".upper()] = stack.mongodb_username
    env_vars["mongodb_password".upper()] = stack.mongodb_password
    env_vars["ED_TEMPLATE_VARS"] = "{},{}".format("mongodb_username".upper(),"mongodb_password".upper())

    env_vars["stateful_id".upper()] = stack.stateful_id
    env_vars["docker_exec_env".upper()] = stack.docker_exec_env
    #env_vars["ANSIBLE_BUILD_DIR"] = "/var/tmp/build/ansible"
    env_vars["METHOD"] = "create"
    env_vars["USE_DOCKER"] = True
    env_vars["CLOBBER"] = True

    docker_env_fields_keys = env_vars.keys()
    docker_env_fields_keys.remove("METHOD")

    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)

    inputargs = {"display":True}
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["name"] = stack.mongodb_cluster
    inputargs["stateful_id"] = stack.stateful_id
    inputargs["human_description"] = "Creating MongoDB Replica set {}".format(stack.mongodb_cluster)
    stack.ubuntu_vendor.insert(**inputargs)

    return stack.get_results()
