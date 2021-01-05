def _get_instance_info(stack,hostname):

    _lookup = {"must_exists":True}
    _lookup["must_be_one"] = True
    _lookup["resource_type"] = "server"
    _lookup["hostname"] = hostname
    _lookup["region"] = stack.aws_default_region
    _info = list(stack.get_resource(**_lookup))[0]

    return _info["instance_id"]

def _get_volume_id(stack,volume_name):

    _lookup = {"must_exists":True}
    _lookup["must_be_one"] = True
    _lookup["name"] = volume_name
    _lookup["resource_type"] = "ebs_volume"
    _lookup["region"] = stack.aws_default_region
    _info = list(stack.get_resource(**_lookup))[0]

    return _info["volume_id"]

def _get_ssh_key(stack):

    _lookup = {"must_exists":True}
    _lookup["resource_type"] = "ssh_key_pair"
    _lookup["name"] = stack.ssh_keyname

    return list(stack.get_resource(decrypt=True,**_lookup))[0]["private_key"]

def _get_mongodb_pem(stack):

    _lookup = {"must_exists":True}
    _lookup["resource_type"] = "ssl_pem"
    _lookup["provider"] = "openssl"
    _lookup["name"] = "{}.pem".format(stack.mongodb_cluster)

    return list(stack.get_resource(decrypt=True,**_lookup))[0]["contents"]

    # lookup mongodb keyfile needed for secure mongodb replication
def _get_mongodb_keyfile(stack):
    _lookup = {"must_exists":True}
    _lookup["provider"] = "openssl"
    _lookup["resource_type"] = "symmetric_key"
    _lookup["name"] = "{}_keyfile".format(stack.mongodb_cluster)

    return list(stack.get_resource(decrypt=True,**_lookup))[0]["contents"]

def _get_mongodb_hosts(stack):

    public_ips = []
    private_ips = []
    mongodb_hosts_info = []

    _lookup = {"must_exists":True,"must_be_one":True}
    _lookup["resource_type"] = "server"

    mongodb_hosts = stack.to_list(stack.mongodb_hosts)

    for mongodb_host in mongodb_hosts:

        _lookup["hostname"] = mongodb_host
        _host_info = list(stack.get_resource(**_lookup))[0]

        # insert volume_name 
        # ref 45304958324
        _host_info["volume_name"] = "{}-{}".format(mongodb_host,stack.volume_mountpoint).replace("/","-").replace(".","-")

        mongodb_hosts_info.append(_host_info)

        stack.logger.debug_highlight('mongo hostname {}, found public_ip address "{}"'.format(mongodb_host,
                                                                                              _host_info["public_ip"]))

        if _host_info["public_ip"] not in public_ips: public_ips.append(_host_info["public_ip"])
        if _host_info["private_ip"] not in private_ips: private_ips.append(_host_info["private_ip"])

    return mongodb_hosts_info,public_ips,private_ips

