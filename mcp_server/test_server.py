#!/usr/bin/env python3
"""
Test script for the Salesforce Flow Analyzer MCP Server
Run this to verify the server is working correctly.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.server import FlowAnalyzerMCPServer


async def test_server():
    """Test the MCP server functionality"""
    print("🧪 Testing Salesforce Flow Analyzer MCP Server\n")
    
    server = FlowAnalyzerMCPServer()
    
    # Test 1: List tools
    print("1️⃣ Testing list_tools...")
    try:
        tools = await server.server.list_tools()
        print(f"   ✅ Found {len(tools)} tools")
        for tool in tools[:5]:
            print(f"      - {tool.name}: {tool.description[:50]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: List flows
    print("\n2️⃣ Testing list_flows...")
    try:
        result = await server._list_flows({"include_details": False})
        print(f"   ✅ Result:\n{result[0].text[:500]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Get config status
    print("\n3️⃣ Testing get_config_status...")
    try:
        result = await server._get_config_status({})
        print(f"   ✅ Result:\n{result[0].text[:500]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: List scenario categories
    print("\n4️⃣ Testing list_scenario_categories...")
    try:
        result = await server._list_scenario_categories({})
        print(f"   ✅ Result:\n{result[0].text[:500]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Check best practices (if flows exist)
    print("\n5️⃣ Testing check_best_practices...")
    try:
        result = await server._check_best_practices({"flow_name": "Create_property"})
        print(f"   ✅ Result:\n{result[0].text[:500]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 6: List resources
    print("\n6️⃣ Testing list_resources...")
    try:
        resources = await server.server.list_resources()
        print(f"   ✅ Found {len(resources)} resources")
        for resource in resources[:5]:
            print(f"      - {resource.uri}: {resource.name}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 7: List prompts
    print("\n7️⃣ Testing list_prompts...")
    try:
        prompts = await server.server.list_prompts()
        print(f"   ✅ Found {len(prompts)} prompts")
        for prompt in prompts:
            print(f"      - {prompt.name}: {prompt.description[:50]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(test_server())
