# Generate preview text for fzf with color coding
# Input: formatted_display\toriginal_command\toriginal_description\toriginal_tags\toriginal_examples
# Output: Formatted preview with command, description, and examples
# Examples format: "desc1: cmd1; desc2: cmd2" or "cmd1; cmd2"
#
# ANSI color codes:
#   \033[1;36m = Bold Cyan (labels)
#   \033[0m = Reset
#   \033[33m = Yellow (example descriptions)
#   \033[32m = Green (example commands)
#   \033[0;37m = White (values)

BEGIN {
    # Color codes
    label_color = "\033[1;36m"      # Bold cyan for labels
    reset = "\033[0m"               # Reset
    desc_color = "\033[33m"         # Yellow for example descriptions
    cmd_color = "\033[32m"          # Green for example commands
    value_color = "\033[0;37m"      # White for values
}

{
    printf "%sCommand:%s\n%s%s%s\n\n", label_color, reset, value_color, $2, reset
    printf "%sDescription:%s\n%s%s%s\n", label_color, reset, value_color, $3, reset
    if ($5 != "") {
        printf "\n%sExamples:%s\n", label_color, reset
        # Split examples by "; " and format each
        n = split($5, examples, "; ")
        for (i = 1; i <= n; i++) {
            example = examples[i]
            # Check if example has description (contains ": ")
            if (match(example, /: /)) {
                desc = substr(example, 1, RSTART - 1)
                cmd = substr(example, RSTART + 2)
                printf "  %s%s%s\n    %s%s%s\n", desc_color, desc, reset, cmd_color, cmd, reset
            } else {
                printf "  %s%s%s\n", cmd_color, example, reset
            }
        }
    }
}

