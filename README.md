# GoalList_Home_Assistant
This is a python script for home assistant for creating recurring daily goals in the todo list

# Prerequisite
* Have Home Assistant
* Create a todo list that has all your Daily Goals Setup
* In each of your goals set a due date and add to the description a number representing your error budget (This is how many days you can skip in a week)
# Install
1. Follow this guide to install Python Script: https://www.home-assistant.io/integrations/python_script/
   Summary:
   1. Add to `configuration.yaml`: `python_script:` Like this
     ```yaml
     ...
     python_script:
     ...
     ```
    2. Next create a folder `python_scripts` inside Home Assistant `data` folder
2. Inside the `python_scripts` folder run `wget https://raw.githubusercontent.com/shreyasajj/GoalList_Home_Assistant/main/goallist.py -O goallist.py`
3. Run Service `Python script: Reload`
4. You should now see a service called `Python script: goallist`

# Input
* **entity_id**: Your todo list entity_id ie `entity_id: todo.goallist` - required
* **reset_window**: Either weekly or daily supported now ie `reset_window: weekly` - optional, default: "weekly" # Not working right now
```yaml
service: python_script.goallist
data:
  entity_id: todo.goallist
```
# Output
* **failed_goals**: Goals that were failed and passed the error budget. This will be a string that follows `Failed to accomplish these goals in 7 days: goal1, goal2, and goal3`
* **end_of_week_report**: Weekly status report, it will return on the end of the week and be a string that looks like 
```yaml
**This is the end of week report**
**Goal 1**
[7/29/2024] No work notes for today
**Goal 2**
[7/29/2024] Skipped
**Goal 3**
[7/29/2024] Worked on it today got so and so done
```

# Usage
* In order to use this, just update description with what you did that day and mark that todo list item completed

# Automation
Here a automation on how I am using it
```yaml
alias: Daily Goal List Automation
description: An Automation for accountablity, sending my friend a list a goals I failed to acchieve and send a weekly status report at the end
trigger:
  - platform: time
    at: "00:02:00"
condition: []
action:
  - service: python_script.goallist
    data:
      entity_id: todo.goallist
    response_variable: goal_list_response
  - if:
      - condition: template
        value_template: "{{ not goal_list_response['failed_goals']  == false}}"
    then:
      - service: notify.notify
        metadata: {}
        data:
          message: "{{ goal_list_response['failed_goals'] }}"
  - if:
      - condition: template
        value_template: "{{ not goal_list_response['end_of_week_report']  == false}}"
    then:
      - service: notify.notify
        metadata: {}
        data:
          message: "{{ goal_list_response['end_of_week_report'] }}"
          data:
            text_mode: styled

mode: single

```



