def default():
    
    task = {}
    env_vars = []
    shelloutconfigs = []

    shelloutconfigs.append('elasticdev:::mongodb::create_ansible_replica_hosts')

    task['method'] = 'shelloutconfig'
    task['metadata'] = {'env_vars': env_vars,
                        'shelloutconfigs': shelloutconfigs
                        }

    return task

