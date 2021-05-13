**Description**

  - The stack that creates a MongoDB Replica on Ec2 instances on AWS.

**Infrastructure**

  - expects ssh_keyname to be uploaded to Ec2
  - expects vpc and security groups to be already configured and loaded in ED

**Required**

| argument      | description                            | var type | default      |
| ------------- | -------------------------------------- | -------- | ------------ |
| ssh_keyname   | the name the ssh_keyname to use for the VMs       | string   | None         |
| mongodb_cluster   | the name of the mongodb cluster       | string   | None         |
| num_of_replicas   | the number of replicas in the mongodb cluster       | string   | 1         |
| image   | the ami image used for the mongodb instances      | string   | ami-06fb5332e8e3e577a         |
| bastion_security_groups   | the security group used for the bastion config host      | string   | bastion         |
| bastion_subnet   | the subnet or subnet label used for the bastion config host      | string   | private         |
| bastion_image   | the ami image used for the bastion config host      | string   | ami-06fb5332e8e3e577a         |

**Optional**

| argument           | description                            | var type |  default      |
| ------------- | -------------------------------------- | -------- | ------------ |
| aws_default_region   | aws region to create the ecr repo                | string   | us-east-1         |
| vm_username | The username for the VM.  e.g. ec2 for AWS linux     | string   | master       |
| security_groups | name of the security groups entered into ED resources to use for the VMs | string   | None       |
| vpc_name | name of the vpc entered into ED resources to use for the VMs | string   | None       |
| subnet | name of the subnet entered into ED resources to use for the VMs | string   | None       |
| instance_type | the VMs instance_type for the VMs | string   | None       |
| disksize | the disksize for the VM | string   | None       |
| tags | the tags for the Kafka cluster as ED resources | string   | None       |
| labels | the labels for the Kafka cluster as ED resources | string   | None       |
| mongodb_username | the master mongodb username    | string   | master       |
| mongodb_password | the master mongodb password    | string   | master       |
| volume_size | the size for volume used for mongodb data | string   | 100       |
| volume_mountpoint | the mountpoint for volume used for mongodb data | string   | /var/lib/mongodb       |
| volume_fstype | the fileystem type for volume used for mongodb data | string   | xfs       |

**Sample entry**

```
infrastructure:
   replica:
       stack_name: elasticdev:::mongodb_replica_on_ec2
       arguments:
          bastion_config_destroy: true
          bastion_security_groups: bastion
          bastion_subnet: public
          hostname_random: true
          size: t3.micro
          ssh_keyname: mongodb-cluster-ssh-dev
          num_of_replicas: 3
          security_groups: database
          subnet: private
          disksize: 25
          ip_key: public_ip
          volume_size: 25
          volume_mount: /var/lib/mongodb
          volume_fstype: xfs
          mongodb_username: admin123
          mongodb_password: admin123
```

**Sample launch elasticdev/elasticdev.yml**

```
global_arguments:
   aws_default_region: ap-southeast-1
   vpc_name: kafka-cluster-dev-vpc
   kafka_cluster: kafka-cluster-dev
infrastructure:
   ssh_upload:
       stack_name: elasticdev:::ec2_ssh_upload
       arguments:
          name: kafka-cluster-ssh-dev
          clobber: True
       credentials:
           - reference: aws_2
             orchestration: true
   vpc:
       stack_name: elasticdev:::aws_vpc_and_security_group
       arguments:
          main_network_block: 10.43.0.0/16
          tier_level: "3"
          enable_nat_gateway: true
          single_nat_gateway: true
          enable_dns_hostnames: true
          reuse_nat_ips: true
          one_nat_gateway_per_az: false
          use_docker: True
          labels: "db_type:kafka"
          tags: "kafka,database"
       credentials:
           - reference: aws_2
             orchestration: true
   kafka:
       stack_name: elasticdev:::kafka_on_ec2
       dependencies:
          - infrastructure::vpc
          - infrastructure::ssh_upload
       arguments:
          image: ami-03aad423811bbee56
          bastion_image: ami-03aad423811bbee56
          bastion_config_destroy: true
          bastion_security_groups: bastion
          bastion_subnet: public
          hostname_random: true
          size: t3.micro
          ssh_keyname: kafka-cluster-ssh-dev
          num_of_replicas: 5
          security_groups: database
          subnet: private
          disksize: 25
       credentials:
           - reference: aws_2
             orchestration: true
```
