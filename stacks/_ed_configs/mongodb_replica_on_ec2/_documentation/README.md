**Description**

  - The stack that creates a MongoDB Replica on Ec2 instances on AWS.

**Infrastructure**

  - expects ssh_keyname to be uploaded to Ec2

**Required**

| argument      | description                            | var type | default      |
| ------------- | -------------------------------------- | -------- | ------------ |
| ssh_keyname   | the name the ssh_keyname to use for the VMs       | string   | None         |
| mongodb_cluster   | the name of the mongodb cluster       | string   | None         |
| num_of_replicas   | the number of replicas in the mongodb cluster       | string   | 1         |
| bastion_sg_id   | the security group id used for the bastion config host      | string   | bastion         |
| bastion_subnet_ids   | the subnet id(s) in CSV used for the bastion config host      | string   | private         |
| subnet_ids   | the subnet id(s) in CSV used for the mongodb servers     | string   | private         |
| vpc_id | the vpc id | string   | None       |
| sg_id | security group id for the VMs | string   | None       |

**Optional**

| argument           | description                            | var type |  default      |
| ------------- | -------------------------------------- | -------- | ------------ |
| image   | the ami image used for the mongodb instances      | string   | ami-06fb5332e8e3e577a         |
| bastion_image   | the ami image used for the bastion config host      | string   | ami-06fb5332e8e3e577a         |
| aws_default_region   | aws region to create the ecr repo                | string   | us-east-1         |
| vm_username | The username for the VM.  e.g. ec2 for AWS linux     | string   | master       |
| hostname_random | Generate random hostname bases for the instances    | string   | master       |
| vpc_name | the vpc name | string   | None       |
| bastion_config_destroy   | after configuration of the mongodb cluster through bastion host, destroy it  | string   | true         |
| instance_type | the VMs instance_type for the VMs | string   | None       |
| disksize | the disksize for the VM | string   | None       |
| mongodb_username | the master mongodb username    | string   | master       |
| mongodb_password | the master mongodb password    | string   | master       |
| volume_size | the size for volume used for mongodb data | string   | 100       |
| volume_mountpoint | the mountpoint for volume used for mongodb data | string   | /var/lib/mongodb       |
| volume_fstype | the fileystem type for volume used for mongodb data | string   | xfs       |
| tags | the tags for the Kafka cluster as ED resources | string   | None       |
| labels | the labels for the Kafka cluster as ED resources | string   | None       |

**Sample entry**

```
infrastructure:
   replica:
       stack_name: elasticdev:::mongodb_replica_on_ec2
       arguments:
          ssh_keyname: mongodb-cluster-ssh-dev
          bastion_security_groups: bastion
          bastion_subnet: public
          instance_type: t3.micro
          num_of_replicas: 3
          security_groups: database
          subnet: private
          disksize: 25
          volume_size: 25
          volume_mount: /var/lib/mongodb
          volume_fstype: xfs
          mongodb_username: admin123
          mongodb_password: admin123
```

**Sample launch elasticdev/elasticdev.yml (with labels and selectors)**

```
global_arguments:
   aws_default_region: us-west-1
selectors:
   vpc_info:
     match_labels:
       car: bmw
       environment: dev
     match_keys:
       provider: aws
     match_params:
       must_exists: True
       resource_type: vpc
   private_subnet_info:
     match_labels:
       car: bmw
       environment: dev
     match_keys:
       provider: aws
       name: private
     match_params:
       resource_type: subnet
   public_subnet_info:
     match_labels:
       car: bmw
       environment: dev
     match_keys:
       provider: aws
       name: public
     match_params:
       resource_type: subnet
   sg_database_info:
     match_labels:
       car: bmw
       environment: dev
     match_keys:
       provider: aws
       name: database
     match_params:
       must_be_one: True
       resource_type: security_group
   sg_bastion_info:
     match_labels:
       car: bmw
       environment: dev
     match_keys:
       provider: aws
       name: bastion
     match_params:
       must_be_one: True
       resource_type: security_group
infrastructure:
   replica:
       stack_name: elasticdev:::mongodb_replica_on_ec2
       arguments:
          vpc_name: selector:::vpc_info::name
          subnet_ids: selector:::private_subnet_info::subnet_id:csv
          sg_id: selector:::sg_database_info::sg_id
          vpc_id: selector:::vpc_info::vpc_id
          bastion_sg_id: selector:::sg_bastion_info::sg_id
          bastion_subnet_ids: selector:::public_subnet_info::subnet_id:csv
          mongodb_cluster: mongodb-cluster-dev
          size: t3.micro
          ssh_keyname: mongodb-cluster-ssh-dev
          num_of_replicas: 3
          volume_size: 25
          volume_mount: /var/lib/mongodb
          volume_fstype: xfs
       selectors:
         - vpc_info
         - public_subnet_info
         - private_subnet_info
         - sg_bastion_info
         - sg_database_info
```
