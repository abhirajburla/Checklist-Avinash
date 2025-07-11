#!/usr/bin/env python3
"""
Utility script to load environment variables from dot env file.txt
"""
import os
import re

def load_env_from_txt():
    """Load environment variables from dot env file.txt"""
    env_file = "dot env file.txt"
    
    if not os.path.exists(env_file):
        print(f"❌ Environment file not found: {env_file}")
        return False
    
    try:
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Extract key=value pairs (skip comments and empty lines)
        env_vars = {}
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Use regex to parse KEY="VALUE" or KEY=VALUE
                match = re.match(r'^([A-Z_][A-Z0-9_]*)=(["\']?)([^"\']*)\2', line)
                if match:
                    key, _, value = match.groups()
                    env_vars[key] = value
                    os.environ[key] = value
        
        print(f"✅ Loaded {len(env_vars)} environment variables")
        
        # Show some key variables (without exposing sensitive data)
        important_keys = ['GOOGLE_API_KEY', 'GEMINI_API_KEY', 'AWS_REGION']
        for key in important_keys:
            if key in env_vars:
                value_preview = env_vars[key][:10] + "..." if len(env_vars[key]) > 10 else env_vars[key]
                print(f"   {key}: {value_preview}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading environment variables: {e}")
        return False

if __name__ == "__main__":
    load_env_from_txt() 