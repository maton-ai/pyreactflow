"""
Basic test file for export method.

Copyright 2025 Maton, Inc. All rights reserved.
Use of this source code is governed by a MIT
license that can be found in the LICENSE file.
"""

import pytest
from pyreactflow import ReactFlow

def test_export_from_code_basic_case():
    """Test basic sequential operations without conditions or loops."""
    code ='''
@flow
def main() -> list[str]:
    customer_ids = get_customer_ids()
    results = []
    return results
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input:"),
        ("operation", "customer_ids = get_customer_ids()"),
        ("operation", "results = []"),
        ("end", "output:  results"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Expected parent relationships (all should be top-level)
    for node in result['nodes']:
        assert 'parentId' not in node, f"Node '{node['data']['label']}' should not have parent but has {node.get('parentId')}"

    # Expected edges (source_label, target_label, edge_label)
    label_map = {n['id']: n['data']['label'] for n in result['nodes']}
    def edge_tuple(e):
        return (
            label_map.get(e['source'], e['source']),
            label_map.get(e['target'], e['target']),
            e.get('label', None)
        )
    actual_edges = set(edge_tuple(e) for e in result['edges'])
    expected_edges = set([
        ("input:", "customer_ids = get_customer_ids()", None),
        ("customer_ids = get_customer_ids()", "results = []", None),
        ("results = []", "output:  results", None),
    ])
    assert expected_edges == actual_edges

def test_export_from_code_basic_condition():
    """Test basic if/else condition with simple statements."""
    code ='''
