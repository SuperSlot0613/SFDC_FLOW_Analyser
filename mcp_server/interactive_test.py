#!/usr/bin/env python3
"""
Interactive test for the Salesforce Flow Analyzer MCP Server
Run individual tools to test functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.server import FlowAnalyzerMCPServer


async def main():
    print("🚀 Salesforce Flow Analyzer MCP Server - Interactive Test\n")
    
    server = FlowAnalyzerMCPServer()
    
    # Initialize components
    server._initialize_components()
    
    while True:
        print("\n" + "="*50)
        print("Available commands:")
        print("  1. list_flows        - List all flows")
        print("  2. analyze           - Analyze a flow")
        print("  3. query             - Query flow with AI")
        print("  4. best_practices    - Check best practices")
        print("  5. dependencies      - Get flow dependencies")
        print("  6. config            - Show config status")
        print("  7. scenarios         - List scenario categories")
        print("  8. run_scenarios     - Run test scenarios")
        print("  9. regression        - Run regression analysis")
        print("  0. exit              - Exit")
        print("="*50)
        
        choice = input("\nEnter command number: ").strip()
        
        if choice == "0" or choice.lower() == "exit":
            print("👋 Goodbye!")
            break
        
        elif choice == "1":
            result = await server._list_flows({"include_details": True})
            print(result[0].text)
        
        elif choice == "2":
            flow_name = input("Enter flow name (e.g., Create_property): ").strip()
            if flow_name:
                result = await server._analyze_flow({"flow_name": flow_name})
                print(result[0].text)
        
        elif choice == "3":
            query = input("Enter your question: ").strip()
            flow_name = input("Flow name (optional, press Enter to skip): ").strip()
            args = {"query": query}
            if flow_name:
                args["flow_name"] = flow_name
            result = await server._query_flow(args)
            print(result[0].text)
        
        elif choice == "4":
            flow_name = input("Enter flow name: ").strip()
            if flow_name:
                result = await server._check_best_practices({"flow_name": flow_name})
                print(result[0].text)
        
        elif choice == "5":
            flow_name = input("Enter flow name: ").strip()
            if flow_name:
                result = await server._get_flow_dependencies({"flow_name": flow_name})
                print(result[0].text)
        
        elif choice == "6":
            result = await server._get_config_status({})
            print(result[0].text)
        
        elif choice == "7":
            result = await server._list_scenario_categories({})
            print(result[0].text)
        
        elif choice == "8":
            flow_name = input("Flow name (optional, press Enter for all): ").strip()
            limit = input("Max scenarios to run (default 5): ").strip()
            args = {"limit": int(limit) if limit else 5}
            if flow_name:
                args["flow_name"] = flow_name
            result = await server._run_scenarios(args)
            print(result[0].text)
        
        elif choice == "9":
            result = await server._run_regression({})
            print(result[0].text)
        
        else:
            print("❌ Unknown command. Please enter a number 0-9.")


if __name__ == "__main__":
    asyncio.run(main())
