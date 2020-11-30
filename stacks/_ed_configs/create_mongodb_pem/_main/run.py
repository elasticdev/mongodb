def run(stackargs):

    import json

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="basename")

    # Add shelloutconfig dependencies
    stack.add_shelloutconfig('elasticdev:::mongodb::create_keys')

    # Initialize 
    stack.init_variables()
    stack.init_shelloutconfigs()

    # Create mongodb.pem for MongoDb SSL
    env_vars = {"INSERT_IF_EXISTS":True}
    env_vars["NAME"] = stack.basename
    env_vars["METHOD"] = "create_ssl"

    inputargs = {"display":True}
    inputargs["human_description"] = 'Create mongodb.pem for MongoDb SSL'
    inputargs["env_vars"] = json.dumps(env_vars)
    inputargs["automation_phase"] = "infrastructure"
    stack.create_keys.resource_exec(**inputargs)

    return stack.get_results()
