# Parse commands.yaml using awk
# Output format: command\tdescription\ttags\texamples
BEGIN { in_command = 0; in_description = 0; in_tags = 0; in_examples = 0 }
/^- command:/ { 
    if (cmd != "") print cmd "\t" desc "\t" tags "\t" examples
    cmd = ""; desc = ""; tags = ""; examples = ""
    in_command = 1
    sub(/^- command: /, "")
    cmd = $0
    next
}
/^    description:/ {
    in_description = 1
    sub(/^    description: /, "")
    desc = $0
    next
}
/^    tags:/ {
    in_tags = 1
    in_examples = 0
    tags = ""
    # Handle inline array format: tags: [tag1, tag2, tag3]
    if (match($0, /\[.*\]/)) {
        tags = substr($0, RSTART+1, RLENGTH-2)
        gsub(/,/, "", tags)
        gsub(/^ +| +$/, "", tags)
        gsub(/ +/, " ", tags)
        in_tags = 0
    }
    next
}
/^    examples:/ {
    in_examples = 1
    in_example_desc = 0
    in_example_cmd = 0
    in_tags = 0
    examples = ""
    example_desc = ""
    example_cmd = ""
    # Handle inline array format: examples: [ex1, ex2, ex3]
    if (match($0, /\[.*\]/)) {
        examples = substr($0, RSTART+1, RLENGTH-2)
        gsub(/^ +| +$/, "", examples)
        gsub(/ +/, " ", examples)
        in_examples = 0
    }
    next
}
in_tags && /^      - / {
    gsub(/^      - /, "", $0)
    gsub(/^ +| +$/, "", $0)
    if (tags != "") tags = tags " "
    tags = tags $0
    next
}
in_examples && /^      - description:/ {
    in_example_desc = 1
    in_example_cmd = 0
    sub(/^      - description: /, "")
    # Remove quotes if present
    gsub(/^['"]|['"]$/, "", $0)
    example_desc = $0
    next
}
in_examples && in_example_desc && /^        command:/ {
    in_example_cmd = 1
    sub(/^        command: /, "")
    # Remove quotes if present
    gsub(/^['"]|['"]$/, "", $0)
    example_cmd = $0
    # Format as "desc: cmd" and add to examples
    if (examples != "") examples = examples "; "
    if (example_desc != "" && example_cmd != "") {
        examples = examples example_desc ": " example_cmd
    } else if (example_cmd != "") {
        examples = examples example_cmd
    }
    example_desc = ""
    example_cmd = ""
    in_example_desc = 0
    in_example_cmd = 0
    next
}
in_examples && /^      - / {
    # Simple string format (not an object)
    gsub(/^      - /, "", $0)
    # Remove quotes if present
    gsub(/^['"]|['"]$/, "", $0)
    gsub(/^ +| +$/, "", $0)
    if (examples != "") examples = examples "; "
    examples = examples $0
    next
}
/^  - command:/ {
    in_command = 0; in_description = 0; in_tags = 0; in_examples = 0
}
END { if (cmd != "") print cmd "\t" desc "\t" tags "\t" examples }

