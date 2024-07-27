todolist_entity_id = data.get("entity_id")
current_time = datetime.datetime.now()
reset_window = 7

if todolist_entity_id is not None:
    # Get all todolist items
    service_data = {"entity_id": todolist_entity_id}
    all_goals = hass.services.call("todo", "get_items", service_data, blocking=True, return_response=True)

    failed_goals_val = []
    failed_goals = False
    # Loop through all items
    for goal in all_goals[todolist_entity_id]["items"]:
        # Skipping over values without description, summary, or status Not Supported
        if not "description" in goal or not "status" in goal or not len(goal["description"]) > 0:
            logger.info("Skipping "+ goal["summary"] + " has no \"description\"/\"status\"")
            continue
        # Penalize goals passed dues 
        penalize = False
        if "due" in goal and goal["status"] == "needs_action":
            # two different ways to define datetime
            try:
                goal_due = datetime.datetime.strptime(goal["due"], "%Y-%m-%dT%H:%M:%S%z")
            except ValueError:
                goal_due = datetime.datetime.strptime(goal["due"], "%Y-%m-%d")
            if current_time > goal_due:
                penalize = True

        initial_description = goal["description"].split("\n")
        error_budget_left = None
        total_error_budget = None
        remaining_days = reset_window - current_time.weekday()
        final_description = []
        # Create a new goal template if it only contains a number and description
        if initial_description[0].isdigit():
            error_budget_left = int(initial_description[0])
            total_error_budget = error_budget_left
            initial_description.pop(0)
            final_description = initial_description
        else:
            #else find "Error Budget Left" and "Total Error Budget" and get the raw description out
            
            for line in initial_description:
                if "Error Budget Left" in line:
                    error_budget_left = 5
                elif "Total Error Budget" in line:
                    total_error_budget = 5
                elif "Remaining Days" in line:
                    continue
                else:
                    final_description.append(line)
        # if error_budget_left or total_error_budget is missing skip
        if not error_budget_left or not total_error_budget:
            logger.info(f"No \"Error Budget Left\" or \"Total Error Budget\" found in description for %s, skipping" % (goal["summary"]))
            continue

        # deduct penalities
        if penalize:
            error_budget_left -=1
            if error_budget_left == 0:
                failed_goals = True
                failed_goals_val.append(goal["summary"])
        
        # reset error budget
        if remaining_days == reset_window:
            error_budget_left = total_error_budget
        
        # changing description 
        description = '\n'.join(final_description)
        description += f"\nError Budget Left: %d\nTotal Error Budget: %d\nRemaining Days: %d\n" % (error_budget_left, total_error_budget, remaining_days)
        logger.info(description)
        service_data = {"entity_id": todolist_entity_id, "status":"needs_action", "item": goal["summary"], "due_date": current_time.strftime("%Y-%m-%d"), "description": description}
        hass.services.call("todo", "update_item", service_data, False)

    # if failed_goals:
    #     output["failed_goals_val"] = failedGoalHelper(reset_window, failed_goals_val)
    # output["failed_goals"] = failed_goals

        
# def getNumber(searchstring):
#     digits = ''.join(x for x in r if x.isdigit())
#     if digits:
#         return int(s)
#     else:
#         return None

# def failedGoalHelper(reset_window, failed_activies):
#     output_string = "Failed to accomplish these goals in "+reset_window+": "+failed_goals[0]
#     for i in range(len(failed_goals)):
#         if not i == len(failed_goals)-1:
#             output_string+= ", "+failed_goals[i]
#         else:
#             output_string+= ", and "+failed_goals

        
