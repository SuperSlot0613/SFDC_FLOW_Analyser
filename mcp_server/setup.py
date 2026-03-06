#!/usr/bin/env python3
"""
Setup script for the Salesforce Flow Analyzer MCP Server
Helps configure Claude Desktop and install dependencies.
"""

import os
import sys
import json
import platform
import subprocess
from pathlib import Path

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")


def get_claude_config_path():
    """Get the Claude Desktop config path based on OS"""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif system == "Windows":
        return Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json"
    elif system == "Linux":
        return Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
    else:
        return None


def install_dependencies():
    """Install required Python packages"""
    print_header("Installing Dependencies")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    try:
        print_info("Installing MCP SDK and dependencies...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print_success("Dependencies installed successfully!")
        else:
            print_error(f"Failed to install dependencies: {result.stderr}")
            return False
            
    except Exception as e:
        print_error(f"Error installing dependencies: {e}")
        return False
    
    return True


def configure_claude_desktop():
    """Configure Claude Desktop to use this MCP server"""
    print_header("Configuring Claude Desktop")
    
    config_path = get_claude_config_path()
    
    if not config_path:
        print_error("Could not determine Claude Desktop config path for your OS")
        return False
    
    print_info(f"Claude Desktop config path: {config_path}")
    
    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing config or create new
    existing_config = {}
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                existing_config = json.load(f)
            print_info("Found existing Claude Desktop configuration")
        except json.JSONDecodeError:
            print_warning("Existing config is invalid, will create new one")
    
    # Prepare server config
    project_root = Path(__file__).parent.parent
    server_path = Path(__file__).parent / "server.py"
    
    server_config = {
        "command": sys.executable,  # Use the current Python interpreter
        "args": [str(server_path)],
        "env": {
            "PYTHONPATH": str(project_root)
        }
    }
    
    # Add to config
    if "mcpServers" not in existing_config:
        existing_config["mcpServers"] = {}
    
    existing_config["mcpServers"]["salesforce-flow-analyzer"] = server_config
    
    # Save config
    try:
        with open(config_path, 'w') as f:
            json.dump(existing_config, f, indent=2)
        print_success(f"Configuration saved to {config_path}")
    except Exception as e:
        print_error(f"Failed to save configuration: {e}")
        return False
    
    return True


def verify_setup():
    """Verify the setup is correct"""
    print_header("Verifying Setup")
    
    # Check MCP is installed
    try:
        import mcp
        print_success(f"MCP SDK is installed (version check passed)")
    except ImportError:
        print_error("MCP SDK is not installed. Run: pip install mcp")
        return False
    
    # Check server file exists
    server_path = Path(__file__).parent / "server.py"
    if server_path.exists():
        print_success(f"Server file exists: {server_path}")
    else:
        print_error(f"Server file not found: {server_path}")
        return False
    
    # Check flows directory
    flows_dir = Path(__file__).parent.parent / "org_flows"
    if flows_dir.exists():
        flow_count = len(list(flows_dir.glob("*.json"))) - 1  # -1 for _all_flows.json
        print_success(f"Flows directory exists with {flow_count} flows")
    else:
        print_warning("Flows directory not found. Run fetch_org_flows_cli.py to fetch flows.")
    
    # Check .env file
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        print_success("Environment file (.env) exists")
    else:
        print_warning("No .env file found. LLM features may not work.")
    
    return True


def print_next_steps():
    """Print next steps for the user"""
    print_header("Next Steps")
    
    print("""
1. 🔄 Restart Claude Desktop to load the MCP server

2. 🧪 Test the server by running:
   python mcp_server/test_server.py

3. 💬 In Claude Desktop, try these commands:
   - "List all Salesforce flows"
   - "Analyze the Create_property flow"
   - "Check best practices for offer_to_lead"

4. 📚 Read the documentation:
   - mcp_server/README.md
   - COMMANDS.md

5. 🔧 If you need to fetch flows from Salesforce:
   sf org login web
   python fetch_org_flows_cli.py
""")


def main():
    """Main setup function"""
    print_header("Salesforce Flow Analyzer MCP Server Setup")
    
    print("This script will:")
    print("  1. Install required Python packages")
    print("  2. Configure Claude Desktop")
    print("  3. Verify the setup\n")
    
    response = input("Continue? (y/n): ").strip().lower()
    if response != 'y':
        print("Setup cancelled.")
        return
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print_error("Setup failed at dependency installation")
        return
    
    # Step 2: Configure Claude Desktop
    if not configure_claude_desktop():
        print_warning("Claude Desktop configuration failed, but you can configure manually")
    
    # Step 3: Verify setup
    if not verify_setup():
        print_warning("Some verification checks failed")
    
    # Print next steps
    print_next_steps()
    
    print_success("Setup completed!")


if __name__ == "__main__":
    main()
