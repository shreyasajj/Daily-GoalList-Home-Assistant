todolist_entity_id = data.get("entity_id")
reset_window = data.get("reset_window", "weekly")

if todolist_entity_id is not None:
    # Get all todolist items
    service_data = {"entity_id": todolist_entity_id}
    all_goals = hass.services.call("todo", "get_items", service_data, blocking=True, return_response=True)
    logger.warning(all_goals)

    # Loop through all items
    # for goal in all_goals[""]:
    #     # Check for items not completed by due date
    #     if 