"""
Sample code to generate react-flow compatible dict from code.

Copyright 2025 Maton, Inc. All rights reserved.
Use of this source code is governed by a MIT
license that can be found in the LICENSE file.
"""

import json
from pyreactflow import ReactFlow

code = '''
def main() -> list[str]:
    customer_ids = get_customer_ids()
    results = []
    if check_customer_ids_length(customer_ids):
        for customer_id in customer_ids:
            results.append(process_customer(customer_id))
            notify_customer(customer_id)
    else:
        print("no need for processing since there is no customer")
    return results
'''

# Generate the react-flow compatible dict from code
def main():
    rf = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    react_flow = rf.export()
    print(json.dumps(react_flow, indent=2))

if __name__ == "__main__":
    main()