def run(stackargs):

    import json

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="bastion_hostname")
    stack.parse.add_required(key="mongodb_hosts")
    stack.parse.add_required(key="mongodb_cluster")
    stack.parse.add_required(key="ssh_keyname")
    stack.parse.add_required(key="aws_default_region")

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
    stack.parse.add_optional(key="device_name",default="/dev/xvdc")
    stack.parse.add_optional(key="terraform_docker_exec_env",default="elasticdev/terraform-run-env")
    stack.parse.add_optional(key="ansible_docker_exec_env",default="elasticdev/ansible-run-env")

    # Add execgroup
    stack.add_execgroup("elasticdev:::aws::attach_volume_to_ec2")

    # Add host group
    stack.add_hostgroups("elasticdev:::ubuntu::18.04-docker","install_docker")
    stack.add_hostgroups("elasticdev:::ansible::ubuntu-18.04","install_python")
    #stack.add_hostgroups("elasticdev:::aws::attach_volume_to_ec2","attach_volume_to_ec2")
    stack.add_hostgroups("elasticdev:::aws::config_vol","config_vol")
    stack.add_hostgroups("elasticdev:::mongodb::ubuntu_vendor_setup","ubuntu_vendor_setup")
    stack.add_hostgroups("elasticdev:::mongodb::ubuntu_vendor_init_replica","ubuntu_vendor_init_replica")

    # Initialize 
    stack.init_variables()
    stack.init_execgroups()
    stack.init_hostgroups()

    # get ssh_key
    private_key = _get_ssh_key(stack)

    # get mongodb pem key
    mongodb_pem = _get_mongodb_pem(stack)

    # lookup mongodb keyfile needed for secure mongodb replication
    mongodb_keyfile = _get_mongodb_keyfile(stack)

    # collect mongodb_hosts info
    mongodb_hosts_info,public_ips,private_ips = _get_mongodb_hosts(stack)

    # install docker on bastion hosts
    inputargs = {"display":True}
    inputargs["human_description"] = "Install Docker on bastion {}".format(stack.bastion_hostname)
    inputargs["automation_phase"] = "infrastructure"
    inputargs["hostname"] = stack.bastion_hostname
    inputargs["groups"] = stack.install_docker
    stack.add_groups_to_host(**inputargs)

    # install python on mongodb_hosts
    env_vars = {"METHOD":"create"}
    env_vars["STATEFUL_ID"] = stack.random_id(size=10)
    env_vars["ANS_VAR_private_key"] = private_key
    env_vars["ANS_VAR_exec_ymls"] = "entry_point/10-install-python.yml"
    env_vars["ANSIBLE_DIR"] = "/var/tmp/ansible"
    env_vars["ANS_VAR_host_ips"] = ",".join(private_ips)

    inputargs = {"display":True}
    inputargs["human_description"] = 'Install Python for Ansible'
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["stateful_id"] = env_vars["STATEFUL_ID"]
    inputargs["automation_phase"] = "infrastructure"
    inputargs["hostname"] = stack.bastion_hostname
    inputargs["groups"] = stack.install_python

    stack.add_groups_to_host(**inputargs)

    # mount volumes on mongodb_hosts
    # install mongodb on mongodb_hosts

    for mongodb_host_info in mongodb_hosts_info:

        # Call to create the server with shellout script
        env_vars = {"AWS_DEFAULT_REGION":stack.aws_default_region}
        env_vars["STATEFUL_ID"] = stack.random_id(size=10)
 
        instance_id = _get_instance_info(stack,mongodb_host_info["hostname"])

        env_vars["TF_VAR_aws_default_region"] = stack.aws_default_region
        env_vars["TF_VAR_device_name"] = stack.device_name
        env_vars["TF_VAR_instance_id"] = instance_id
        env_vars["TF_VAR_volume_id"] = _get_volume_id(stack,mongodb_host_info["volume_name"])
        env_vars["docker_exec_env".upper()] = stack.terraform_docker_exec_env
        env_vars["resource_type".upper()] = "ebs_volume_attach"
        env_vars["RESOURCE_TAGS"] = "{},{},{},{}".format("ebs","ebs_attach", "aws", stack.aws_default_region)
        env_vars["METHOD"] = "create"
        env_vars["use_docker".upper()] = True

        _docker_env_fields_keys = env_vars.keys()
        _docker_env_fields_keys.append("AWS_ACCESS_KEY_ID")
        _docker_env_fields_keys.append("AWS_SECRET_ACCESS_KEY")
        _docker_env_fields_keys.append("AWS_DEFAULT_REGION")
        _docker_env_fields_keys.remove("METHOD")
        env_vars["DOCKER_ENV_FIELDS"] = ",".join(_docker_env_fields_keys)

        #insert_env_vars = ["AWS_ACCESS_KEY_ID"]
        #insert_env_vars.append("AWS_SECRET_ACCESS_KEY")
  
        inputargs = {"display":True}
        inputargs["human_description"] = 'Attaches ebs volume to instance_id "{}"'.format(instance_id)
        inputargs["env_vars"] = json.dumps(env_vars)
        inputargs["stateful_id"] = env_vars["STATEFUL_ID"]
        inputargs["automation_phase"] = "infrastructure"
        stack.attach_volume_to_ec2.insert(**inputargs)

        #inputargs["insert_env_vars"] = insert_env_vars
        #inputargs["hostname"] = stack.bastion_hostname
        #inputargs["groups"] = stack.attach_volume_to_ec2
        #stack.add_groups_to_host(**inputargs)

    # mount volumes
    human_description = 'Format and mount volume on mongodb hosts fstype {} mountpoint {}'.format(stack.volume_fstype,
                                                                                                  stack.volume_mountpoint)
    env_vars = {"METHOD":"create"}
    env_vars["docker_exec_env".upper()] = stack.ansible_docker_exec_env
    env_vars["ANSIBLE_DIR"] = "/var/tmp/ansible"
    env_vars["STATEFUL_ID"] = stack.random_id(size=10)
    env_vars["ANS_VAR_volume_fstype"] = stack.volume_fstype
    env_vars["ANS_VAR_volume_mountpoint"] = stack.volume_mountpoint
    env_vars["ANS_VAR_private_key"] = private_key
    env_vars["ANS_VAR_exec_ymls"] = "entry_point/20-format.yml,entry_point/30-mount.yml"
    env_vars["ANS_VAR_host_ips"] = ",".join(private_ips)

    inputargs = {"display":True}
    inputargs["human_description"] = human_description
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["stateful_id"] = env_vars["STATEFUL_ID"]
    inputargs["automation_phase"] = "infrastructure"
    inputargs["hostname"] = stack.bastion_hostname
    inputargs["groups"] = stack.config_vol

    stack.add_groups_to_host(**inputargs)

    ###############################################################
    # standard env variables for creating the mongodb cluster
    # they will all use the same stateful_id since the files
    # don't change.
    ###############################################################

    stateful_id = stack.random_id(size=10)

    base_env_vars = {"METHOD":"create"}
    base_env_vars["docker_exec_env".upper()] = stack.ansible_docker_exec_env
    base_env_vars["ANSIBLE_DIR"] = "/var/tmp/ansible"
    base_env_vars["STATEFUL_ID"] = stateful_id
    base_env_vars["ANS_VAR_mongodb_pem"] = mongodb_pem
    base_env_vars["ANS_VAR_mongodb_keyfile"] = mongodb_keyfile
    base_env_vars["ANS_VAR_private_key"] = private_key
    base_env_vars["ANS_VAR_mongodb_version"] = stack.mongodb_version
    base_env_vars["ANS_VAR_mongodb_port"] = stack.mongodb_port
    base_env_vars["ANS_VAR_mongodb_data_dir"] = stack.mongodb_data_dir
    base_env_vars["ANS_VAR_mongodb_storage_engine"] = stack.mongodb_storage_engine
    base_env_vars["ANS_VAR_mongodb_bind_ip"] = stack.mongodb_bind_ip
    base_env_vars["ANS_VAR_mongodb_logpath"] = stack.mongodb_logpath
    base_env_vars["ANS_VAR_mongodb_username"] = stack.mongodb_username
    base_env_vars["ANS_VAR_mongodb_password"] = stack.mongodb_password
    base_env_vars["ANS_VAR_mongodb_config_network"] = private_ips[0]
    base_env_vars["ANS_VAR_mongodb_cluster"] = stack.mongodb_cluster
    base_env_vars["ANS_VAR_mongodb_main_ips"] = "{},{}".format(public_ips[0],private_ips[0])
    base_env_vars["ANS_VAR_mongodb_public_ips"] = ",".join(public_ips)
    base_env_vars["ANS_VAR_mongodb_private_ips"] = ",".join(private_ips)

    # This is the configuration ips that bastion hosts will connect
    base_env_vars["ANS_VAR_mongodb_config_ips"] = ",".join(private_ips)

    #inputargs["name"] = stack.mongodb_cluster

    ###############################################################
    # deploy files Ansible for MongoDb
    ###############################################################

    human_description = "Setting up Ansible for MongoDb"

    inputargs = {"display":True}
    inputargs["human_description"] = human_description
    inputargs["env_vars"] = json.dumps(base_env_vars.copy())
    inputargs["stateful_id"] = stateful_id
    inputargs["automation_phase"] = "infrastructure"
    inputargs["hostname"] = stack.bastion_hostname
    inputargs["groups"] = stack.ubuntu_vendor_setup

    stack.add_groups_to_host(**inputargs)

    ###############################################################
    # mongo install and setup
    ###############################################################
    human_description = "Install MongoDb version {} on nodes".format(stack.mongodb_version)

    env_vars = base_env_vars.copy()
    env_vars["ANS_VAR_exec_ymls"] = "entry_point/20-mongo-setup.yml"
    docker_env_fields_keys = env_vars.keys()
    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)

    inputargs = {"display":True}
    inputargs["human_description"] = human_description
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["stateful_id"] = stateful_id
    inputargs["automation_phase"] = "infrastructure"
    inputargs["hostname"] = stack.bastion_hostname
    inputargs["groups"] = stack.ubuntu_vendor_init_replica

    stack.add_groups_to_host(**inputargs)

    ###############################################################
    # mongo init replica
    ###############################################################
    human_description = "Initialize ReplicaSet on Master Node {}/{}".format(public_ips[0],private_ips[0])

    env_vars = base_env_vars.copy()
    env_vars["ANS_VAR_exec_ymls"] = "entry_point/30-mongo-init-replica.yml"
    docker_env_fields_keys = env_vars.keys()
    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)

    inputargs = {"display":True}
    inputargs["human_description"] = human_description
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["stateful_id"] = stateful_id
    inputargs["automation_phase"] = "infrastructure"
    inputargs["hostname"] = stack.bastion_hostname
    inputargs["groups"] = stack.ubuntu_vendor_init_replica

    stack.add_groups_to_host(**inputargs)

    ###############################################################
    # add slave replica nodes
    ###############################################################
    human_description = "Add slave nodes to the master node"

    #inputargs["name"] = stack.mongodb_cluster

    env_vars = base_env_vars.copy()
    env_vars["ANS_VAR_exec_ymls"] = "entry_point/40-mongo-add-slave-replica.yml"
    docker_env_fields_keys = env_vars.keys()
    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)

    inputargs = {"display":True}
    inputargs["human_description"] = human_description
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["stateful_id"] = stateful_id
    inputargs["automation_phase"] = "infrastructure"
    inputargs["hostname"] = stack.bastion_hostname
    inputargs["groups"] = stack.ubuntu_vendor_init_replica

    stack.add_groups_to_host(**inputargs)

    ###############################################################
    # publish variables
    ###############################################################
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