@flow
def main() -> list[str]:
    customer_ids = get_customer_ids()
    results = []
    if len(customer_ids) > 0:
        print(f"Customers do exist: {len(customer_ids)}")
    else:
        print("No customers")
    return results
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input:"),
        ("operation", "customer_ids = get_customer_ids()"),
        ("operation", "results = []"),
        ("condition", "len(customer_ids) > 0"),
        ("subroutine", "print(f'Customers do exist: {len(customer_ids)}')"),
        ("subroutine", "print('No customers')"),
        ("end", "output:  results"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Expected parent relationships (label -> parent_label or None)
    expected_parents = {
        "input:": None,
        "customer_ids = get_customer_ids()": None,
        "results = []": None,
        "len(customer_ids) > 0": None,
        "print(f'Customers do exist: {len(customer_ids)}')": None,
        "print('No customers')": None,
        "output:  results": None,
    }
    
    # Build label to nodes mapping
    label_to_nodes = {}
    for n in result['nodes']:
        label_to_nodes.setdefault(n['data']['label'], []).append(n)
    
    # Check parent relationships
    for label, parent_label in expected_parents.items():
        for node in label_to_nodes.get(label, []):
            if parent_label is None:
                assert 'parentId' not in node, f"Node '{label}' should not have parent but has {node.get('parentId')}"
            else:
                # Find the expected parent node id by label
                parent_nodes = label_to_nodes.get(parent_label, [])
                assert parent_nodes, f"Expected parent node with label '{parent_label}' not found"
                parent_ids = {pn['id'] for pn in parent_nodes}
                assert node.get('parentId') in parent_ids, f"Node '{label}' should have parentId in {parent_ids}, got {node.get('parentId')}"

    # Expected edges (source_label, target_label, edge_label)
    label_map = {n['id']: n['data']['label'] for n in result['nodes']}
    def edge_tuple(e):
        return (
            label_map.get(e['source'], e['source']),
            label_map.get(e['target'], e['target']),
            e.get('label', None)
        )
    actual_edges = set(edge_tuple(e) for e in result['edges'])
    expected_edges = set([
        ("input:", "customer_ids = get_customer_ids()", None),
        ("customer_ids = get_customer_ids()", "results = []", None),
        ("results = []", "len(customer_ids) > 0", None),
        ("len(customer_ids) > 0", "print(f'Customers do exist: {len(customer_ids)}')", "Yes"),
        ("len(customer_ids) > 0", "print('No customers')", "No"),
        ("print(f'Customers do exist: {len(customer_ids)}')", "output:  results", None),
        ("print('No customers')", "output:  results", None),
    ])
    assert expected_edges == actual_edges

def test_export_from_code_sequential_within_loop():
    code ='''
@flow
def main() -> list[str]:
    customer_ids = get_customer_ids()
    results = []
    for customer_id in customer_ids:
        results.append(process_customer(customer_id))
        notify_customer(customer_id)
    return results
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input:"),
        ("operation", "customer_ids = get_customer_ids()"),
        ("operation", "results = []"),
        ("loop", "for customer_id in customer_ids"),
        ("subroutine", "results.append(process_customer(customer_id))"),
        ("subroutine", "notify_customer(customer_id)"),
        ("end", "output:  results"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Expected parent relationships (label -> parent_label or None)
    expected_parents = {
        "input:": None,
        "customer_ids = get_customer_ids()": None,
        "results = []": None,
        "for customer_id in customer_ids": None,
        "results.append(process_customer(customer_id))": "for customer_id in customer_ids",
        "notify_customer(customer_id)": "for customer_id in customer_ids",
        "output:  results": None,
    }
    
    # Build label to nodes mapping
    label_to_nodes = {}
    for n in result['nodes']:
        label_to_nodes.setdefault(n['data']['label'], []).append(n)
    
    # Check parent relationships
    for label, parent_label in expected_parents.items():
        for node in label_to_nodes.get(label, []):
            if parent_label is None:
                assert 'parentId' not in node, f"Node '{label}' should not have parent but has {node.get('parentId')}"
            else:
                # Find the expected parent node id by label
                parent_nodes = label_to_nodes.get(parent_label, [])
                assert parent_nodes, f"Expected parent node with label '{parent_label}' not found"
                parent_ids = {pn['id'] for pn in parent_nodes}
                assert node.get('parentId') in parent_ids, f"Node '{label}' should have parentId in {parent_ids}, got {node.get('parentId')}"

    # Expected edges (source_label, target_label, edge_label)
    label_map = {n['id']: n['data']['label'] for n in result['nodes']}
    def edge_tuple(e):
        return (
            label_map.get(e['source'], e['source']),
            label_map.get(e['target'], e['target']),
            e.get('label', None)
        )
    actual_edges = set(edge_tuple(e) for e in result['edges'])
    expected_edges = set([
        ("input:", "customer_ids = get_customer_ids()", None),
        ("customer_ids = get_customer_ids()", "results = []", None),
        ("results = []", "for customer_id in customer_ids", None),
        ("for customer_id in customer_ids", "output:  results", None),
        ("results.append(process_customer(customer_id))", "notify_customer(customer_id)", None),
    ])
    assert expected_edges == actual_edges

def test_export_from_code_loop_node_merge():
    code = '''
@flow
def main() -> list[str]:
    customer_ids = get_customer_ids()
    results = []
    if len(customer_ids) > 0:
        for customer_id in customer_ids:
            results.append(process_customer(customer_id))
    else:
        for customer_id in customer_ids:
            notify_customer(customer_id)
    return results
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input:"),
        ("operation", "customer_ids = get_customer_ids()"),
        ("operation", "results = []"),
        ("condition", "len(customer_ids) > 0"),
        ("loop", "for customer_id in customer_ids"),
        ("subroutine", "results.append(process_customer(customer_id))"),
        ("subroutine", "notify_customer(customer_id)"),
        ("end", "output:  results"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Expected parent relationships (label -> parent_label or None)
    expected_parents = {
        "input:": None,
        "customer_ids = get_customer_ids()": None,
        "results = []": None,
        "len(customer_ids) > 0": None,
        "for customer_id in customer_ids": None,
        "results.append(process_customer(customer_id))": "for customer_id in customer_ids",
        "notify_customer(customer_id)": "for customer_id in customer_ids",
        "output:  results": None,
    }
    # There are two loops with the same label, both should have the same parent
    # We'll check all nodes with that label
    label_to_nodes = {}
    for n in result['nodes']:
        label_to_nodes.setdefault(n['data']['label'], []).append(n)
    for label, parent_label in expected_parents.items():
        for node in label_to_nodes.get(label, []):
            if parent_label is None:
                assert 'parentId' not in node
            else:
                # Find the expected parent node id by label
                parent_nodes = label_to_nodes.get(parent_label, [])
                assert parent_nodes, f"Expected parent node with label '{parent_label}' not found"
                parent_ids = {pn['id'] for pn in parent_nodes}
                assert node.get('parentId') in parent_ids, f"Node '{label}' should have parentId in {parent_ids}, got {node.get('parentId')}"

    # Expected edges (source, target, label if present)
    label_map = {n['id']: n['data']['label'] for n in result['nodes']}
    def edge_tuple(e):
        return (
            label_map.get(e['source'], e['source']),
            label_map.get(e['target'], e['target']),
            e.get('label', None)
        )
    actual_edges = set(edge_tuple(e) for e in result['edges'])
    expected_edges = set([
        ("results = []", "len(customer_ids) > 0", None),
        ("customer_ids = get_customer_ids()", "results = []", None),
        ("input:", "customer_ids = get_customer_ids()", None),
        ("len(customer_ids) > 0", "for customer_id in customer_ids", "Yes"),
        ("len(customer_ids) > 0", "for customer_id in customer_ids", "No"),
        ("for customer_id in customer_ids", "output:  results", None),
    ])
    assert expected_edges == actual_edges

def test_export_from_code_loop_node_merge_with_sequential():
    """Test that loops with multiple sequential statements get merged into combined nodes."""
    code = '''
@flow
def main() -> list[str]:
    customer_ids = get_customer_ids()
    results = []
    if len(customer_ids) > 0:
        for customer_id in customer_ids:
            results.append(process_customer(customer_id))
            notify_customer(customer_id)
    else:
        for customer_id in customer_ids:
            notify_customer(customer_id)
    return results
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input:"),
        ("operation", "customer_ids = get_customer_ids()"),
        ("operation", "results = []"),
        ("condition", "len(customer_ids) > 0"),
        ("loop", "for customer_id in customer_ids"),
        ("subroutine", "results.append(process_customer(customer_id))"),
        ("subroutine", "notify_customer(customer_id)"),
        ("end", "output:  results"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Expected parent relationships (label -> parent_label or None)
    expected_parents = {
        "input:": None,
        "customer_ids = get_customer_ids()": None,
        "results = []": None,
        "len(customer_ids) > 0": None,
        "for customer_id in customer_ids": None,
        "results.append(process_customer(customer_id))": "for customer_id in customer_ids",
        "notify_customer(customer_id)": "for customer_id in customer_ids",
        "output:  results": None,
    }

    # Create mapping from label to parent label
    label_to_parent = {}
    node_map = {n['id']: n for n in result['nodes']}
    for node in result['nodes']:
        label = node['data']['label']
        parent_id = node.get('parentId')
        parent_label = node_map[parent_id]['data']['label'] if parent_id else None
        label_to_parent[label] = parent_label

    assert expected_parents == label_to_parent

    # Expected edges (source_label, target_label, edge_label)
    expected_edges = set([
        ("results = []", "len(customer_ids) > 0", None),
        ("customer_ids = get_customer_ids()", "results = []", None),
        ("input:", "customer_ids = get_customer_ids()", None),
        ("len(customer_ids) > 0", "for customer_id in customer_ids", "Yes"),
        ("len(customer_ids) > 0", "for customer_id in customer_ids", "No"),
        ("results.append(process_customer(customer_id))", "notify_customer(customer_id)", None),
        ("for customer_id in customer_ids", "output:  results", None),
    ])
    
    actual_edges = set()
    for edge in result['edges']:
        source_label = node_map[edge['source']]['data']['label']
        target_label = node_map[edge['target']]['data']['label']
        edge_label = edge.get('label')
        actual_edges.add((source_label, target_label, edge_label))
    
    assert expected_edges == actual_edges

def test_export_from_code_condition_inside_while_loop():
    code = '''
def main() -> None:
    while True:
        now = datetime.now()
        # Determine today's 9 AM
        target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now >= target_time:
            # It's past 9 AM: fetch and print, then schedule for next day
            pokemon = fetch_random_pokemon()
            print(pokemon)
            next_run = target_time + timedelta(days=1)
            sleep_secs = (next_run - now).total_seconds()
        else:
            # Before 9 AM: wait until 9 AM today
            sleep_secs = (target_time - now).total_seconds()

        time.sleep(sleep_secs)
    '''

    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input:"),
        ("loop", "while True"),
        ("operation", "now = datetime.now()"),
        ("operation", "target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)"),
        ("condition", "now >= target_time"),
        ("operation", "pokemon = fetch_random_pokemon()"),
        ("subroutine", "print(pokemon)"),
        ("operation", "next_run = target_time + timedelta(days=1)"),
        ("operation", "sleep_secs = (next_run - now).total_seconds()"),
        ("operation", "sleep_secs = (target_time - now).total_seconds()"),
        ("subroutine", "time.sleep(sleep_secs)"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Expected parent relationships (label -> parent_label or None)
    expected_parents = {
        "input:": None,
        "while True": None,
        "now = datetime.now()": "while True",
        "target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)": "while True",
        "now >= target_time": "while True",
        "pokemon = fetch_random_pokemon()": "while True",
        "print(pokemon)": "while True",
        "next_run = target_time + timedelta(days=1)": "while True",
        "sleep_secs = (next_run - now).total_seconds()": "while True",
        "sleep_secs = (target_time - now).total_seconds()": "while True",
        "time.sleep(sleep_secs)": "while True",
    }

    # Build label to nodes mapping
    label_to_nodes = {}
    for n in result['nodes']:
        label_to_nodes.setdefault(n['data']['label'], []).append(n)

    # Check parent relationships
    for label, parent_label in expected_parents.items():
        for node in label_to_nodes.get(label, []):
            if parent_label is None:
                assert 'parentId' not in node, f"Node '{label}' should not have parent but has {node.get('parentId')}"
            else:
                # Find the expected parent node id by label
                parent_nodes = label_to_nodes.get(parent_label, [])
                assert parent_nodes, f"Expected parent node with label '{parent_label}' not found"
                parent_ids = {pn['id'] for pn in parent_nodes}
                assert node.get('parentId') in parent_ids, f"Node '{label}' should have parentId in {parent_ids}, got {node.get('parentId')}"

    # Expected edges (source_label, target_label, edge_label)
    label_map = {n['id']: n['data']['label'] for n in result['nodes']}
    def edge_tuple(e):
        return (
            label_map.get(e['source'], e['source']),
            label_map.get(e['target'], e['target']),
            e.get('label', None)
        )
    actual_edges = set(edge_tuple(e) for e in result['edges'])
    expected_edges = set([
        ("input:", "while True", None),
        ("now = datetime.now()", "target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)", None),
        ("target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)", "now >= target_time", None),
        ("now >= target_time", "pokemon = fetch_random_pokemon()", "Yes"),
        ("now >= target_time", "sleep_secs = (target_time - now).total_seconds()", "No"),
        ("pokemon = fetch_random_pokemon()", "print(pokemon)", None),
        ("print(pokemon)", "next_run = target_time + timedelta(days=1)", None),
        ("next_run = target_time + timedelta(days=1)", "sleep_secs = (next_run - now).total_seconds()", None),
        ("sleep_secs = (next_run - now).total_seconds()", "time.sleep(sleep_secs)", None),
        ("sleep_secs = (target_time - now).total_seconds()", "time.sleep(sleep_secs)", None),
    ])
    assert expected_edges == actual_edges

def test_export_from_code_exclude_docstring():
    code = '''
def main() -> None:
    """
    Runs daily at 9 AM to fetch and print a random Pokémon.
    Random pokemon is fetched from PokeAPI.
    """
    while True:
        now = datetime.now()
        # Determine today's 9 AM
        target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now >= target_time:
            # It's past 9 AM: fetch and print, then schedule for next day
            pokemon = fetch_random_pokemon()
            print(pokemon)
            next_run = target_time + timedelta(days=1)
            sleep_secs = (next_run - now).total_seconds()
        else:
            # Before 9 AM: wait until 9 AM today
            sleep_secs = (target_time - now).total_seconds()

        time.sleep(sleep_secs)
    '''

    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input:"),
        ("loop", "while True"),
        ("operation", "now = datetime.now()"),
        ("operation", "target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)"),
        ("condition", "now >= target_time"),
        ("operation", "pokemon = fetch_random_pokemon()"),
        ("subroutine", "print(pokemon)"),
        ("operation", "next_run = target_time + timedelta(days=1)"),
        ("operation", "sleep_secs = (next_run - now).total_seconds()"),
        ("operation", "sleep_secs = (target_time - now).total_seconds()"),
        ("subroutine", "time.sleep(sleep_secs)"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Expected parent relationships (label -> parent_label or None)
    expected_parents = {
        "input:": None,
        "while True": None,
        "now = datetime.now()": "while True",
        "target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)": "while True",
        "now >= target_time": "while True",
        "pokemon = fetch_random_pokemon()": "while True",
        "print(pokemon)": "while True",
        "next_run = target_time + timedelta(days=1)": "while True",
        "sleep_secs = (next_run - now).total_seconds()": "while True",
        "sleep_secs = (target_time - now).total_seconds()": "while True",
        "time.sleep(sleep_secs)": "while True",
    }

    # Build label to nodes mapping
    label_to_nodes = {}
    for n in result['nodes']:
        label_to_nodes.setdefault(n['data']['label'], []).append(n)

    # Check parent relationships
    for label, parent_label in expected_parents.items():
        for node in label_to_nodes.get(label, []):
            if parent_label is None:
                assert 'parentId' not in node, f"Node '{label}' should not have parent but has {node.get('parentId')}"
            else:
                # Find the expected parent node id by label
                parent_nodes = label_to_nodes.get(parent_label, [])
                assert parent_nodes, f"Expected parent node with label '{parent_label}' not found"
                parent_ids = {pn['id'] for pn in parent_nodes}
                assert node.get('parentId') in parent_ids, f"Node '{label}' should have parentId in {parent_ids}, got {node.get('parentId')}"

    # Expected edges (source_label, target_label, edge_label)
    label_map = {n['id']: n['data']['label'] for n in result['nodes']}
    def edge_tuple(e):
        return (
            label_map.get(e['source'], e['source']),
            label_map.get(e['target'], e['target']),
            e.get('label', None)
        )
    actual_edges = set(edge_tuple(e) for e in result['edges'])
    expected_edges = set([
        ("input:", "while True", None),
        ("now = datetime.now()", "target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)", None),
        ("target_time = now.replace(hour=9, minute=0, second=0, microsecond=0)", "now >= target_time", None),
        ("now >= target_time", "pokemon = fetch_random_pokemon()", "Yes"),
        ("now >= target_time", "sleep_secs = (target_time - now).total_seconds()", "No"),
        ("pokemon = fetch_random_pokemon()", "print(pokemon)", None),
        ("print(pokemon)", "next_run = target_time + timedelta(days=1)", None),
        ("next_run = target_time + timedelta(days=1)", "sleep_secs = (next_run - now).total_seconds()", None),
        ("sleep_secs = (next_run - now).total_seconds()", "time.sleep(sleep_secs)", None),
        ("sleep_secs = (target_time - now).total_seconds()", "time.sleep(sleep_secs)", None),
    ])
    assert expected_edges == actual_edges

def test_export_from_code_condition_node_yes_only():
    code = '''
@flow
def main() -> str:
    # 1. Create spreadsheet
    spreadsheet_id = create_spreadsheet()

    # Prepare header row
    header = ["Title", "Image URL", "Price", "Description", "Hype Level", "Resale Value", "Link"]
    append_row_to_sheet(spreadsheet_id, "Sheet1!A1:G1", header)

    # 2. Fetch and parse
    html = fetch_nike_upcoming_drops()
    products = parse_html(html)

    # 3. Load existing links
    existing = get_existing_links(spreadsheet_id, "Sheet1!G2:G")

    # 4 & 5. Analyze and append only new products
    for p in products:
        if p["Link"] not in existing:
            enriched = analyze_product(p)
            row = [
                enriched["Title"],
                enriched["Image URL"],
                enriched["Price"],
                enriched["Description"],
                enriched["Hype Level"],
                enriched["Resale Value"],
                enriched["Link"]
            ]
            append_row_to_sheet(spreadsheet_id, "Sheet1!A2:G2", row)

    return spreadsheet_id
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input:"),
        ("operation", "spreadsheet_id = create_spreadsheet()"),
        ("operation", "header = ['Title', 'Image URL', 'Price', 'Description', 'Hype Level', 'Resale Value', 'Link']"),
        ("subroutine", "append_row_to_sheet(spreadsheet_id, 'Sheet1!A1:G1', header)"),
        ("operation", "html = fetch_nike_upcoming_drops()"),
        ("operation", "products = parse_html(html)"),
        ("operation", "existing = get_existing_links(spreadsheet_id, 'Sheet1!G2:G')"),
        ("loop", "for p in products"),
        ("condition", "p['Link'] not in existing"),
        ("operation", "enriched = analyze_product(p)"),
        ("operation", "row = [enriched['Title'], enriched['Image URL'], enriched['Price'], enriched['Description'], enriched['Hype Level'], enriched['Resale Value'], enriched['Link']]"),
        ("subroutine", "append_row_to_sheet(spreadsheet_id, 'Sheet1!A2:G2', row)"),
        ("end", "output:  spreadsheet_id"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Expected parent relationships (label -> parent_label or None)
    expected_parents = {
        "input:": None,
        "spreadsheet_id = create_spreadsheet()": None,
        "header = ['Title', 'Image URL', 'Price', 'Description', 'Hype Level', 'Resale Value', 'Link']": None,
        "append_row_to_sheet(spreadsheet_id, 'Sheet1!A1:G1', header)": None,
        "html = fetch_nike_upcoming_drops()": None,
        "products = parse_html(html)": None,
        "existing = get_existing_links(spreadsheet_id, 'Sheet1!G2:G')": None,
        "for p in products": None,
        "p['Link'] not in existing": "for p in products",
        "enriched = analyze_product(p)": "for p in products",
        "row = [enriched['Title'], enriched['Image URL'], enriched['Price'], enriched['Description'], enriched['Hype Level'], enriched['Resale Value'], enriched['Link']]": "for p in products",
        "append_row_to_sheet(spreadsheet_id, 'Sheet1!A2:G2', row)": "for p in products",
        "output:  spreadsheet_id": None,
    }

    # Build label to nodes mapping
    label_to_nodes = {}
    for n in result['nodes']:
        label_to_nodes.setdefault(n['data']['label'], []).append(n)

    # Check parent relationships
    label_to_parent = {}
    node_map = {n['id']: n for n in result['nodes']}
    for node in result['nodes']:
        label = node['data']['label']
        parent_id = node.get('parentId')
        parent_label = node_map[parent_id]['data']['label'] if parent_id else None
        label_to_parent[label] = parent_label

    assert expected_parents == label_to_parent

    # Expected edges (source_label, target_label, edge_label)
    label_map = {n['id']: n['data']['label'] for n in result['nodes']}
    def edge_tuple(e):
        return (
            label_map.get(e['source'], e['source']),
            label_map.get(e['target'], e['target']),
            e.get('label', None)
        )
    actual_edges = set(edge_tuple(e) for e in result['edges'])
    expected_edges = set([
        ("input:", "spreadsheet_id = create_spreadsheet()", None),
        ("spreadsheet_id = create_spreadsheet()", "header = ['Title', 'Image URL', 'Price', 'Description', 'Hype Level', 'Resale Value', 'Link']", None),
        ("header = ['Title', 'Image URL', 'Price', 'Description', 'Hype Level', 'Resale Value', 'Link']", "append_row_to_sheet(spreadsheet_id, 'Sheet1!A1:G1', header)", None),
        ("append_row_to_sheet(spreadsheet_id, 'Sheet1!A1:G1', header)", "html = fetch_nike_upcoming_drops()", None),
        ("html = fetch_nike_upcoming_drops()", "products = parse_html(html)", None),
        ("products = parse_html(html)", "existing = get_existing_links(spreadsheet_id, 'Sheet1!G2:G')", None),
        ("existing = get_existing_links(spreadsheet_id, 'Sheet1!G2:G')", "for p in products", None),
        ("p['Link'] not in existing", "enriched = analyze_product(p)", "Yes"),
        ("enriched = analyze_product(p)", "row = [enriched['Title'], enriched['Image URL'], enriched['Price'], enriched['Description'], enriched['Hype Level'], enriched['Resale Value'], enriched['Link']]", None),
        ("row = [enriched['Title'], enriched['Image URL'], enriched['Price'], enriched['Description'], enriched['Hype Level'], enriched['Resale Value'], enriched['Link']]", "append_row_to_sheet(spreadsheet_id, 'Sheet1!A2:G2', row)", None),
        ("for p in products", "output:  spreadsheet_id", None),
    ])
    assert expected_edges == actual_edges

def test_export_from_code_condition_node_merge():
    code = '''
@flow
def main() -> list[str]:
    customer_ids = get_customer_ids()
    results = []
    for customer_id in customer_ids:
        if customer_id != "a":
            results.append(process_customer(customer_id))
        else:
            print("do not process customer a")
    for customer_id in customer_ids:
        notify_customer(customer_id)
    return results
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input:"),
        ("operation", "customer_ids = get_customer_ids()"),
        ("operation", "results = []"),
        ("loop", "for customer_id in customer_ids"),
        ("condition", "customer_id != 'a'"),
        ("subroutine", "results.append(process_customer(customer_id))"),
        ("subroutine", "print('do not process customer a')"),
        ("loop", "for customer_id in customer_ids"),
        ("subroutine", "notify_customer(customer_id)"),
        ("end", "output:  results"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Expected parent relationships (label -> parent_label or None)
    expected_parents = {
        "input:": None,
        "customer_ids = get_customer_ids()": None,
        "results = []": None,
        "for customer_id in customer_ids": None,
        'customer_id != "a"': "for customer_id in customer_ids",
        "results.append(process_customer(customer_id))": "for customer_id in customer_ids",
        "print('do not process customer a')": "for customer_id in customer_ids",
        "notify_customer(customer_id)": "for customer_id in customer_ids",
        "output:  results": None,
    }
    # There are two loops with the same label, both should have the same parent
    # We'll check all nodes with that label
    label_to_nodes = {}
    for n in result['nodes']:
        label_to_nodes.setdefault(n['data']['label'], []).append(n)
    for label, parent_label in expected_parents.items():
        for node in label_to_nodes.get(label, []):
            if parent_label is None:
                assert 'parentId' not in node
            else:
                # Find the expected parent node id by label
                parent_nodes = label_to_nodes.get(parent_label, [])
                assert parent_nodes, f"Expected parent node with label '{parent_label}' not found"
                parent_ids = {pn['id'] for pn in parent_nodes}
                assert node.get('parentId') in parent_ids, f"Node '{label}' should have parentId in {parent_ids}, got {node.get('parentId')}"

    # Expected edges (source, target, label if present)
    label_map = {n['id']: n['data']['label'] for n in result['nodes']}
    def edge_tuple(e):
        return (
            label_map.get(e['source'], e['source']),
            label_map.get(e['target'], e['target']),
            e.get('label', None)
        )
    actual_edges = set(edge_tuple(e) for e in result['edges'])
    expected_edges = set([
        ("results = []", "for customer_id in customer_ids", None),
        ("customer_ids = get_customer_ids()", "results = []", None),
        ("input:", "customer_ids = get_customer_ids()", None),
        ("for customer_id in customer_ids", "for customer_id in customer_ids", None),
        ("customer_id != 'a'", "results.append(process_customer(customer_id))", "Yes"),
        ("customer_id != 'a'", "print('do not process customer a')", "No"),
        ("for customer_id in customer_ids", "output:  results", None),
    ])
    assert expected_edges == actual_edges

def test_export_from_code_complex_nested_if_else():
    """Test complex nested if/else with loops and sequential statements."""
    code = '''
@flow
def main() -> list[str]:
    customer_ids = get_customer_ids()
    results = []
    if len(customer_ids) > 0:
        for customer_id in customer_ids:
            results.append(process_customer(customer_id))
        notify_customer("")
    else:
        for customer_id in customer_ids:
            notify_customer(customer_id)
        results.append("")
    results.append("final")
    return results
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input:"),
        ("operation", "customer_ids = get_customer_ids()"),
        ("operation", "results = []"),
        ("condition", "len(customer_ids) > 0"),
        ("loop", "for customer_id in customer_ids"),
        ("subroutine", "results.append(process_customer(customer_id))"),
        ("subroutine", "notify_customer('')"),
        ("subroutine", "notify_customer(customer_id)"),
        ("loop", "for customer_id in customer_ids"),
        ("subroutine", "results.append('')"),
        ("operation", "results.append('final')"),
        ("end", "output:  results"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Expected parent relationships (label -> parent_label or None)
    expected_parents = {
        "input:": None,
        "customer_ids = get_customer_ids()": None,
        "results = []": None,
        "len(customer_ids) > 0": None,
        "for customer_id in customer_ids": None,
        "results.append(process_customer(customer_id))": "for customer_id in customer_ids",
        "notify_customer('')": None,
        "notify_customer(customer_id)": "for customer_id in customer_ids",
        "results.append('')": None,
        "results.append('final')": None,
        "output:  results": None,
    }
    
    # Build label to nodes mapping
    label_to_nodes = {}
    for n in result['nodes']:
        label_to_nodes.setdefault(n['data']['label'], []).append(n)
    
    # Check parent relationships
    for label, parent_label in expected_parents.items():
        for node in label_to_nodes.get(label, []):
            if parent_label is None:
                assert 'parentId' not in node, f"Node '{label}' should not have parent but has {node.get('parentId')}"
            else:
                # Find the expected parent node id by label
                parent_nodes = label_to_nodes.get(parent_label, [])
                assert parent_nodes, f"Expected parent node with label '{parent_label}' not found"
                parent_ids = {pn['id'] for pn in parent_nodes}
                assert node.get('parentId') in parent_ids, f"Node '{label}' should have parentId in {parent_ids}, got {node.get('parentId')}"

    # Expected edges (source_label, target_label, edge_label)
    label_map = {n['id']: n['data']['label'] for n in result['nodes']}
    def edge_tuple(e):
        return (
            label_map.get(e['source'], e['source']),
            label_map.get(e['target'], e['target']),
            e.get('label', None)
        )
    actual_edges = set(edge_tuple(e) for e in result['edges'])
    expected_edges = set([
        ("input:", "customer_ids = get_customer_ids()", None),
        ("customer_ids = get_customer_ids()", "results = []", None),
        ("results = []", "len(customer_ids) > 0", None),
        ("len(customer_ids) > 0", "for customer_id in customer_ids", "Yes"),
        ("len(customer_ids) > 0", "for customer_id in customer_ids", "No"),
        ("for customer_id in customer_ids", "notify_customer('')", None),
        ("for customer_id in customer_ids", "results.append('')", None),
        ("notify_customer('')", "results.append('final')", None),
        ("results.append('')", "results.append('final')", None),
        ("results.append('final')", "output:  results", None),
    ])
    assert expected_edges == actual_edges

def test_export_from_code_depth_limit_enforcement():
    """Test depth limit enforcement for complex nested structures from example.py"""
    code = '''
@flow
def main() -> list[str]:
    customer_ids = get_customer_ids()
    options = ["a", "b", "c"]
    results = []
    for customer_id in customer_ids:
        if len(customer_ids) > 0:
            for option in options:
                assign_option_to_customer(option, customer_id)
            results.append(process_customer(customer_id))
        else:
            print("no need for assigning since there is no customer")
    return results
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input:"),
        ("operation", "customer_ids = get_customer_ids()"),
        ("operation", "options = ['a', 'b', 'c']"),
        ("operation", "results = []"),
        ("loop", "for customer_id in customer_ids"),
        ("condition", "len(customer_ids) > 0"),
        ("loop", "for option in options \u2192 assign_option_to_customer(option, customer_id)"),
        ("subroutine", "results.append(process_customer(customer_id))"),
        ("subroutine", "print('no need for assigning since there is no customer')"),
        ("end", "output:  results"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Expected parent relationships (label -> parent_label or None)
    expected_parents = {
        "input:": None,
        "customer_ids = get_customer_ids()": None,
        "options = ['a', 'b', 'c']": None,
        "results = []": None,
        "for customer_id in customer_ids": None,
        "len(customer_ids) > 0": "for customer_id in customer_ids",
        "for option in options \u2192 assign_option_to_customer(option, customer_id)": "for customer_id in customer_ids",
        "results.append(process_customer(customer_id))": "for customer_id in customer_ids",
        "print('no need for assigning since there is no customer')": "for customer_id in customer_ids",
        "output:  results": None,
    }
    
    # Build label to nodes mapping
    label_to_nodes = {}
    for n in result['nodes']:
        label_to_nodes.setdefault(n['data']['label'], []).append(n)
    
    # Check parent relationships
    for label, parent_label in expected_parents.items():
        for node in label_to_nodes.get(label, []):
            if parent_label is None:
                assert 'parentId' not in node, f"Node '{label}' should not have parent but has {node.get('parentId')}"
            else:
                # Find the expected parent node id by label
                parent_nodes = label_to_nodes.get(parent_label, [])
                assert parent_nodes, f"Expected parent node with label '{parent_label}' not found"
                parent_ids = {pn['id'] for pn in parent_nodes}
                assert node.get('parentId') in parent_ids, f"Node '{label}' should have parentId in {parent_ids}, got {node.get('parentId')}"

    # Verify depth <= 1: check that no node has a parent that itself has a parent
    for node in result['nodes']:
        if 'parentId' in node:
            parent_node = next((n for n in result['nodes'] if n['id'] == node['parentId']), None)
            assert parent_node is not None, f"Parent node {node['parentId']} not found for {node['id']}"
            assert 'parentId' not in parent_node, f"Depth > 1 violation: node {node['id']} has parent {parent_node['id']} which itself has parent {parent_node.get('parentId')}"

    # Expected edges (source_label, target_label, edge_label)
    label_map = {n['id']: n['data']['label'] for n in result['nodes']}
    def edge_tuple(e):
        return (
            label_map.get(e['source'], e['source']),
            label_map.get(e['target'], e['target']),
            e.get('label', None)
        )
    actual_edges = set(edge_tuple(e) for e in result['edges'])
    expected_edges = set([
        ("input:", "customer_ids = get_customer_ids()", None),
        ("customer_ids = get_customer_ids()", "options = ['a', 'b', 'c']", None),
        ("options = ['a', 'b', 'c']", "results = []", None),
        ("results = []", "for customer_id in customer_ids", None),
        ("len(customer_ids) > 0", "for option in options \u2192 assign_option_to_customer(option, customer_id)", "Yes"),
        ("for option in options \u2192 assign_option_to_customer(option, customer_id)", "results.append(process_customer(customer_id))", None),
        ("len(customer_ids) > 0", "print('no need for assigning since there is no customer')", "No"),
        ("for customer_id in customer_ids", "output:  results", None),
    ])
    assert expected_edges == actual_edges

def test_export_from_code_sequential_steps_in_loop():
    code = '''
@flow
def main(
    stripe_api_key: str,
    hubspot_api_key: str,
    openai_api_key: str,
    slack_webhook_url: str,
    slack_channel: str
) -> list[str]:
    customers = fetch_new_stripe_customers(stripe_api_key)
    summaries: list[str] = []
    for customer in customers:
        create_hubspot_contact(customer, hubspot_api_key)
        email = customer.get("email", "")
        domain = email.split("@")[1] if "@" in email else ""
        metadata = fetch_company_metadata(domain)
        summary = summarize_company(metadata, openai_api_key)
        send_slack_message(summary, slack_webhook_url, slack_channel)
        summaries.append(summary)
    return summaries
'''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input: stripe_api_key, hubspot_api_key, openai_api_key, slack_webhook_url, slack_channel"),
        ("operation", "customers = fetch_new_stripe_customers(stripe_api_key)"),
        ("operation", "summaries: list[str] = []"),
        ("loop", "for customer in customers"),
        ("subroutine", "create_hubspot_contact(customer, hubspot_api_key)"),
        ("operation", "email = customer.get('email', '')"),
        ("operation", "domain = email.split('@')[1] if '@' in email else ''"),
        ("operation", "metadata = fetch_company_metadata(domain)"),
        ("operation", "summary = summarize_company(metadata, openai_api_key)"),
        ("subroutine", "send_slack_message(summary, slack_webhook_url, slack_channel)"),
        ("subroutine", "summaries.append(summary)"),
        ("end", "output:  summaries"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Expected parent relationships (label -> parent_label or None)
    expected_parents = {
        "input: stripe_api_key, hubspot_api_key, openai_api_key, slack_webhook_url, slack_channel": None,
        "customers = fetch_new_stripe_customers(stripe_api_key)": None,
        "summaries: list[str] = []": None,
        "for customer in customers": None,
        "create_hubspot_contact(customer, hubspot_api_key)": "for customer in customers",
        "email = customer.get('email', '')": "for customer in customers",
        "domain = email.split('@')[1] if '@' in email else ''": "for customer in customers",
        "metadata = fetch_company_metadata(domain)": "for customer in customers",
        "summary = summarize_company(metadata, openai_api_key)": "for customer in customers",
        "send_slack_message(summary, slack_webhook_url, slack_channel)": "for customer in customers",
        "summaries.append(summary)": "for customer in customers",
        "output:  summaries": None,
    }
    
    # Build label to nodes mapping
    label_to_nodes = {}
    for n in result['nodes']:
        label_to_nodes.setdefault(n['data']['label'], []).append(n)
    
    # Check parent relationships
    for label, parent_label in expected_parents.items():
        for node in label_to_nodes.get(label, []):
            if parent_label is None:
                assert 'parentId' not in node, f"Node '{label}' should not have parent but has {node.get('parentId')}"
            else:
                # Find the expected parent node id by label
                parent_nodes = label_to_nodes.get(parent_label, [])
                assert parent_nodes, f"Expected parent node with label '{parent_label}' not found"
                parent_ids = {pn['id'] for pn in parent_nodes}
                assert node.get('parentId') in parent_ids, f"Node '{label}' should have parentId in {parent_ids}, got {node.get('parentId')}"

    # Expected edges (source_label, target_label, edge_label)
    label_map = {n['id']: n['data']['label'] for n in result['nodes']}
    def edge_tuple(e):
        return (
            label_map.get(e['source'], e['source']),
            label_map.get(e['target'], e['target']),
            e.get('label', None)
        )
    actual_edges = set(edge_tuple(e) for e in result['edges'])
    expected_edges = set([
        ("input: stripe_api_key, hubspot_api_key, openai_api_key, slack_webhook_url, slack_channel", "customers = fetch_new_stripe_customers(stripe_api_key)", None),
        ("customers = fetch_new_stripe_customers(stripe_api_key)", "summaries: list[str] = []", None),
        ("summaries: list[str] = []", "for customer in customers", None),
        ("for customer in customers", "output:  summaries", None),
        ("create_hubspot_contact(customer, hubspot_api_key)", "email = customer.get('email', '')", None),
        ("email = customer.get('email', '')", "domain = email.split('@')[1] if '@' in email else ''", None),
        ("domain = email.split('@')[1] if '@' in email else ''", "metadata = fetch_company_metadata(domain)", None),
        ("metadata = fetch_company_metadata(domain)", "summary = summarize_company(metadata, openai_api_key)", None),
        ("summary = summarize_company(metadata, openai_api_key)", "send_slack_message(summary, slack_webhook_url, slack_channel)", None),
        ("send_slack_message(summary, slack_webhook_url, slack_channel)", "summaries.append(summary)", None),
    ])
    assert expected_edges == actual_edges

def test_export_from_code_check_structured_task_data():
    """Test export for structured task data extraction logic"""
    code = '''
@flow
def main(email: str, phone_number: str) -> list[str]:
    customer_ids = get_customer_ids()
    results = []
    if len(customer_ids) > 0:
        for customer_id in customer_ids:
            results.append(process_customer(customer_id))
            notify_customer(customer_id)
    else:
        print("no need for assigning since there is no customer")
    return results
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input: email, phone_number"),
        ("operation", "customer_ids = get_customer_ids()"),
        ("operation", "results = []"),
        ("condition", "len(customer_ids) > 0"),
        ("loop", "for customer_id in customer_ids"),
        ("subroutine", "results.append(process_customer(customer_id))"),
        ("subroutine", "notify_customer(customer_id)"),
        ("subroutine", "print('no need for assigning since there is no customer')"),
        ("end", "output:  results"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Expected parent relationships (label -> parent_label or None)
    expected_parents = {
        "input: email, phone_number": None,
        "customer_ids = get_customer_ids()": None,
        "results = []": None,
        "len(customer_ids) > 0": None,
        "for customer_id in customer_ids": None,
        "results.append(process_customer(customer_id))": "for customer_id in customer_ids",
        "notify_customer(customer_id)": "for customer_id in customer_ids",
        "print('no need for assigning since there is no customer')": None,
        "output:  results": None,
    }
    
    # Build label to nodes mapping
    label_to_nodes = {}
    for n in result['nodes']:
        label_to_nodes.setdefault(n['data']['label'], []).append(n)
    
    # Check parent relationships
    for label, parent_label in expected_parents.items():
        for node in label_to_nodes.get(label, []):
            if parent_label is None:
                assert 'parentId' not in node, f"Node '{label}' should not have parent but has {node.get('parentId')}"
            else:
                # Find the expected parent node id by label
                parent_nodes = label_to_nodes.get(parent_label, [])
                assert parent_nodes, f"Expected parent node with label '{parent_label}' not found"
                parent_ids = {pn['id'] for pn in parent_nodes}
                assert node.get('parentId') in parent_ids, f"Node '{label}' should have parentId in {parent_ids}, got {node.get('parentId')}"

    # Expected edges (source_label, target_label, edge_label)
    label_map = {n['id']: n['data']['label'] for n in result['nodes']}
    def edge_tuple(e):
        return (
            label_map.get(e['source'], e['source']),
            label_map.get(e['target'], e['target']),
            e.get('label', None)
        )
    actual_edges = set(edge_tuple(e) for e in result['edges'])
    expected_edges = set([
        ("input: email, phone_number", "customer_ids = get_customer_ids()", None),
        ("customer_ids = get_customer_ids()", "results = []", None),
        ("results = []", "len(customer_ids) > 0", None),
        ("len(customer_ids) > 0", "for customer_id in customer_ids", "Yes"),
        ("len(customer_ids) > 0", "print('no need for assigning since there is no customer')", "No"),
        ("results.append(process_customer(customer_id))", "notify_customer(customer_id)", None),
        ("for customer_id in customer_ids", "output:  results", None),
        ("print('no need for assigning since there is no customer')", "output:  results", None),
    ])
    assert expected_edges == actual_edges

    # Test structured task data
    # Find nodes with tasks and verify structure
    nodes_with_tasks = [n for n in result['nodes'] if 'tasks' in n['data']]
    
    # Verify the get_customer_ids operation has correct task structure
    get_customer_ids_node = next((n for n in result['nodes'] 
                                 if n['data']['label'] == "customer_ids = get_customer_ids()"), None)
    assert get_customer_ids_node is not None
    assert 'tasks' in get_customer_ids_node['data']
    assert len(get_customer_ids_node['data']['tasks']) == 1
    task = get_customer_ids_node['data']['tasks'][0]
    assert task['name'] == 'get_customer_ids'
    assert task['args'] == []

    # Verify the len function call in condition has correct argument structure
    len_condition_node = next((n for n in result['nodes'] 
                              if n['data']['label'] == "len(customer_ids) > 0"), None)
    assert len_condition_node is not None
    assert 'tasks' in len_condition_node['data']
    len_task = next((t for t in len_condition_node['data']['tasks'] if t['name'] == 'len'), None)
    assert len_task is not None
    assert len(len_task['args']) == 1
    assert len_task['args'][0]['name'] == 'customer_ids'
    assert len_task['args'][0]['type'] == 'variable'

    # Verify the process_customer call has correct argument structure
    process_node = next((n for n in result['nodes'] 
                        if 'process_customer' in n['data']['label']), None)
    assert process_node is not None
    assert 'tasks' in process_node['data']
    process_task = next((t for t in process_node['data']['tasks'] if t['name'] == 'process_customer'), None)
    assert process_task is not None
    assert len(process_task['args']) == 1
    assert process_task['args'][0]['name'] == 'customer_id'
    assert process_task['args'][0]['type'] == 'variable'

    # Verify the append method call with nested function call
    append_node = next((n for n in result['nodes'] 
                       if 'results.append' in n['data']['label']), None)
    assert append_node is not None
    assert 'tasks' in append_node['data']
    append_task = next((t for t in append_node['data']['tasks'] if t['name'] == 'append'), None)
    assert append_task is not None
    assert len(append_task['args']) == 1
    assert append_task['args'][0]['name'] == 'function_call'
    assert append_task['args'][0]['type'] == 'call'

    # Verify the notify_customer call has correct argument structure
    notify_node = next((n for n in result['nodes'] 
                       if n['data']['label'] == "notify_customer(customer_id)"), None)
    assert notify_node is not None
    assert 'tasks' in notify_node['data']
    notify_task = next((t for t in notify_node['data']['tasks'] if t['name'] == 'notify_customer'), None)
    assert notify_task is not None
    assert len(notify_task['args']) == 1
    assert notify_task['args'][0]['name'] == 'customer_id'
    assert notify_task['args'][0]['type'] == 'variable'

    # Verify the print statement has correct string argument
    print_node = next((n for n in result['nodes'] 
                      if 'print(' in n['data']['label']), None)
    assert print_node is not None
    assert 'tasks' in print_node['data']
    print_task = next((t for t in print_node['data']['tasks'] if t['name'] == 'print'), None)
    assert print_task is not None
    assert len(print_task['args']) == 1
    assert print_task['args'][0]['type'] == 'string'
    assert 'no need for assigning' in print_task['args'][0]['name']

    # Verify variable assignments
    # Check customer_ids assignment
    get_customer_ids_node = next((n for n in result['nodes'] 
                                 if n['data']['label'] == "customer_ids = get_customer_ids()"), None)
    assert 'vars' in get_customer_ids_node['data']
    assert 'customer_ids' in get_customer_ids_node['data']['vars']

    # Check results assignment
    results_node = next((n for n in result['nodes'] 
                        if n['data']['label'] == "results = []"), None)
    assert 'vars' in results_node['data']
    assert 'results' in results_node['data']['vars']

    # Check loop variable
    loop_node = next((n for n in result['nodes'] 
                     if n['data']['label'] == "for customer_id in customer_ids"), None)
    assert 'vars' in loop_node['data']
    assert 'customer_id' in loop_node['data']['vars']

if __name__ == "__main__":
    pytest.main([__file__])
