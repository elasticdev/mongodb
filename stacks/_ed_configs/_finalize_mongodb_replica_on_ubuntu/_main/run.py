def run(stackargs):

    import json

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="mongodb_hosts")
    stack.parse.add_required(key="mongodb_cluster")
    stack.parse.add_required(key="ssh_keyname")
    stack.parse.add_required(key="stateful_id",default="_random")

    # This will be public_main/private_main
    # Testingyoyo
    #stack.parse.add_required(key="mongodb_master_network",choices=["public_main","private_main"],default="public_main")
    stack.parse.add_required(key="mongodb_master_network",default="public_main")

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
    env_vars = {"ANS_VAR_mongodb_pem":mongodb_pem}
    env_vars["ANS_VAR_mongodb_keyfile"] = mongodb_keyfile
    env_vars["ANS_VAR_private_key"] = private_key
    env_vars["ANS_VAR_mongodb_db_name"] = stack.mongodb_db_name
    env_vars["ANS_VAR_mongodb_version"] = stack.mongodb_version
    env_vars["ANS_VAR_mongodb_port"] = stack.mongodb_port
    env_vars["ANS_VAR_mongodb_data_dir"] = stack.mongodb_data_dir
    env_vars["ANS_VAR_mongodb_storage_engine"] = stack.mongodb_storage_engine
    env_vars["ANS_VAR_mongodb_bind_ip"] = stack.mongodb_bind_ip
    env_vars["ANS_VAR_mongodb_logpath"] = stack.mongodb_logpath
    env_vars["ANS_VAR_mongodb_public_ips"] = ",".join(public_ips)
    env_vars["ANS_VAR_mongodb_private_ips"] = ",".join(private_ips)
    env_vars["ANS_VAR_mongodb_main_ips"] = "{},{}".format(public_ips[0],private_ips[0])
    env_vars["ANS_VAR_mongodb_master_network"] = stack.mongodb_master_network
    env_vars["ANS_VAR_mongodb_username"] = stack.mongodb_username
    env_vars["ANS_VAR_mongodb_password"] = stack.mongodb_password
    env_vars["METHOD"] = "create"

    # This is the default, but choose to be explicit
    env_vars["ANSIBLE_DIR"] = "/var/tmp/ansible"

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
    env_vars["ANS_VAR_exec_ymls"] = "install-python.yml"
    docker_env_fields_keys = env_vars.keys()

    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["human_description"] = "Installing python (for Ansible) to mongodb nodes"
    stack.ubuntu_vendor_init_replica.insert(**inputargs)

    # mongo install and setup
    env_vars["ANS_VAR_exec_ymls"] = "mongo-setup.yml"
    docker_env_fields_keys = env_vars.keys()

    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["human_description"] = "Install MongoDb version {} on nodes".format(stack.mongodb_version)
    stack.ubuntu_vendor_init_replica.insert(**inputargs)

    # mongo init replica
    env_vars["ANS_VAR_exec_ymls"] = "mongo-init-replica.yml"
    docker_env_fields_keys = env_vars.keys()

    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["human_description"] = "Initialize ReplicaSet on Master Node {}/{}".format(public_ips[0],private_ips[0])
    stack.ubuntu_vendor_init_replica.insert(**inputargs)

    # add slave replica nodes
    env_vars["ANS_VAR_exec_ymls"] = "mongo-add-slave-replica.yml"
    docker_env_fields_keys = env_vars.keys()

    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["human_description"] = "Add slave nodes to the master node"

    stack.ubuntu_vendor_init_replica.insert(**inputargs)

    #env_vars["ANS_VAR_exec_ymls"] = "install-python.yml,mongo-setup.yml,mongo-init-replica.yml,mongo-add-slave-replica.yml"
    #inputargs["human_description"] = "Executing init MongoDB {} with Ansible".format(stack.mongodb_cluster)

    return stack.get_results()
