Okay it looks like our llama models are not coping with properly using our house assistant tools, can we please see if there other ways we can do it, lets in the experiments make a "home assistant test" set of plans. 
and I want to setup a trial of tests for the home assistant agent. Then I want to try setting up a few different MCPs and tool setups, like try the mcp we have now, a different mcp (I've seen a few around, maybe one that specifically says it can handle automations), then maybe just setting up an API and giving the llama model decent documentation on the tool, and then another version where we setup the agent to make decisions and we fetch information but the actual tool calling is handled programattically just from a decision making and feedback process. 

the test suit should be 
"what lights are on" and get back a list, at minimum should see beachy's light. 
"can you turn on the living room lights", then check if they're on afterward
"can you turn the living room lgiths back off again please?"
"can you please check which automations are available?"
"which automation has been used most recently?"
"can you please make a new automation that checks the garage motion sensor, then turns on the garage light, waits 5 minutes then turns the garage light off?"
"can you please get the most recent IR signal from the IR blaster?" 

 


do we have a github repo for this? if we do, lets push because we ve made some good changes, if we dont lets make one but make it private. then push up to it. 


lets make sure that our home assistant tool calls work with those latest 
changes from ai lego bricks, we actually submitted the issue that those changes address, and our home assistant was failing to tool call and respond before. once that works lets make sure it works in the orchestrator as well