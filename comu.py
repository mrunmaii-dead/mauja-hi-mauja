from flask import Flask, jsonify,request
import subprocess
import os
import uuid 
import platform
import socket
import requests
from flask_cors import CORS
import time
from datetime import datetime
app = Flask(__name__)
CORS(app)

# Path to VBScript for vulnerability scan
 # Directory for storing logs
ADMIN_SERVER_URL = 'http://192.168.4.198:5000/upload-log'  # Admin server IP and endpoint to send logs

program_files_dir = "C:\\Program Files"
VBSCRIPT_PATH = os.path.join(program_files_dir, "DLP", "VulAssess.vbs")
LOG_DIRECTORY = os.path.join(program_files_dir, "DLP", "VA logs")
SCREENSHOT_BLOCK_EXE = os.path.join(program_files_dir, "DLP", "Start_SS_Monitoring.exe")
SCREENSHOT_UNBLOCK_EXE = os.path.join(program_files_dir, "DLP", "Stop_SS_Monitoring.exe")

USB_LOG_FILE_PATH = os.path.join(program_files_dir, "DLP", "usb_log.txt")
KEYWORDS_FILE_PATH = os.path.join(program_files_dir, "DLP", "keywords.txt")
SCREENSHOT_LOG_FILE_PATH = os.path.join(program_files_dir, "DLP", "screenshot_log.txt")
KEYWORD_MONITORING_EXE = os.path.join(program_files_dir, "DLP", "test13.exe")
usb_blocking_status = False
keyword_monitoring_status = False
screenshot_status = False
last_va_scan_time = None 
executable_status = False
def log_usb_action(action):
    with open(USB_LOG_FILE_PATH, "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"{timestamp} - {action}\n")


# Load keywords from the file
def load_keywords():
    if os.path.exists(KEYWORDS_FILE_PATH):
        with open(KEYWORDS_FILE_PATH, "r") as f:
            keywords = [line.strip() for line in f if line.strip()]
        return keywords
    return []

# Save keywords to the file
def save_keywords(keywords):
    with open(KEYWORDS_FILE_PATH, "w") as f:
        for keyword in keywords:
            f.write(keyword + "\n")


def run_executable(path):
    subprocess.Popen([path])

def log_screenshot_action(action):
    with open(SCREENSHOT_LOG_FILE_PATH, "a") as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"{timestamp} - {action}\n")

@app.route('/get-screenshot-log', methods=['GET'])
def get_screenshot_log():
    if os.path.exists(SCREENSHOT_LOG_FILE_PATH):
        try:
            with open(SCREENSHOT_LOG_FILE_PATH, 'r') as file:
                content = file.read()
            return jsonify({"content": content}), 200
        except Exception as e:
            return jsonify({"error": f"Error reading file: {str(e)}"}), 500
    else:
        return jsonify({"error": "Screenshot log file not found"}), 404

        
@app.route('/toggle-screenshot-block', methods=['POST'])
def toggle_screenshot_block():
    global screenshot_status
    data = request.get_json()
    toggle_state = data.get('toggleState', False)

    try:
        if toggle_state:
            run_executable(SCREENSHOT_BLOCK_EXE)
            print("enabled")
            log_screenshot_action("Screenshot blocking enabled")
            message = "Screenshot blocking enabled."
            screenshot_status= True
        else:
            run_executable(SCREENSHOT_UNBLOCK_EXE)
            print("disabled")
            log_screenshot_action("Screenshot blocking disabled")
            message = "Screenshot blocking disabled."
            screenshot_status= False

        
        return jsonify({"message": message}), 200
    except Exception as e:
        return jsonify({"message": "Error toggling screenshot blocking", "error": str(e)}), 500

@app.route('/')
def index():
    return "Flask server is running."
# Get all keywords
@app.route('/get-keyword-content', methods=['GET'])
def get_keyword_logs():
    print("got it")
    if os.path.exists(KEYWORDS_FILE_PATH):
        try:
            with open(KEYWORDS_FILE_PATH, 'r') as file:
                content = file.read()
            return jsonify({"content": content}), 200
        except Exception as e:
            return jsonify({"error": f"Error reading file: {str(e)}"}), 500
    else:
        return jsonify({"error": "Keywords file not found"}), 404


@app.route('/keywords', methods=['GET'])
def get_keywords():
    keywords = load_keywords()
    return jsonify({"keywords": keywords}), 200

# Add a new keyword
@app.route('/keywords', methods=['POST'])
def add_keyword():
    new_keyword = request.json.get('keyword', '').strip()
    if new_keyword:
        keywords = load_keywords()
        if new_keyword not in keywords:
            keywords.append(new_keyword)
            save_keywords(keywords)
            return jsonify({"message": "Keyword added successfully", "keywords": keywords}), 200
        return jsonify({"message": "Keyword already exists"}), 400
    return jsonify({"message": "Invalid keyword"}), 400

# Delete a specific keyword
@app.route('/keywords/<string:keyword>', methods=['DELETE'])
def delete_keyword(keyword):
    keywords = load_keywords()
    if keyword in keywords:
        keywords.remove(keyword)
        save_keywords(keywords)
        return jsonify({"message": "Keyword deleted successfully", "keywords": keywords}), 200
    return jsonify({"message": "Keyword not found"}), 404



def get_windows_version():
    return platform.platform()

