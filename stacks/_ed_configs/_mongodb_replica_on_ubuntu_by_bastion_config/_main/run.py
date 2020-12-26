def _get_instance_info(hostname):

    _lookup = {"must_exists":True}
    _lookup["must_be_one"] = True
    _lookup["resource_type"] = "server"
    _lookup["hostname"] = hostname
    _lookup["region"] = stack.aws_default_region
    _info = list(stack.get_resource(**_lookup))[0]

    return _info["instance_id"]

def _get_volume_id(volume_name):

    _lookup = {"must_exists":True}
    _lookup["must_be_one"] = True
    _lookup["name"] = volume_name
    _lookup["resource_type"] = "ebs_volume"
    _lookup["region"] = stack.aws_default_region
    _info = list(stack.get_resource(**_lookup))[0]

    return _info["volume_id"]

def run(stackargs):

    import json

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="bastion_hostname")
    stack.parse.add_required(key="mongodb_hosts")
    stack.parse.add_required(key="mongodb_cluster")
    stack.parse.add_required(key="ssh_keyname")

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

    stack.parse.add_optional(key="volume_mountpoint",default="/var/lib/mongodb")
    stack.parse.add_optional(key="volume_fstype",default="xfs")
    stack.parse.add_optional(key="docker_exec_env",default="elasticdev/ansible-run-env")

    # Add Execution Group
    # Testingyoyo
    # ubuntu 18.04 - install docker with regular hostgroup and shell scripting

    #stack.add_hostgroups("elasticdev:::aws::config_vol")
    stack.add_hostgroups("elasticdev:::aws::config_vol")
    stack.add_hostgroups("elasticdev:::mongodb::ubuntu_vendor_setup")
    stack.add_hostgroups("elasticdev:::mongodb::ubuntu_vendor_init_replica")

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

    # collect mongodb_hosts info
    public_ips = []
    private_ips = []
    mongodb_hosts_info = []

    _lookup = {"must_exists":True,"must_be_one":True}
    _lookup["resource_type"] = "server"

    mongodb_hosts = stack.to_list(stack.mongodb_hosts)

    for mongodb_host in mongodb_hosts:

        _lookup["hostname"] = mongodb_host
        _host_info = list(stack.get_resource(**_lookup))[0]
        mongodb_hosts_info.append(_host_info)

        stack.logger.debug_highlight('mongo hostname {}, found public_ip address "{}"'.format(mongodb_host,
                                                                                              _host_info["public_ip"]))

        if _host_info["public_ip"] not in public_ips: public_ips.append(_host_info["public_ip"])
        if _host_info["private_ip"] not in private_ips: private_ips.append(_host_info["private_ip"])

    ###############################################################
    # mount volumes
    ###############################################################
    for mongodb_host_info in mongodb_hosts_info:

        env_vars = {"METHOD":"create"}
        env_vars["STATEFUL_ID"] = stack.random_id(size=10)
        env_vars["ANS_VAR_volume_fstype"] = stack.volume_fstype
        env_vars["ANS_VAR_volume_mountpoint"] = stack.volume_mountpoint
        env_vars["ANS_VAR_private_key"] = private_key
        env_vars["ANS_VAR_exec_ymls"] = "entry_point/20-format.yml,entry_point/30-mount.yml"
        env_vars["ANS_VAR_host_ips"] = mongodb_host_info["private_ip"]

        inputargs = {"display":True}
        inputargs["human_description"] = 'Format and mount volume on mongodb_host "{}" fstype {} mountpoint {}'.format(mongodb_host_info["hostname"],
                                                                                                                       stack.volume_fstype,
                                                                                                                       stack.volume_mountpoint)
        inputargs["env_vars"] = json.dumps(env_vars)
        inputargs["stateful_id"] = env_vars["STATEFUL_ID"]
        inputargs["automation_phase"] = "infrastructure"
        stack.add_groups_to_host(groups=stack.config_vol,hostname=stack.bastion_hostname)

    return stack.get_results()

    ################################################################
    ## Testing one change at a time below
    ################################################################
    ## Testingyoyo
    ## Testingyoyo
    ## Testingyoyo
    ## Testingyoyo
    ## Testingyoyo
    ################################################################
    ## Setup Ansible for MongoDb
    ## templify ansible and create necessary files
    ################################################################
    #human_description = "Setting up Ansible for MongoDb"
    #inputargs = {"display":True}

    #env_vars = {"ANS_VAR_mongodb_pem":mongodb_pem}
    #env_vars["ANS_VAR_mongodb_keyfile"] = mongodb_keyfile
    #env_vars["ANS_VAR_private_key"] = private_key
    #env_vars["ANS_VAR_mongodb_version"] = stack.mongodb_version
    #env_vars["ANS_VAR_mongodb_port"] = stack.mongodb_port
    #env_vars["ANS_VAR_mongodb_data_dir"] = stack.mongodb_data_dir
    #env_vars["ANS_VAR_mongodb_storage_engine"] = stack.mongodb_storage_engine
    #env_vars["ANS_VAR_mongodb_bind_ip"] = stack.mongodb_bind_ip
    #env_vars["ANS_VAR_mongodb_logpath"] = stack.mongodb_logpath
    #env_vars["ANS_VAR_mongodb_public_ips"] = ",".join(public_ips)
    #env_vars["ANS_VAR_mongodb_private_ips"] = ",".join(private_ips)
    #env_vars["ANS_VAR_mongodb_main_ips"] = "{},{}".format(public_ips[0],private_ips[0])
    #env_vars["ANS_VAR_mongodb_username"] = stack.mongodb_username
    #env_vars["ANS_VAR_mongodb_password"] = stack.mongodb_password
    #env_vars["ANS_VAR_mongodb_config_network"] = private_ips[0]
    #env_vars["ANSIBLE_DIR"] = "/var/tmp/ansible"
    #env_vars["docker_exec_env".upper()] = stack.docker_exec_env
    #env_vars["use_docker".upper()] = True
    #env_vars["METHOD"] = "create"

    #env_vars["STATEFUL_ID"] = stack.random_id(size=10)
    #inputargs["env_vars"] = json.dumps(env_vars)
    #inputargs["stateful_id"] = env_vars["STATEFUL_ID"]

    #inputargs["name"] = stack.mongodb_cluster
    #inputargs["human_description"] = human_description
    #stack.add_groups_to_host(groups=stack.ubuntu_vendor_setup,hostname=stack.bastion_hostname)

    ################################################################
    ## installing python
    ################################################################
    #human_description = "Installing python (for Ansible) to mongodb nodes"
    #inputargs = {"display":True}
    #inputargs["name"] = stack.mongodb_cluster

    #env_vars["ANS_VAR_exec_ymls"] = "entry_point/10-install-python.yml"
    #env_vars["STATEFUL_ID"] = stack.random_id(size=10)
    #inputargs["stateful_id"] = env_vars["STATEFUL_ID"]

    #docker_env_fields_keys = env_vars.keys()
    #env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)
    #inputargs["env_vars"] = json.dumps(env_vars)
    #inputargs["human_description"] = human_description
    #stack.add_groups_to_host(groups=stack.ubuntu_vendor_init_replica,hostname=stack.bastion_hostname)

    ################################################################
    ## mongo install and setup
    ################################################################
    #human_description = "Install MongoDb version {} on nodes".format(stack.mongodb_version)

    #inputargs = {"display":True}
    #inputargs["name"] = stack.mongodb_cluster

    #env_vars["ANS_VAR_exec_ymls"] = "entry_point/20-mongo-setup.yml"
    #docker_env_fields_keys = env_vars.keys()
    #env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)
    #inputargs["env_vars"] = json.dumps(env_vars)
    #inputargs["human_description"] = human_description
    #stack.add_groups_to_host(groups=stack.ubuntu_vendor_init_replica,hostname=stack.bastion_hostname)

    ################################################################
    ## mongo init replica
    ################################################################
    #human_description = "Initialize ReplicaSet on Master Node {}/{}".format(public_ips[0],private_ips[0])

    #inputargs = {"display":True}
    #inputargs["name"] = stack.mongodb_cluster

    #env_vars["ANS_VAR_exec_ymls"] = "entry_point/30-mongo-init-replica.yml"
    #docker_env_fields_keys = env_vars.keys()

    #env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)
    #inputargs["env_vars"] = json.dumps(env_vars)
    #inputargs["human_description"] = human_description
    #stack.add_groups_to_host(groups=stack.ubuntu_vendor_init_replica,hostname=stack.bastion_hostname)

    ################################################################
    ## add slave replica nodes
    ################################################################
    #human_description = "Add slave nodes to the master node"

    #inputargs = {"display":True}
    #inputargs["name"] = stack.mongodb_cluster

    #env_vars["ANS_VAR_exec_ymls"] = "entry_point/40-mongo-add-slave-replica.yml"
    #docker_env_fields_keys = env_vars.keys()

    #env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)
    #inputargs["env_vars"] = json.dumps(env_vars)
    #inputargs["human_description"] = human_description
    #stack.add_groups_to_host(groups=stack.ubuntu_vendor_init_replica,hostname=stack.bastion_hostname)

    ################################################################
    ## publish variables
    ################################################################
    #_publish_vars = {"mongodb_cluster":stack.mongodb_cluster}
    #_publish_vars["mongodb_version"] = stack.mongodb_version
    #_publish_vars["mongodb_port"] = stack.mongodb_port
    #_publish_vars["mongodb_data_dir"] = stack.mongodb_data_dir
    #_publish_vars["mongodb_storage_engine"] = stack.mongodb_storage_engine
    #_publish_vars["mongodb_bind_ip"] = stack.mongodb_bind_ip
    #_publish_vars["mongodb_logpath"] = stack.mongodb_logpath
    #_publish_vars["mongodb_public_ips"] = ",".join(public_ips)
    #_publish_vars["mongodb_private_ips"] = ",".join(private_ips)

    #if stack.publish_creds:
    #    _publish_vars["mongodb_username"] = stack.mongodb_username
    #    _publish_vars["mongodb_password"] = stack.mongodb_password

    #stack.publish(_publish_vars)
    ## Testingyoyo
    ## Testingyoyo
    ## Testingyoyo
    ## Testingyoyo

    #return stack.get_results()
