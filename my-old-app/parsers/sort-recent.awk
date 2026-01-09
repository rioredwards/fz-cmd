# Sort commands by recent usage
# Input: formatted_display\toriginal_command\toriginal_description\toriginal_tags\toriginal_examples
# Output: priority\tformatted_display\toriginal_command\toriginal_description\toriginal_tags\toriginal_examples
BEGIN {
    # Read recent order into an array with line numbers as priority
    priority = 1
    while ((getline cmd < recent_file) > 0) {
        recent_priority[cmd] = priority++
    }
    close(recent_file)
    max_priority = priority
}
{
    cmd = $2  # Original command is in field 2
    # Assign priority: lower number = higher priority (appears first)
    if (cmd in recent_priority) {
        prio = recent_priority[cmd]
    } else {
        prio = max_priority + NR  # Unused commands get high priority numbers
    }
    print prio "\t" $0
}

