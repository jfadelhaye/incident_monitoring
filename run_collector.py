#!/usr/bin/env python3
"""
Standalone script to run the collector without module import issues.
"""

if __name__ == "__main__":
    from app.services.collector import main
    main()