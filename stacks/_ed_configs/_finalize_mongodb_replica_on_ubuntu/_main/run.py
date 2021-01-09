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
    stack.parse.add_optional(key="config_network",choices=["public","private"],default="public")

    stack.parse.add_optional(key="mongodb_username",default="_random")
    stack.parse.add_optional(key="mongodb_password",default="_random")
    stack.parse.add_optional(key="vm_username",default="ubuntu")
    stack.parse.add_optional(key="mongodb_data_dir",default="/var/lib/mongodb")
    stack.parse.add_optional(key="mongodb_storage_engine",default="wiredTiger")
    stack.parse.add_optional(key="mongodb_version",default="4.0.3")
    stack.parse.add_optional(key="mongodb_port",default="27017")
    stack.parse.add_optional(key="mongodb_bind_ip",default="0.0.0.0")
    stack.parse.add_optional(key="mongodb_logpath",default="/var/log/mongodb/mongod.log")
    stack.parse.add_optional(key="publish_creds",default=True,null_allowed=True)
    stack.parse.add_optional(key="use_docker",default=True,null_allowed=True)

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
    _lookup["serialize"] = True
    _lookup["serialize_keys"] = [ "contents" ]
    return stack.get_resource(decrypt=True,**_lookup)

    # get mongodb pem key
    _lookup = {"must_exists":True}
    _lookup["resource_type"] = "ssl_pem"
    _lookup["provider"] = "openssl"
    _lookup["name"] = "{}.pem".format(stack.mongodb_cluster)
    _lookup["serialize"] = True
    _lookup["serialize_keys"] = [ "contents" ]
    return stack.get_resource(decrypt=True,**_lookup)

    # lookup mongodb keyfile needed for secure mongodb replication
    _lookup = {"must_exists":True}
    _lookup["provider"] = "openssl"
    _lookup["resource_type"] = "symmetric_key"
    _lookup["name"] = "{}_keyfile".format(stack.mongodb_cluster)
    _lookup["serialize"] = True
    _lookup["serialize_keys"] = [ "contents" ]
    return stack.get_resource(decrypt=True,**_lookup)

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
    env_vars["ANS_VAR_mongodb_version"] = stack.mongodb_version
    env_vars["ANS_VAR_mongodb_port"] = stack.mongodb_port
    env_vars["ANS_VAR_mongodb_data_dir"] = stack.mongodb_data_dir
    env_vars["ANS_VAR_mongodb_storage_engine"] = stack.mongodb_storage_engine
    env_vars["ANS_VAR_mongodb_bind_ip"] = stack.mongodb_bind_ip
    env_vars["ANS_VAR_mongodb_logpath"] = stack.mongodb_logpath
    env_vars["ANS_VAR_mongodb_public_ips"] = ",".join(public_ips)
    env_vars["ANS_VAR_mongodb_private_ips"] = ",".join(private_ips)
    env_vars["ANS_VAR_mongodb_main_ips"] = "{},{}".format(public_ips[0],private_ips[0])
    env_vars["ANS_VAR_mongodb_username"] = stack.mongodb_username
    env_vars["ANS_VAR_mongodb_password"] = stack.mongodb_password

    if stack.config_network == "private":
        env_vars["ANS_VAR_mongodb_config_network"] = private_ips[0]
    else:
        env_vars["ANS_VAR_mongodb_config_network"] = public_ips[0]

    env_vars["METHOD"] = "create"
    env_vars["ANSIBLE_DIR"] = "/var/tmp/ansible"

    human_description = "Setting up Ansible for MongoDb"
    inputargs = {"display":True}
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["name"] = stack.mongodb_cluster
    inputargs["stateful_id"] = stack.stateful_id
    inputargs["human_description"] = human_description
    stack.ubuntu_vendor_setup.insert(**inputargs)

    env_vars = {"stateful_id".upper():stack.stateful_id}
    env_vars["docker_exec_env".upper()] = stack.docker_exec_env
    if stack.use_docker: env_vars["use_docker".upper()] = True

    inputargs = {"display":True}
    inputargs["name"] = stack.mongodb_cluster
    inputargs["stateful_id"] = stack.stateful_id

    # install python
    env_vars["ANS_VAR_exec_ymls"] = "entry_point/10-install-python.yml"
    docker_env_fields_keys = env_vars.keys()

    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["human_description"] = "Installing python (for Ansible) to mongodb nodes"
    stack.ubuntu_vendor_init_replica.insert(**inputargs)

    # mongo install and setup
    env_vars["ANS_VAR_exec_ymls"] = "entry_point/20-mongo-setup.yml"
    docker_env_fields_keys = env_vars.keys()

    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["human_description"] = "Install MongoDb version {} on nodes".format(stack.mongodb_version)
    stack.ubuntu_vendor_init_replica.insert(**inputargs)

    # mongo init replica
    env_vars["ANS_VAR_exec_ymls"] = "entry_point/30-mongo-init-replica.yml"
    docker_env_fields_keys = env_vars.keys()

    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["human_description"] = "Initialize ReplicaSet on Master Node {}/{}".format(public_ips[0],private_ips[0])
    stack.ubuntu_vendor_init_replica.insert(**inputargs)

    # add slave replica nodes
    env_vars["ANS_VAR_exec_ymls"] = "entry_point/40-mongo-add-slave-replica.yml"
    docker_env_fields_keys = env_vars.keys()

    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["human_description"] = "Add slave nodes to the master node"
    stack.ubuntu_vendor_init_replica.insert(**inputargs)

    _publish_vars = {"mongodb_cluster":stack.mongodb_cluster}
    _publish_vars["mongodb_version"] = stack.mongodb_version
    _publish_vars["mongodb_port"] = stack.mongodb_port
    _publish_vars["mongodb_data_dir"] = stack.mongodb_data_dir
    _publish_vars["mongodb_storage_engine"] = stack.mongodb_storage_engine
    _publish_vars["mongodb_bind_ip"] = stack.mongodb_bind_ip
    _publish_vars["mongodb_logpath"] = stack.mongodb_logpath
    _publish_vars["mongodb_public_ips"] = ",".join(public_ips)
    _publish_vars["mongodb_private_ips"] = ",".join(private_ips)

    if stack.publish_creds:
        _publish_vars["mongodb_username"] = stack.mongodb_username
        _publish_vars["mongodb_password"] = stack.mongodb_password

    stack.publish(_publish_vars)

    return stack.get_results()
