todolist_entity_id = data.get("entity_id")
current_time = datetime.datetime.now()
current_time = current_time.replace(tzinfo=None)
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
    if not failed_goals:
        return False
    output_string = f"Failed to accomplish these goals in %d days: %s" % (reset_window, failed_goals[0])
    for i in range(1, len(failed_goals)):
        if not i == len(failed_goals)-1:
            output_string+= ", "+failed_goals[i]
        else:
            output_string+= ", and "+failed_goals[i]
    return output_string

def endOfWeekReportHelper(end_of_week_report):
    if not end_of_week_report:
        return False
    output_string = "**This is the end of week report**"
    for name, report in end_of_week_report.items():
        output_string+= f"\n**%s**" % (name)
        if not report:
            output_string += "\nNo Report"
        else:
            output_string += f"\n%s" % (report)
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
    end_of_week_report = {}
    failed_goals = []
    # Loop through all items
    for goal in all_goals[todolist_entity_id]["items"]:
        logger.info("Processing "+ goal["summary"])
        # Skipping over values without description, summary, or status Not Supported
        if not "description" in goal or not "status" in goal or not "due" in globals or not len(goal["description"]) > 0:
            logger.info("Skipping "+ goal["summary"] + " has no \"description\"/\"status\"/\"due\"")
            continue
        # Penalize goals passed dues 
        penalize = False
        due_date_type = 0
        # two different ways to define datetime
        try:
            goal_due = datetime.datetime.strptime(goal["due"], "%Y-%m-%dT%H:%M:%S%z")
            logger.debug(f"Found the current date as datetime %s" %(goal_due))
            due_date_type = 1
        except ValueError:
            goal_due = datetime.datetime.strptime(goal["due"], "%Y-%m-%d")
            goal_due = goal_due.replace(hour=23, minute=59, second=59)
            logger.debug(f"Found the current date as date %s" %(goal_due))
            due_date_type = 2
        goal_due = goal_due.replace(tzinfo=None)
        if current_time > goal_due and goal["status"] == "needs_action":
            logger.debug(f"Time due is less than the current time %s %s" %(goal_due, current_time))
            penalize = True 
        else:
            logger.debug(f"Time due is greater than the current time %s %s, ignoring this time" %(goal_due, current_time))
            due_date_type = 0
            

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
            today_work_notes = []
            end_of_work_notes = False
            for line in initial_description:
                if "Error Budget Left" in line:
                    error_budget_left = getNumber(line)
                    logger.debug(f"Found the Error Budget Left = %s" %(error_budget_left))
                    end_of_work_notes = True
                elif "Total Error Budget" in line:
                    total_error_budget = getNumber(line)
                    logger.debug(f"Found the Total Error Budget = %s" %(total_error_budget))
                    end_of_work_notes = True
                elif "Remaining Days" in line:
                    logger.debug(f"Found the Remaining Days")
                    end_of_work_notes = True
                    continue
                elif line and not end_of_work_notes:
                    today_work_notes.append(line)
                else:
                    final_description.append(line)
        # if error_budget_left or total_error_budget is missing skip
        if error_budget_left is None or total_error_budget is None:
            logger.info(f"No \"Error Budget Left\" or \"Total Error Budget\" found in description for %s, skipping" % (goal["summary"]))
            continue

        # deduct penalities/set work notes descrition
        if penalize:
            error_budget_left -= 1
            final_description.append(f"[%d/%d/%d] Skipped" % (current_time.month, current_time.day, current_time.year))
            logger.info(f"%s was passed the due date...Subtracting from error budget. Error budget is now %d" % (goal["summary"], error_budget_left))
            if error_budget_left == 0:
                failed_goals.append(goal["summary"])
                logger.info(f"Error budget for %s is 0, adding it to the failed_goals" % (goal["summary"]))
        elif today_work_notes:
            final_description.append(f"[%d/%d/%d] %s" % (current_time.month, current_time.day, current_time.year, '\n'.join([x for x in today_work_notes if x])))
        else:
            final_description.append(f"[%d/%d/%d] No work notes for today" % (current_time.month, current_time.day, current_time.year))
        
        # reset error budget/outputing all work notes for end of the week report
        if remaining_days == reset_window:
            error_budget_left = total_error_budget
            logger.info(f"%s: Setting error budget to total_error_budget as reset window was hit" % (goal["summary"]))
            end_of_week_report[goal["summary"]] = '\n'.join([x for x in final_description if x])
            logger.debug(f"This is the end of the week report %s" % (end_of_week_report))
            final_description = []
        
        # changing description 
        final_description.insert(0,f"\nError Budget Left: %d\nTotal Error Budget: %d\nRemaining Days: %d\n" % (error_budget_left, total_error_budget, remaining_days))
        description = '\n'.join([x for x in final_description if x])
        logger.debug(f"The final description is %s" % (description))

        #creating due_date based on current version of date
        final_datetime = None
        if not due_date_type == 0 and goal_due.date() == current_time.date():
            final_datetime = goal_due  + datetime.timedelta(days=1)
            logger.debug(f"Added one day to the final time because the due date and the current are the same %s" % (final_datetime))
        elif not due_date_type == 0:
            final_datetime = datetime.datetime(current_time.year, current_time.month, current_time.day, goal_due.hour, goal_due.minute, goal_due.second)
            logger.debug(f"Set final datetime to %s" % (final_datetime))
            #it could be afternoon and the date is set for the morning instead
            if final_datetime < current_time:
                final_datetime = final_datetime + datetime.timedelta(days=1)
                logger.debug(f"Final datetime was not greater than the current time, rectifing  %s" % (final_datetime))
        
        #setting the new due date based on previous type
        if due_date_type == 0:
            service_data = {"entity_id": todolist_entity_id, "status":"needs_action", "item": goal["summary"], "description": description}
        elif due_date_type == 1:
            # has a bug and cant figure it out, dont use a due date that time specific
            service_data = {"entity_id": todolist_entity_id, "status":"needs_action", "due_datetime": f"%d-%d-%d %d:%d:%d" % (final_datetime.year, final_datetime.month, final_datetime.day, final_datetime.hour, final_datetime.minute, final_datetime.second),"item": goal["summary"], "description": description}
        elif due_date_type == 2:
            service_data = {"entity_id": todolist_entity_id, "status":"needs_action", "due_date": f"%d-%d-%d" % (final_datetime.year, final_datetime.month, final_datetime.day), "item": goal["summary"], "description": description}
        logger.debug(f"Service Call is %s" % (service_data))
        hass.services.call("todo", "update_item", service_data, False)
    
    #output staus of goal
    output["failed_goals"] = failedGoalHelper(reset_window, failed_goals)
    output["end_of_week_report"] = endOfWeekReportHelper(end_of_week_report)

else:
    logger.warning("Did not provide a entity_id")

        




        
