def run(instructargs):

    import json

    stack = newStack(instructargs)

    # Add required variables
    stack.parse.add_required(key="first_name")
    stack.parse.add_required(key="last_name")

    # Add required variables with default
    stack.parse.add_required(key="city",default="boston")

    # Add optional variables
    stack.parse.add_optional(key="parents")

    # Initialize Variables in stack
    stack.init_variables()

    # Set variables
    stack.set_variable("country","usa")

    if not hasattr(stack,"parents"):

        parents = {"father":"bob",
                   "mom":"jeanne",
                   "city_of_origin":"denver"}

        stack.set_variable("parents",json.dumps(parents))

    # sample log
    stack.logger.aggmsg("",new=True)
    stack.logger.aggmsg("Summary")
    stack.logger.aggmsg("")
    stack.logger.aggmsg("first_name = {}".format(stack.first_name))
    stack.logger.aggmsg("last_name = {}".format(stack.last_name))
    stack.logger.aggmsg("city = {}".format(stack.city))
    stack.logger.aggmsg("parents = {}".format(stack.parents))
    stack.logger.aggmsg("")
    stack.logger.aggmsg("",prt=True,cmethod="debug_highlight")

    return stack.get_results()
