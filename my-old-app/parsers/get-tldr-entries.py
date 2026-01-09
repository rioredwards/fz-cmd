#!/usr/bin/env python3
"""
Extract and format tldr entries for fz-cmd.
Outputs tab-separated: command\tdescription\ttags\texamples
"""

import sys
import subprocess
import re
import json
from datetime import datetime

LOG_PATH = '/Users/rioredwards/.dotfiles/.cursor/debug.log'

def debug_log(session_id, run_id, hypothesis_id, location, message, data):
    """Write debug log entry."""
    try:
        with open(LOG_PATH, 'a') as f:
            log_entry = {
                'sessionId': session_id,
                'runId': run_id,
                'hypothesisId': hypothesis_id,
                'location': location,
                'message': message,
                'data': data,
                'timestamp': int(datetime.now().timestamp() * 1000)
            }
            f.write(json.dumps(log_entry) + '\n')
    except Exception:
        pass

def get_tldr_entries(max_entries=500):
    """Get all tldr entries and format them."""
    session_id = 'debug-session'
    run_id = 'run1'
    
    # #region agent log
    debug_log(session_id, run_id, 'A', 'get-tldr-entries.py:12', 'Function entry', {'max_entries': max_entries})
    # #endregion
    
    # Check if tldr is available
    try:
        subprocess.run(['tldr', '--version'], 
                      capture_output=True, 
                      check=True, 
                      timeout=1)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
        # #region agent log
        debug_log(session_id, run_id, 'A', 'get-tldr-entries.py:20', 'tldr not available', {'error': str(e)})
        # #endregion
        return
    
    # Get list of tldr pages
    try:
        result = subprocess.run(['tldr', '--list'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode != 0:
            return
        
        pages = result.stdout.strip().split('\n')[:max_entries]
    except subprocess.TimeoutExpired:
        return
    
    # Process each page
    for page in pages:
        if not page.strip():
            continue
        
        page = page.strip()
        
        # #region agent log
        debug_log(session_id, run_id, 'B', 'get-tldr-entries.py:40', 'Processing page', {'page': page})
        # #endregion
        
        # Get tldr content for this page
        try:
            result = subprocess.run(['tldr', page], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=2)
            if result.returncode != 0:
                # #region agent log
                debug_log(session_id, run_id, 'C', 'get-tldr-entries.py:49', 'tldr command failed', {'page': page, 'returncode': result.returncode})
                # #endregion
                continue
            
            content = result.stdout
        except subprocess.TimeoutExpired:
            # #region agent log
            debug_log(session_id, run_id, 'C', 'get-tldr-entries.py:53', 'tldr timeout', {'page': page})
            # #endregion
            continue
        
        if not content:
            # #region agent log
            debug_log(session_id, run_id, 'C', 'get-tldr-entries.py:56', 'Empty content', {'page': page})
            # #endregion
            continue
        
        # #region agent log
        debug_log(session_id, run_id, 'D', 'get-tldr-entries.py:60', 'Raw tldr content (first 500 chars)', {'page': page, 'content_preview': content[:500]})
        # #endregion
        
        # Extract command (first example)
        # tldr format: "- Description:" followed by indented "    command args"
        first_cmd = None
        matched_lines = []
        lines_list = content.split('\n')
        for i, line in enumerate(lines_list):
            # Look for example lines starting with "- " or "* " (description)
            if re.match(r'^\s*[-*]\s+', line):
                matched_lines.append(line)
                # The actual command is on the next line, indented
                if i + 1 < len(lines_list):
                    next_line = lines_list[i + 1]
                    # Extract command from indented line (starts with spaces, then command)
                    # Match: "    command args" -> extract "command"
                    cmd_match = re.match(r'^\s+(\S+)', next_line)
                    if cmd_match:
                        extracted_cmd = cmd_match.group(1)
                        # If command is "sudo" or other wrapper, use the page name instead
                        if extracted_cmd in ['sudo', 'doas', 'run0']:
                            first_cmd = page
                        else:
                            first_cmd = extracted_cmd
                        # #region agent log
                        debug_log(session_id, run_id, 'A', 'get-tldr-entries.py:66', 'Command extracted from indented line', {'page': page, 'description_line': line, 'command_line': next_line, 'extracted_cmd': extracted_cmd, 'final_cmd': first_cmd})
                        # #endregion
                        break
        
        # #region agent log
        debug_log(session_id, run_id, 'A', 'get-tldr-entries.py:70', 'All matched example lines', {'page': page, 'matched_lines': matched_lines[:5]})
        # #endregion
        
        # If no command found, use page name
        if not first_cmd:
            first_cmd = page
            # #region agent log
            debug_log(session_id, run_id, 'B', 'get-tldr-entries.py:75', 'No command found, using page name', {'page': page, 'fallback_cmd': first_cmd})
            # #endregion
        
        # Extract description (first non-empty line after page name and blank line)
        # tldr format: "page_name\n\nDescription text..."
        desc = None
        lines = content.split('\n')
        # Skip first line (page name) and next empty line, find first non-empty line
        # Structure: line[0] = empty, line[1] = page name, line[2] = empty, line[3] = description
        for i, line in enumerate(lines[2:], start=2):
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith('More information:') and not line_stripped.startswith('See also:'):
                desc = line_stripped[:100]  # Limit to 100 chars
                # #region agent log
                debug_log(session_id, run_id, 'D', 'get-tldr-entries.py:90', 'Description extracted', {'page': page, 'line_idx': i, 'line': line_stripped, 'desc': desc})
                # #endregion
                break
        
        # Default description if not found
        if not desc:
            desc = f"Command from tldr: {page}"
            # #region agent log
            debug_log(session_id, run_id, 'E', 'get-tldr-entries.py:96', 'Using default description', {'page': page, 'default_desc': desc})
            # #endregion
        
        # Format output: command\tdescription\ttags\texamples
        tags = f"tldr {page}"
        examples = first_cmd
        
        # #region agent log
        debug_log(session_id, run_id, 'ALL', 'get-tldr-entries.py:102', 'Final output values', {'page': page, 'first_cmd': first_cmd, 'desc': desc, 'tags': tags, 'examples': examples})
        # #endregion
        
        print(f"{first_cmd}\t📖 {desc}\t{tags}\t{examples}")


if __name__ == '__main__':
    max_entries = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    get_tldr_entries(max_entries)

