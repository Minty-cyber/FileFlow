import logfire

logfire.configure(token="pylf_v1_us_F67kvTz3gbcGwM7xp6SxwTrDx212gnPS2Q9rC1Ysyg9f")

logfire.info('Hello, {name}!', name='Destiny')
logfire.error("This is an example error!")
logfire.exception("This is an example exception!")
logfire.debug("This is an example debug context")
logfire.warn("This is an example warn!")