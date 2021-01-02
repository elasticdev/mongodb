def default():
    
    task = {}
    env_vars = []
    shelloutconfigs = []

    shelloutconfigs.append('elasticdev:::ansible::write_ssh_key')

    task['method'] = 'shelloutconfig'
    task['metadata'] = {'env_vars': env_vars,
                        'shelloutconfigs': shelloutconfigs
                        }

    return task
