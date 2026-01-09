head

Output the first part of files.
See also: `tail`.
More information: <https://keith.github.io/xcode-man-pages/head.1.html>.

- Output the first 10 lines of a file:
    head path/to/file

- Output the first 5 lines of multiple files:
    head [-5|--lines 5] path/to/file1 path/to/file2 ...

- Output the first `n` lines of a file:
    head [-n|--lines] n path/to/file

- Output the first `n` bytes of a file:
    head [-c|--bytes] n path/to/file


content:
lpstat

Display status information about the current classes, jobs, and printers.
More information: <https://keith.github.io/xcode-man-pages/lpstat.1.html>.

- Show a long listing of printers, classes, and jobs:
    lpstat -l

- Force encryption when connecting to the CUPS server:
    lpstat -E

- Show the ranking of print jobs:
    lpstat -R

- Show whether or not the CUPS server is running:
    lpstat -r

- Show all status information:
    lpstat -t


content:
reboot

Reboot the system.
More information: <https://keith.github.io/xcode-man-pages/reboot.8.html>.

- Reboot immediately:
    sudo reboot

- Reboot immediately without gracefully shutting down:
    sudo reboot -q


content:
terminal-notifier

Send macOS User Notifications.
More information: <https://github.com/julienXX/terminal-notifier>.

- Send a notification (only the message is required):
    terminal-notifier -group tldr-info -title TLDR -message 'TLDR rocks'

- Display piped data with a sound:
    echo 'Piped Message Data!' | terminal-notifier -sound default

- Open a URL when the notification is clicked:
    terminal-notifier -message 'Check your Apple stock!' -open 'http://finance.yahoo.com/q?s=AAPL'

- Open an app when the notification is clicked:
    terminal-notifier -message 'Imported 42 contacts.' -activate com.apple.AddressBook


content:
system_profiler

Report system hardware and software configuration.
More information: <https://keith.github.io/xcode-man-pages/system_profiler.8.html>.

- Display a report with specific details level (mini [no personal information], basic, or full):
    system_profiler -detailLevel level

- Display a full system profiler report which can be opened by `System Profiler.app`:
    system_profiler -xml > MyReport.spx

- Display a hardware overview (Model, CPU, Memory, Serial, etc) and software data (System, Kernel, Name, Uptime, etc):
    system_profiler SPHardwareDataType SPSoftwareDataType

- Print the system serial number:
    system_profiler SPHardwareDataType|grep "Serial Number (system)" | awk '{ print $4 }'


content:
bless

Set volume boot capability and startup disk options.
More information: <https://keith.github.io/xcode-man-pages/bless.8.html>.

- Bless a volume with only Mac OS X or Darwin, and create the BootX and `boot.efi` files as needed:
    bless --folder /Volumes/Mac OS X/System/Library/CoreServices --bootinfo --bootefi

- Set a volume containing either Mac OS 9 and Mac OS X to be the active volume:
    bless --mount /Volumes/Mac OS --setBoot

- Set the system to NetBoot and broadcast for an available server:
    bless --netboot --server bsdp://255.255.255.255

- Gather information about the currently selected volume (as determined by the firmware), suitable for piping to a program capable of parsing Property Lists:
    bless --info --plist


content:
gtrue

This command is an alias of GNU `true`.

- View documentation for the original command:
    tldr true


content:
mac-cleanup

A modern macOS cleanup tool to remove caches and junk.
More information: <https://github.com/mac-cleanup/mac-cleanup-py>.

- Start the cleanup process:
    mac-cleanup

- Open the module configuration screen:
    mac-cleanup [-c|--configure]

- Perform a dry-run, showing what will be removed without actually deleting it:
    mac-cleanup [-n|--dry-run]

- Specify the directory with custom cleanup modules:
    mac-cleanup [-p|--custom-path] path/to/directory

- Automatically acknowledge all warnings and continue with force:
    mac-cleanup [-f|--force]


content:
lsappinfo

Control and query CoreApplicationServices about the app state on the system.
More information: <https://keith.github.io/xcode-man-pages/lsappinfo.8.html>.

- List all running applications with their details:
    lsappinfo list

- Show the front application:
    lsappinfo front

- Show the information for a specific application:
    lsappinfo info com.apple.calculator


content:
pmset

Configure macOS power management settings, as one might do in System Preferences > Energy Saver.
Commands that modify settings must begin with `sudo`.
More information: <https://keith.github.io/xcode-man-pages/pmset.1.html>.

- Display the current power management settings:
    pmset -g

- Display the current power source and battery levels:
    pmset -g batt

- Put display to sleep immediately:
    pmset displaysleepnow

- Set display to never sleep when on charger power:
    sudo pmset -c displaysleep 0

- Set display to sleep after 15 minutes when on battery power:
    sudo pmset -b displaysleep 15

- Schedule computer to automatically wake up every weekday at 9 AM:
    sudo pmset repeat wake MTWRF 09:00:00

- Restore to system defaults:
    sudo pmset -a displaysleep 10 disksleep 10 sleep 30 womp 1
