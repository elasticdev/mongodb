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

    # Add Execution Group
    stack.add_execgroup("elasticdev:::mongodb::ubuntu_vendor")

    # stack.add_shelloutconfig('elasticdev:::mongodb::create_keys')
    #stack.init_substacks()
    #stack.init_shelloutconfigs()

    # Initialize 
    stack.init_variables()
    stack.init_execgroups()

    _lookup = {"must_exists":True}
    _lookup["resource_type"] = "security_group"
    _lookup["provider"] = "openssl"
    _lookup["name"] = security_group_name
    _lookup["vpc"] = stack.vpc_name
    _lookup["region"] = stack.aws_default_region
    _lookup["search_keys"] = "vpc"
    _sg_id = list(stack.get_resource(**_lookup))[0]["sg_id"]

    # Testingyoyo

    # Execute execgroup
    env_vars = {"MONGODB_USERNAME":stack.mongodb_username}
    env_vars["mongodb_password".upper()] = stack.mongodb_password
    env_vars["ED_TEMPLATE_VARS"] = "{},{}".format("mongodb_password".upper(),
                                                  "mongodb_username",upper())

    env_vars["DB_SUBNET_NAME"] = stack.db_subnet_name
    env_vars["RDS_MASTER_USERNAME"] = stack.master_username
    env_vars["RDS_MASTER_PASSWORD"] = stack.master_password
    env_vars["SECURITY_GROUP_IDS"] = ",".join(_sg_ids)
    env_vars["SUBNET_IDS"] = _get_subnet_ids(vpc_info,subnet_names=stack.subnet_names)
    env_vars["ALLOCATED_STORAGE"] = stack.allocated_storage
    env_vars["ENGINE"] = stack.engine
    env_vars["ENGINE_VERSION"] = stack.engine_version
    env_vars["INSTANCE_CLASS"] = stack.instance_class
    env_vars["MULTI_AZ"] = stack.multi_az
    env_vars["STORAGE_TYPE"] = stack.storage_type
    env_vars["PUBLICLY_ACCESSIBLE"] = stack.publicly_accessible
    env_vars["STORAGE_ENCRYPTED"] = stack.storage_encrypted
    env_vars["ALLOW_MAJOR_VERSION_UPGRADE"] = stack.allow_major_version_upgrade
    env_vars["AUTO_MINOR_VERSION_UPGRADE"] = stack.auto_minor_version_upgrade
    env_vars["SKIP_FINAL_SNAPSHOT"] = stack.skip_final_snapshot
    env_vars["PORT"] = stack.port
    env_vars["resource_type".upper()] = stack.resource_type
    env_vars["RESOURCE_TAGS"] = "{},{},{}".format(stack.resource_type, stack.rds_name, stack.aws_default_region)
    env_vars["AWS_DEFAULT_REGION"] = stack.aws_default_region
    env_vars["TF_VAR_aws_default_region"] = stack.aws_default_region

    env_vars["BACKUP_RETENTION_PERIOD"] = stack.backup_retention_period
    env_vars["BACKUP_WINDOW"] = stack.backup_window
    env_vars["MAINTENANCE_WINDOW"] = stack.maintenance_window

    env_vars["TF_TEMPLATE_VARS"] = ",".join(env_vars.keys())

    env_vars["docker_exec_env".upper()] = stack.docker_exec_env
    env_vars["METHOD"] = "create"
    env_vars["USE_DOCKER"] = True
    env_vars["CLOBBER"] = True

    docker_env_fields_keys = env_vars.keys()
    docker_env_fields_keys.append("AWS_ACCESS_KEY_ID")
    docker_env_fields_keys.append("AWS_SECRET_ACCESS_KEY")
    docker_env_fields_keys.remove("METHOD")

    env_vars["DOCKER_ENV_FIELDS"] = ",".join(docker_env_fields_keys)

    inputargs = {"display":True}
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["name"] = stack.rds_name
    inputargs["stateful_id"] = stack.stateful_id
    inputargs["human_description"] = "Creating RDS {}".format(stack.rds_name)
    stack.rds.insert(**inputargs)


    return stack.get_results()
