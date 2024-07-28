todolist_entity_id = data.get("entity_id")
current_time = datetime.datetime.now()
reset_window_input = data.get("reset_window", "weekly")



def getNumber(searchstring):
    digit = None
    for s in searchstring:
        if s.isdigit():
            if digit is None:
                digit = s
            else:
                digit += s
        elif s == "-":
            digit = "-"
        else:
            if digit:
                break
    if digit == "-" or not digit:
        return None
    return int(digit)

def failedGoalHelper(reset_window, failed_goals):
    output_string = f"Failed to accomplish these goals in %d days: %s" % (reset_window, failed_goals[0])
    for i in range(1, len(failed_goals)):
        if not i == len(failed_goals)-1:
            output_string+= ", "+failed_goals[i]
        else:
            output_string+= ", and "+failed_goals[i]
    return output_string

if reset_window_input == "daily":
    reset_window = 1
    remaining_days = 1

elif reset_window_input == "weekly":
    #reset on 
    reset_window = 7
    remaining_days = reset_window - current_time.weekday()
else:
    logger.warning("\"reset_window\" need to be \"daily\" or \"weekly\"")
    exit(1)


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
        due_date_type = 0
        goal_due = None
        if "due" in goal and goal["status"] == "needs_action":
            # two different ways to define datetime
            try:
                goal_due = datetime.datetime.strptime(goal["due"], "%Y-%m-%dT%H:%M:%S%z")
                due_date_type = 1
            except ValueError:
                goal_due = datetime.datetime.strptime(goal["due"], "%Y-%m-%d")
                due_date_type = 2
            if current_time > goal_due:
                penalize = True

        initial_description = goal["description"].split("\n")
        error_budget_left = None
        total_error_budget = None
        final_description = []
        # Create a new goal template if it only contains a number and description
        if initial_description[0].isdigit():
            error_budget_left = int(initial_description[0])
            total_error_budget = error_budget_left
            initial_description.pop(0)
            final_description = initial_description
            logger.info(f"Found a number for %s in the description setting the error budget and total error budget" % (goal["summary"]))
        else:
            #else find "Error Budget Left" and "Total Error Budget" and get the raw description out
            for line in initial_description:
                if "Error Budget Left" in line:
                    error_budget_left = getNumber(line)
                elif "Total Error Budget" in line:
                    total_error_budget = getNumber(line)
                elif "Remaining Days" in line:
                    continue
                else:
                    final_description.append(line)
        # if error_budget_left or total_error_budget is missing skip
        if error_budget_left is None or total_error_budget is None:
            logger.info(f"No \"Error Budget Left\" or \"Total Error Budget\" found in description for %s, skipping" % (goal["summary"]))
            continue

        # deduct penalities
        if penalize:
            error_budget_left -= 1
            logger.info(f"%s was passed the due date...Subtracting from error budget. Error budget is now %d" % (goal["summary"], error_budget_left))
            if error_budget_left == 0:
                failed_goals = True
                failed_goals_val.append(goal["summary"])
                logger.info(f"Error budget for %s is 0, adding it to the failed_goals" % (goal["summary"]))
        
        # reset error budget
        if remaining_days == reset_window:
            error_budget_left = total_error_budget
            logger.info(f"%s: Setting error budget to total_error_budget as reset window was hit" % (goal["summary"]))
        
        # changing description 
        final_description.append(f"Error Budget Left: %d\nTotal Error Budget: %d\nRemaining Days: %d\n" % (error_budget_left, total_error_budget, remaining_days))
        description = '\n'.join([x for x in final_description if x])

        #creating due_date based on current version of date
        final_datetime = None
        if not goal_due is None and goal_due.date() == current_time.date():
            final_datetime = goal_due  + datetime.timedelta(day=1)
        elif not goal_due is None:
            final_datetime = datetime.datetime(current_time.year, current_time.month, current_time.day, goal_due.hour, goal_due.minute, goal_due.second)
        
        logger.info(final_datetime.strftime(final_datetime.strftime("%Y-%m-%d")))
        #setting the new due date based on previous type
        if due_date_type == 0:
            service_data = {"entity_id": todolist_entity_id, "status":"needs_action", "item": goal["summary"], "description": description}
        elif due_date_type == 1:
            service_data = {"entity_id": todolist_entity_id, "status":"needs_action", "due_datetime": final_datetime.strftime("%Y-%m-%dT%H:%M:%S%z"),"item": goal["summary"], "description": description}
        elif due_date_type == 2:
            service_data = {"entity_id": todolist_entity_id, "status":"needs_action", "due_date": final_datetime.strftime("%Y-%m-%d"), "item": goal["summary"], "description": description}
        hass.services.call("todo", "update_item", service_data, False)
    
    #output staus of goal
    if failed_goals:
        output["failed_goals_val"] = failedGoalHelper(reset_window, failed_goals_val)
    output["failed_goals"] = failed_goals

        




        
