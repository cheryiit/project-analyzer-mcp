#!/usr/bin/env python3
"""
Enhanced Project Analyzer MCP Server - Main Entry Point
Modular, async-capable Python MCP server for comprehensive project analysis
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.server import ProjectAnalyzerMCPServer


async def main_async():
    """Main async entry point"""
    server = ProjectAnalyzerMCPServer()
    
    # Check if running in test mode
    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        server.run_standalone()
    elif len(sys.argv) > 1 and sys.argv[1] == '--async-test':
        print("=== Async Background Test ===")
        
        # Test background task
        task_id = await server.start_background_task("analyze_code", {
            'project_path': '.',
            'analysis_type': 'comprehensive',
            'output_format': 'markdown'
        })
        print(f"Started background task: {task_id}")
        
        # Check status
        while True:
            result = await server.get_background_task_result(task_id)
            print(f"Task status: {result.get('status', 'unknown')}")
            
            if result.get('status') == 'completed':
                print("Task completed successfully!")
                if 'result' in result:
                    meta = result['result'].get('_meta', {})
                    print(f"Errors: {meta.get('errors_count', 0)}")
                    print(f"Warnings: {meta.get('warnings_count', 0)}")
                break
            elif result.get('status') == 'failed':
                print(f"Task failed: {result.get('error', 'Unknown error')}")
                break
            
            await asyncio.sleep(1)
    else:
        # For now, just run a simple test
        print("Enhanced Project Analyzer Python MCP Server v2.0")
        print("Available tools: project_structure, analyze_files, analyze_code, configure_analyzer, get_stats")
        print("Background tasks: start_background_task, get_background_result")
        
        server.run_standalone()


def main():
    """Main synchronous entry point"""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()