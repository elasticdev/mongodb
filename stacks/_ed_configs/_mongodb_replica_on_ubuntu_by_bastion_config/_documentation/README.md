**Description**

  - The stack that creates a MongoDB using Virtual Machines through a basion host since the MongoDB is in a protected private network.

**Infrastructure**

  - expects ssh_keyname to be uploaded to Ec2

**Required**

| argument      | description                            | var type | default      |
| ------------- | -------------------------------------- | -------- | ------------ |
| bastion_hostname   | the hostname for the bastion used to install and configure mongodb on VMs       | string   | None         |
| mongodb_hosts   | the hostnames for he mongodb_hosts in the replica set separated by a comma       | string (csv)   | None         |
| mongodb_cluster   | the name of the mongodb cluster       | string   | None         |
| ssh_keyname   | the name the ssh_keyname to use for the VMs       | string   | None         |
| aws_default_region   | aws region to create the ecr repo                | string   | us-east-1         |
| num_of_replicas   | the number of replicas in the mongodb cluster       | string   | 1         |
| bastion_sg_id   | the security group id used for the bastion config host      | string   | bastion         |
| bastion_subnet_ids   | the subnet id(s) in CSV used for the bastion config host      | string   | private         |
| subnet_ids   | the subnet id(s) in CSV used for the mongodb servers     | string   | private         |
| vpc_id | the vpc id | string   | None       |
| sg_id | security group id for the VMs | string   | None       |

**Optional**

| argument           | description                            | var type |  default      |
| ------------- | -------------------------------------- | -------- | ------------ |
| mongodb_username | the master mongodb username    | string   | <random>       |
| mongodb_password | the master mongodb password    | string   | <random>       |
| vm_username | The username for the VM.  e.g. ec2 for AWS linux     | string   | master       |
| mongodb_data_dir | the directory for mongodb data | string   | /var/lib/mongodb       |
| mongodb_storage_engine | the storage engine for mongodb | string   | wiredTiger       |
| mongodb_version | the version for mongodb | string   | 4.0.3       |
| mongodb_port | the port for mongodb | string   | 27017       |
| mongodb_bind_ip | the bind ip for mongodb to listen | string   | 0.0.0.0       |
| mongodb_logpath | the logpath for mongodb | string   | /var/log/mongodb/mongod.log      |
| publish_creds | publish the credentials for mongodb for ED output in UI | string   | True     |
| use_docker | the use of docker for automation execution | string   | True     |
| volume_fstype | the fileystem type for volume used for mongodb data | string   | xfs       |
| device_name | the device name for the extra data volume for mongodb data | string   | /dev/xvdc       |
| volume_mountpoint | the volume mountpoint for mongodb data | string   | /var/lib/mongodb       |
| terraform_docker_exec_env | the docker container for terraform execution | string   | elasticdev/terraform-run-env       |
| ansible_docker_exec_env | the docker container for ansible execution | string   | elasticdev/ansible-run-env       |
