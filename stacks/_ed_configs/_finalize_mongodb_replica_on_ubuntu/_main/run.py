def run(stackargs):

    import json

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="mongodb_hosts")
    stack.parse.add_required(key="mongodb_cluster")
    stack.parse.add_required(key="ssh_keyname")
    stack.parse.add_required(key="stateful_id",default="_random")

    stack.parse.add_optional(key="mongodb_username",default="_random")
    stack.parse.add_optional(key="mongodb_password",default="_random")
    stack.parse.add_optional(key="vm_username",default="ubuntu")
    stack.parse.add_optional(key="mongodb_data_dir",default="/var/lib/mongodb")
    stack.parse.add_optional(key="mongodb_db_name",default="mymongodb")
    stack.parse.add_optional(key="mongodb_storage_engine",default="wiredTiger")
    stack.parse.add_optional(key="mongodb_version",default="4.0.3")
    stack.parse.add_optional(key="mongodb_port",default="27017")
    stack.parse.add_optional(key="mongodb_bind_ip",default="0.0.0.0")
    stack.parse.add_optional(key="mongodb_logpath",default="/var/log/mongodb/mongod.log")

    stack.parse.add_optional(key="docker_exec_env",default="elasticdev/ansible-run-env")

    # Add Execution Group
    stack.add_execgroup("elasticdev:::mongodb::ubuntu_vendor_setup")
    stack.add_execgroup("elasticdev:::mongodb::ubuntu_vendor_init_replica")

    # Initialize 
    stack.init_variables()
    stack.init_execgroups()

    # get ssh_key
    _lookup = {"must_exists":True}
    _lookup["resource_type"] = "ssh_key_pair"
    _lookup["name"] = stack.ssh_keyname
    private_key = list(stack.get_resource(decrypt=True,**_lookup))[0]["private_key"]

    # get mongodb pem key
    _lookup = {"must_exists":True}
    _lookup["resource_type"] = "ssl_pem"
    _lookup["provider"] = "openssl"
    _lookup["name"] = "{}.pem".format(stack.mongodb_cluster)
    mongodb_pem = list(stack.get_resource(decrypt=True,**_lookup))[0]["contents"]

    # lookup mongodb keyfile needed for secure mongodb replication
    _lookup = {"must_exists":True}
    _lookup["provider"] = "openssl"
    _lookup["resource_type"] = "symmetric_key"
    _lookup["name"] = "{}_keyfile".format(stack.mongodb_cluster)
    mongodb_keyfile = list(stack.get_resource(decrypt=True,**_lookup))[0]["contents"]

    #stack.set_parallel(wait_all=True)

    public_ips = []
    private_ips = []

    _lookup = {"must_exists":True,"must_be_one":True}
    _lookup["resource_type"] = "server"

    for mongodb_host in stack.to_list(stack.mongodb_hosts):

        _lookup["hostname"] = mongodb_host
        _host_info = list(stack.get_resource(**_lookup))[0]

        stack.logger.debug_highlight('mongo hostname {}, found public_ip address "{}"'.format(mongodb_host,
                                                                                              _host_info["public_ip"]))

        if _host_info["public_ip"] not in public_ips: public_ips.append(_host_info["public_ip"])
        if _host_info["private_ip"] not in private_ips: private_ips.append(_host_info["private_ip"])

    # templify ansible and create necessary files
    env_vars = {"MONGODB_PEM":mongodb_pem}
    env_vars["MONGODB_KEYFILE"] = mongodb_keyfile
    env_vars["ANSIBLE_PRV_KEY"] = private_key
    env_vars["MONGODB_DB_NAME"] = stack.mongodb_db_name
    env_vars["MONGODB_VERSION"] = stack.mongodb_version
    env_vars["MONGODB_PORT"] = stack.mongodb_port
    env_vars["MONGODB_DATA_DIR"] = stack.mongodb_data_dir
    env_vars["MONGODB_STORAGE_ENGINE"] = stack.mongodb_storage_engine
    env_vars["MONGODB_BIND_IP"] = stack.mongodb_bind_ip
    env_vars["MONGODB_LOGPATH"] = stack.mongodb_logpath
    env_vars["MONGODB_PUBLIC_IPS"] = ",".join(public_ips)
    env_vars["MONGODB_PRIVATE_IPS"] = ",".join(private_ips)
    env_vars["MONGODB_MAIN_IPS"] = "{},{}".format(public_ips[0],private_ips[0])

    env_vars["mongodb_username".upper()] = stack.mongodb_username
    env_vars["mongodb_password".upper()] = stack.mongodb_password

    _ed_template_vars = [ "MONGODB_DB_NAME",
                          "MONGODB_VERSION",
                          "MONGODB_PORT",
                          "MONGODB_DATA_DIR",
                          "MONGODB_STORAGE_ENGINE",
                          "MONGODB_BIND_IP",
                          "MONGODB_LOGPATH",
                          "mongodb_username".upper(),
                          "mongodb_password".upper() ]

    env_vars["ED_TEMPLATE_VARS"] = ",".join(_ed_template_vars)
    env_vars["ANSIBLE_DIR"] = "/var/tmp/ansible"
    env_vars["METHOD"] = "create"

    inputargs = {"display":True}
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["name"] = stack.mongodb_cluster
    inputargs["stateful_id"] = stack.stateful_id
    inputargs["human_description"] = "Setting up Ansible for MongoDb"
    stack.ubuntu_vendor_setup.insert(**inputargs)

    env_vars = {"USE_DOCKER":True}
    env_vars["stateful_id".upper()] = stack.stateful_id
    env_vars["docker_exec_env".upper()] = stack.docker_exec_env

    inputargs = {"display":True}
    inputargs["name"] = stack.mongodb_cluster
    inputargs["stateful_id"] = stack.stateful_id

    # install python
    env_vars["ANSIBLE_EXEC_YMLS"] = "install-python.yml"
    docker_env_fields_keys = env_vars.keys()

    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["human_description"] = "Installing python to mongodb nodes"
    stack.ubuntu_vendor_init_replica.insert(**inputargs)

    # mongo install and setup
    env_vars["ANSIBLE_EXEC_YMLS"] = "mongo-setup.yml"
    docker_env_fields_keys = env_vars.keys()

    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["human_description"] = "Install and setup on mongodb nodes"
    stack.ubuntu_vendor_init_replica.insert(**inputargs)

    # mongo init replica
    env_vars["ANSIBLE_EXEC_YMLS"] = "mongo-init-replica.yml"
    docker_env_fields_keys = env_vars.keys()

    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["human_description"] = "Initialize replication on master mongodb node"
    stack.ubuntu_vendor_init_replica.insert(**inputargs)

    # add slave replica nodes
    env_vars["ANSIBLE_EXEC_YMLS"] = "mongo-add-slave-replica.yml"
    docker_env_fields_keys = env_vars.keys()

    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["human_description"] = "Add slave nodes to the master mongodb node"
    stack.ubuntu_vendor_init_replica.insert(**inputargs)

    #env_vars["ANSIBLE_EXEC_YMLS"] = "install-python.yml,mongo-setup.yml,mongo-init-replica.yml,mongo-add-slave-replica.yml"
    #inputargs["human_description"] = "Executing init MongoDB {} with Ansible".format(stack.mongodb_cluster)

    return stack.get_results()
