todolist_entity_id = data.get("entity_id")
current_time = datetime.datetime.now()
reset_window = 7

if todolist_entity_id is not None:
    # Get all todolist items
    service_data = {"entity_id": todolist_entity_id}
    all_goals = hass.services.call("todo", "get_items", service_data, blocking=True, return_response=True)
    logger.warning(all_goals)

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
                goal_due = datetime.datetime.strptime(goal["due"], "%Y-%m-%dT%H:%M%S%z")
            except ValueError:
                goal_due = atetime.datetime.strptime(goal["due"], "%Y-%m-%d")
            if current_time > goal_due:
                penalize = True
        
        # Create a new goal template if it only contains a number and description
        initial_description = goal["description"].split("\n")
        error_budget_left = None
        total_error_budget = None
        remaining_days = reset_window - current_time.weekday()
        if description[0].isdigit():
            error_budget_left = int(description[0])
            total_error_budget = error_budget_left
            description.pop(0)
        # if error_budget_left or total_error_budget is missing skip
        if not error_budget_left or not total_error_budget:
            logger.info(f"No \"Error Budget Left\" or \"Total Error Budget\" found in description for %s, skipping" % (goal["summary"]))
            continue
        # changing description 
        description = f"Error Budget Left: %d\nTotal Error Budget: %d\nRemaining Days: %d\n" % (error_budget_left, total_error_budget, remaining_days)
        description += '\n'.join(description)
        logger.warning(description)
        service_data = {"entity_id": todolist_entity_id, "status":"needs_action", "item": goal["summary"], "due_date": current_time.strftime("%Y-%m-%d"), description: description}
        hass.services.call("todo", "update_item", service_data, False)

        


        
