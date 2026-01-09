# Format output with fixed-width columns for better readability
# Input: command\tdescription\ttags\texamples
# Output: formatted_display\toriginal_command\toriginal_description\toriginal_tags\toriginal_examples
{
    cmd = $1
    desc = $2
    tags = $3
    examples = $4  # Examples stored but not displayed in main list
    
    # Truncate and pad command (35 chars)
    if (length(cmd) > 35) {
        cmd = substr(cmd, 1, 32) "..."
    } else {
        cmd = sprintf("%-35s", cmd)
    }
    
    # Truncate and pad description (50 chars)
    if (length(desc) > 50) {
        desc = substr(desc, 1, 47) "..."
    } else {
        desc = sprintf("%-50s", desc)
    }
    
    # Truncate and pad tags (80 chars). This keeps most tag keywords (like "info")
    # searchable in fzf without being cut off.
    if (length(tags) > 80) {
        tags = substr(tags, 1, 77) "..."
    } else {
        tags = sprintf("%-80s", tags)
    }
    
    # Print formatted line with original data for extraction
    # Format: "formatted_display\toriginal_command\toriginal_description\toriginal_tags\toriginal_examples"
    # Use tab as delimiter - very unlikely in commands, and formatted display is searchable
    # The formatted display contains command, description, and tags (no examples) for search
    print cmd "  " desc "  " tags "\t" $1 "\t" $2 "\t" $3 "\t" examples
}

