#!/bin/sh
# Custom tool for managing your various development environments and tasks.

mytool() {
  # Check if configuration is loaded
  if true; then
    local MYTOOL_DESTINATION_PATH="/home/user/projects/${MYTOOL_PROJECT}"
    
    # Command: navigate to project directory
    if [ $# -eq 1 ] && [ "$1" = "cd" ]; then
      cd "/home/john/yahboom_dashboard"/ || return
    
    # Command: connect to remote machine
    elif [ $# -eq 1 ] && [ "$1" = "activate" ]; then
      echo "Activating venv at : /home/john/root/yahboomcar_ws/src/yahboom_dashboard/streamlit-venv/"
      source /home/john/yahboom_dashboard/streamlit-venv/bin/activate
    
    # Command: run a Jupyter server
    # elif [ $# -eq 1 ] && [ "$1" = "jupyter" ]; then
    #   mytool cd
    #   echo "Starting a Jupyter server..."
    #   jupyter-notebook --no-browser
    
    # # Command: remove project directory from remote server
    # elif [ $# -eq 1 ] && [ "$1" = "remove" ]; then
    #   echo "Removing project directory from remote server..."
    #   ssh user@"$MYTOOL_IP" "cd /home/user/projects/ && rm -rf ${MYTOOL_PROJECT}"
    
    # # Command: setup project directory on remote server
    # elif [ $# -eq 1 ] && [ "$1" = "setup" ]; then
    #   echo "Setting up project directory on remote server..."
    #   ssh user@"$MYTOOL_IP" mkdir -p "$MYTOOL_DESTINATION_PATH"
    #   mytool sync all
    
    # # Command: sync files to remote server
    # elif [ $# -eq 2 ] && [ "$1" = "sync" ]; then
    #   local valid_command=false
    #   if [ "$2" = "src" ] || [ "$2" = "all" ]; then
    #     echo "Syncing local source code to remote server..."
    #     rsync -azP --delete "$MYTOOL_ABSOLUTE_PATH"/src user@"$MYTOOL_IP":"$MYTOOL_DESTINATION_PATH"
    #     valid_command=true
    #   fi
    #   if [ "$valid_command" = false ]; then
    #     echo "'${2}' is not a recognized sync command. Use 'src' or 'all'."
    #   fi
    
    # # Command: run a Python script
    # elif [ $# -eq 2 ] && [ "$1" = "run" ]; then
    #   echo "Running Python script $2..."
    #   python3 "$2"
    
    # # Command: backup project
    # elif [ $# -eq 1 ] && [ "$1" = "backup" ]; then
    #   cd "$MYTOOL_ABSOLUTE_PATH"
    #   now="$(date)"
    #   if [ ! -d "backup" ]; then
    #     echo "Backup folder not found, creating one now..."
    #     mkdir ./backup
    #   fi
    #   numfiles=(./backup/*)
    #   numfiles=${#numfiles[@]}
    #   mkdir ./backup/version_"$numfiles"
    #   echo "Backup number: $numfiles"
    #   echo "Backup created at: $MYTOOL_ABSOLUTE_PATH/backup/version_$numfiles"
    #   scp -rp user@"$MYTOOL_IP":/home/user/projects "$MYTOOL_ABSOLUTE_PATH/backup/version_$numfiles"
    
    # # Display help
    # elif [ $# -eq 1 ] && [ "$1" = "help" ]; then
    #   echo "Welcome to my custom tool. Here are the available commands:"
    #   echo "  mytool cd: Navigate to the project directory."
    #   echo "  mytool connect: SSH into the remote machine."
    #   echo "  mytool jupyter: Start Jupyter Notebook server."
    #   echo "  mytool remove: Remove project directory from the remote machine."
    #   echo "  mytool setup: Set up the project directory on the remote machine."
    #   echo "  mytool sync <src|all>: Sync local files with the remote server."
    #   echo "  mytool run <script.py>: Run the specified Python script."
    #   echo "  mytool backup: Create a backup of the project on the local machine."
    #   echo "  mytool help: Show this help message."
    else
      echo "Invalid command. Type 'mytool help' for a list of available commands."
    fi
  fi
}

# Uncomment t