def get_device_id():
    return str(uuid.uuid1())

@app.route('/user-info', methods=['GET'])
def user_info():
    user_name = os.getlogin()
    device_id = get_device_id()
    windows_version = get_windows_version()
    
    return jsonify({
        "user_name": user_name,
        "device_id": device_id,
        "windows_version": windows_version
    })
    
@app.route('/ping',methods=['GET'])
def ping():
    user_name = os.getlogin()  # Get the logged-in user's name
    serial_number = platform.node()  # Use the machine's hostname or another unique identifier
    device_id=get_device_id()
    windows_version = get_windows_version()
    
    return jsonify({
        "message": "Client is connected",
        "user_name": user_name,
        "device_id": device_id,
        "windows_version": windows_version
        }), 200

@app.route('/give-logs', methods=['POST'])
def give_logs():
    print("executing give logs")
    try:
        # List all log files in the directory
        log_files = [f for f in os.listdir(LOG_DIRECTORY) if f.endswith('.txt')]
        if not log_files:
            return jsonify({"message": "No log files available"}), 404

        # Send each log file to the admin server
        for log_file in log_files:
            log_path = os.path.join(LOG_DIRECTORY, log_file)
            with open(log_path, 'rb') as file:
                files = {'file': file}
                response = requests.post(ADMIN_SERVER_URL, files=files)

                if response.status_code == 200:
                    print(f"Log {log_file} sent successfully to the admin server.")
                else:
                    print(f"Failed to send log {log_file} to the admin server, status code: {response.status_code}")

        return jsonify({"message": "All log files sent successfully to the admin."}), 200
    
    except Exception as e:
        return jsonify({"message": "Error sending log files", "error": str(e)}), 500

@app.route('/run-vulnerability-scan', methods=['POST'])
def run_vulnerability_scan():
    global last_va_scan_time
    try:
        # Run the VBScript
        result = subprocess.run(
            ['cscript.exe', '//B', VBSCRIPT_PATH],
            capture_output=True, text=True, check=True
        )
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        last_va_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(5)
        # Log output to a file
        log_files = [f for f in os.listdir(LOG_DIRECTORY) if f.endswith('.txt')]
        print(log_files)

        # Send the log file to the admin server
        for log_file in log_files:
            print("in for loop")
            log_path = os.path.join(LOG_DIRECTORY, log_file)
            print(log_path)
            with open(log_path, 'rb') as file:
                files = {'file': file}
                response = requests.post(ADMIN_SERVER_URL, files=files)
                
                if response.status_code == 200:
                    print(f"Log {log_file} sent successfully to the admin server .")
                else:
                    print(f"Failed to send log {log_file} to the admin server {response.status_code}.")
        
        return jsonify({"message": "Vulnerability scan completed and logs sent to admin.", "output": result.stdout})
    
    except subprocess.CalledProcessError as e:
        return jsonify({"message": "Error running VBScript", "error": e.stderr}), 500
    except Exception as e:
        return jsonify({"message": "Unexpected error occurred", "error": str(e)}), 500



@app.route('/run-keyword-monitoring', methods=['POST'])
def run_keyword_monitoring():
    global keyword_monitoring_status
    try:
        print("rcd cmd")
        # Run the keyword monitoring executable on the client machine
        subprocess.Popen([KEYWORD_MONITORING_EXE]) 
        keyword_monitoring_status = True
         # Run in the background

        return jsonify({"message": "Keyword monitoring started successfully."})
    except Exception as e:
        return jsonify({"message": "Error running executable", "error": str(e)}), 500



@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "usbPortBlocking": usb_blocking_status,
        "keywordMonitoring": keyword_monitoring_status,
        "screenshotBlocking": screenshot_status,
        "lastVAScanTime": last_va_scan_time,
        "executableBlocking": executable_status,
    })



@app.route('/get-usb-log', methods=['GET'])
def get_usb_log():
    if os.path.exists(USB_LOG_FILE_PATH):
        try:
            with open(USB_LOG_FILE_PATH, 'r') as file:
                content = file.read()
            return jsonify({"content": content}), 200
        except Exception as e:
            return jsonify({"error": f"Error reading file: {str(e)}"}), 500
    else:
        return jsonify({"error": "USB log file not found"}), 404



@app.route('/toggle-usb-port-blocking', methods=['POST'])
def toggle_usb_port_blocking_client():
    
    data = request.get_json()
    toggle_state = data.get('toggleState', False)

    try:
        if toggle_state:
            
            
            # Run the VBScript for enabling USB/Port Blocking in a new console window
            process = subprocess.Popen(
                 ['cscript.exe', '//B', os.path.join(home_dir, "Desktop", "DLP", "Admin usb block.vbs")],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            log_usb_action("USB port blcoking enabled")
        else:
            
            # Run the VBScript for disabling USB/Port Blocking in a new console window
            process = subprocess.Popen(
                 ['cscript.exe', '//B', os.path.join(home_dir, "Desktop", "DLP", "Admin usb not block.vbs")],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            log_usb_action("USB port blcoking disabled")
        usb_blocking_state = toggle_state
        return jsonify({"message": f"USB/Port Blocking {'enabled' if toggle_state else 'disabled'}"}), 200
    except Exception as e:
        print(f"Error running the VBScript: {str(e)}")
        return jsonify({"message": "Error running the VBScript", "error": str(e)}), 500
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)