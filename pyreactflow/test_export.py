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
        ("len(customer_ids) > 0", "print(f'Customers do exist: {len(customer_ids)}')", "if len(customer_ids) > 0"),
        ("len(customer_ids) > 0", "print('No customers')", "else"),
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
        ("len(customer_ids) > 0", "for customer_id in customer_ids", "if len(customer_ids) > 0"),
        ("len(customer_ids) > 0", "for customer_id in customer_ids", "else"),
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
        ("len(customer_ids) > 0", "for customer_id in customer_ids", "if len(customer_ids) > 0"),
        ("len(customer_ids) > 0", "for customer_id in customer_ids", "else"),
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
        ("now >= target_time", "pokemon = fetch_random_pokemon()", "if now >= target_time"),
        ("now >= target_time", "sleep_secs = (target_time - now).total_seconds()", "else"),
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
        ("now >= target_time", "pokemon = fetch_random_pokemon()", "if now >= target_time"),
        ("now >= target_time", "sleep_secs = (target_time - now).total_seconds()", "else"),
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
        ("p['Link'] not in existing", "enriched = analyze_product(p)", "if p['Link'] not in existing"),
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
        ("customer_id != 'a'", "results.append(process_customer(customer_id))", "if customer_id != 'a'"),
        ("customer_id != 'a'", "print('do not process customer a')", "else"),
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
        ("len(customer_ids) > 0", "for customer_id in customer_ids", "if len(customer_ids) > 0"),
        ("len(customer_ids) > 0", "for customer_id in customer_ids", "else"),
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
        ("len(customer_ids) > 0", "for option in options \u2192 assign_option_to_customer(option, customer_id)", "if len(customer_ids) > 0"),
        ("for option in options \u2192 assign_option_to_customer(option, customer_id)", "results.append(process_customer(customer_id))", None),
        ("len(customer_ids) > 0", "print('no need for assigning since there is no customer')", "else"),
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
        ("len(customer_ids) > 0", "for customer_id in customer_ids", "if len(customer_ids) > 0"),
        ("len(customer_ids) > 0", "print('no need for assigning since there is no customer')", "else"),
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

def test_export_from_code_for_loop_with_sequential_after():
    """Test that nodes after a for loop are not marked as children of the loop."""
    code = '''
@flow
def main() -> None:
    res = get_messages()
    details = []
    for m in res.messages:
        details.append(get_message(m.id))
    summary = summarize_messages(details)
    subject = build_subject()
    email = build_email(subject, summary)
    send_message(email)
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input:"),
        ("operation", "res = get_messages()"),
        ("operation", "details = []"),
        ("loop", "for m in res.messages"),
        ("subroutine", "details.append(get_message(m.id))"),
        ("operation", "summary = summarize_messages(details)"),
        ("operation", "subject = build_subject()"),
        ("operation", "email = build_email(subject, summary)"),
        ("subroutine", "send_message(email)"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Expected parent relationships - only the append statement should be a child of the loop
    expected_parents = {
        "input:": None,
        "res = get_messages()": None,
        "details = []": None,
        "for m in res.messages": None,
        "details.append(get_message(m.id))": "for m in res.messages",  # Only this is a child
        "summary = summarize_messages(details)": None,  # Not a child
        "subject = build_subject()": None,  # Not a child
        "email = build_email(subject, summary)": None,  # Not a child
        "send_message(email)": None,  # Not a child
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
        ("input:", "res = get_messages()", None),
        ("res = get_messages()", "details = []", None),
        ("details = []", "for m in res.messages", None),
        ("for m in res.messages", "summary = summarize_messages(details)", None),
        ("summary = summarize_messages(details)", "subject = build_subject()", None),
        ("subject = build_subject()", "email = build_email(subject, summary)", None),
        ("email = build_email(subject, summary)", "send_message(email)", None),
    ])
    assert expected_edges == actual_edges

def test_export_from_code_bare_return_in_condition():
    """Test that bare return statement in if condition generates proper end node and edges."""
    code = '''
@flow
def main() -> None:
    emails = fetch_last_24h_emails("me")
    if emails.count == 0:
        return
    summary = summarize_emails(emails.text)
    raw = build_raw_email("user@example.com", "Daily Email Summary (Last 24h)", summary.summary, "recipient@example.com")
    tasks.google_mail.send_message(userId="me", body={"raw": raw.raw})
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input:"),
        ("operation", "emails = fetch_last_24h_emails('me')"),
        ("condition", "emails.count == 0"),
        ("end", "end function return"),  # The bare return creates an end node
        ("operation", "summary = summarize_emails(emails.text)"),
        ("operation", "raw = build_raw_email('user@example.com', 'Daily Email Summary (Last 24h)', summary.summary, 'recipient@example.com')"),
        ("subroutine", "tasks.google_mail.send_message(userId='me', body={'raw': raw.raw})"),
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
        ("input:", "emails = fetch_last_24h_emails('me')", None),
        ("emails = fetch_last_24h_emails('me')", "emails.count == 0", None),
        ("emails.count == 0", "end function return", "if emails.count == 0"),  # Yes branch goes to return
        ("emails.count == 0", "summary = summarize_emails(emails.text)", "else"),  # No branch continues
        ("summary = summarize_emails(emails.text)", "raw = build_raw_email('user@example.com', 'Daily Email Summary (Last 24h)', summary.summary, 'recipient@example.com')", None),
        ("raw = build_raw_email('user@example.com', 'Daily Email Summary (Last 24h)', summary.summary, 'recipient@example.com')", "tasks.google_mail.send_message(userId='me', body={'raw': raw.raw})", None),
    ])
    assert expected_edges == actual_edges

    # Verify the tasks data structure for the operations
    operation_nodes = [n for n in result['nodes'] if n['type'] == 'operation']

    # Check fetch_last_24h_emails task
    fetch_node = next((n for n in operation_nodes
                      if n['data']['label'] == "emails = fetch_last_24h_emails('me')"), None)
    assert fetch_node is not None
    assert 'tasks' in fetch_node['data']
    assert len(fetch_node['data']['tasks']) == 1
    assert fetch_node['data']['tasks'][0]['name'] == 'fetch_last_24h_emails'
    assert fetch_node['data']['tasks'][0]['args'][0]['value'] == "'me'"

    # Check summarize_emails task
    summarize_node = next((n for n in operation_nodes
                          if n['data']['label'] == "summary = summarize_emails(emails.text)"), None)
    assert summarize_node is not None
    assert 'tasks' in summarize_node['data']
    assert len(summarize_node['data']['tasks']) == 1
    assert summarize_node['data']['tasks'][0]['name'] == 'summarize_emails'
    assert summarize_node['data']['tasks'][0]['args'][0]['type'] == 'attribute'

    # Check build_raw_email task
    build_node = next((n for n in operation_nodes
                      if 'build_raw_email' in n['data']['label']), None)
    assert build_node is not None
    assert 'tasks' in build_node['data']
    assert len(build_node['data']['tasks']) == 1
    assert build_node['data']['tasks'][0]['name'] == 'build_raw_email'
    assert len(build_node['data']['tasks'][0]['args']) == 4

    # Check subroutine node
    subroutine_nodes = [n for n in result['nodes'] if n['type'] == 'subroutine']
    send_node = next((n for n in subroutine_nodes
                     if 'send_message' in n['data']['label']), None)
    assert send_node is not None
    assert 'tasks' in send_node['data']
    assert send_node['data']['tasks'][0]['name'] == 'send_message'
    assert any(arg['name'] == 'userId' for arg in send_node['data']['tasks'][0]['args'])
    assert any(arg['name'] == 'body' for arg in send_node['data']['tasks'][0]['args'])

def test_export_from_code_condition_after_loop_bug():
    """Test that condition after for loop is not marked as child of loop (bug fix)."""
    code = '''
def main(event) -> None:
    msgs = list_messages(userId="me", q="newer_than:1d", maxResults=100)
    for m in msgs.messages:
        gm = get_message(userId="me", id=m.id)
        if gm.snippet:
            corpus = corpus + "- " + gm.snippet
    ai = create_chat_completion(model="gpt-4.1-mini", messages=[{"role": "system", "content": "Write a summary"}, {"role": "user", "content": corpus}], temperature=0.2)
    if msgs.resultSizeEstimate > 5:
        send_message(userId="me", body={"raw": ai.choices[0].message.content})
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input: event"),
        ("operation", "msgs = list_messages(userId='me', q='newer_than:1d', maxResults=100)"),
        ("loop", "for m in msgs.messages"),
        ("operation", "gm = get_message(userId='me', id=m.id)"),
        ("condition", "gm.snippet"),
        ("operation", "corpus = corpus + '- ' + gm.snippet"),
        ("operation", "ai = create_chat_completion(model='gpt-4.1-mini', messages=[{'role': 'system', 'content': 'Write a summary'}, {'role': 'user', 'content': corpus}], temperature=0.2)"),
        ("condition", "msgs.resultSizeEstimate > 5"),
        ("subroutine", "send_message(userId='me', body={'raw': ai.choices[0].message.content})"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Critical test: The condition "msgs.resultSizeEstimate > 5" should NOT have the loop as parent
    # This is the bug we're fixing
    result_size_condition = next((n for n in result['nodes']
                                 if n['data']['label'] == "msgs.resultSizeEstimate > 5"), None)
    assert result_size_condition is not None, "Could not find msgs.resultSizeEstimate > 5 condition"
    assert 'parentId' not in result_size_condition, f"Condition 'msgs.resultSizeEstimate > 5' should not have a parent, but has parentId: {result_size_condition.get('parentId')}"

    # Expected parent relationships (label -> parent_label or None)
    expected_parents = {
        "input: event": None,
        "msgs = list_messages(userId='me', q='newer_than:1d', maxResults=100)": None,
        "for m in msgs.messages": None,
        "gm = get_message(userId='me', id=m.id)": "for m in msgs.messages",
        "gm.snippet": "for m in msgs.messages",
        "corpus = corpus + '- ' + gm.snippet": "for m in msgs.messages",
        "ai = create_chat_completion(model='gpt-4.1-mini', messages=[{'role': 'system', 'content': 'Write a summary'}, {'role': 'user', 'content': corpus}], temperature=0.2)": None,
        "msgs.resultSizeEstimate > 5": None,  # This is the key test - should be None, not the loop
        "send_message(userId='me', body={'raw': ai.choices[0].message.content})": None,
    }

    # Build label to nodes mapping and check parent relationships
    label_to_nodes = {}
    for n in result['nodes']:
        label_to_nodes.setdefault(n['data']['label'], []).append(n)

    # Create mapping from label to parent label
    label_to_parent = {}
    node_map = {n['id']: n for n in result['nodes']}
    for node in result['nodes']:
        label = node['data']['label']
        parent_id = node.get('parentId')
        parent_label = node_map[parent_id]['data']['label'] if parent_id else None
        label_to_parent[label] = parent_label

    assert expected_parents == label_to_parent, f"Parent relationships don't match. Expected: {expected_parents}, Got: {label_to_parent}"

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
        ("input: event", "msgs = list_messages(userId='me', q='newer_than:1d', maxResults=100)", None),
        ("msgs = list_messages(userId='me', q='newer_than:1d', maxResults=100)", "for m in msgs.messages", None),
        ("for m in msgs.messages", "ai = create_chat_completion(model='gpt-4.1-mini', messages=[{'role': 'system', 'content': 'Write a summary'}, {'role': 'user', 'content': corpus}], temperature=0.2)", None),
        ("gm = get_message(userId='me', id=m.id)", "gm.snippet", None),
        ("gm.snippet", "corpus = corpus + '- ' + gm.snippet", "if gm.snippet"),
        ("ai = create_chat_completion(model='gpt-4.1-mini', messages=[{'role': 'system', 'content': 'Write a summary'}, {'role': 'user', 'content': corpus}], temperature=0.2)", "msgs.resultSizeEstimate > 5", None),
        ("msgs.resultSizeEstimate > 5", "send_message(userId='me', body={'raw': ai.choices[0].message.content})", "if msgs.resultSizeEstimate > 5"),
    ])
    assert expected_edges == actual_edges

def test_export_from_code_condition_before_loop_bug():
    """Test that condition before for loop is not marked as child of loop (bug fix)."""
    code = '''
def main(event) -> None:
    lm = list_messages(userId="me", maxResults=100)
    count = len(lm.messages)
    if count < 5:
        raw = "raw"
        send_message(userId="me", body={"raw": raw})
        print(count, "email")
        return
    for m in lm.messages:
        gm = get_message(userId="me", id=m.id)
    comp = create_chat_completion(model="gpt-4.1-mini")
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input: event"),
        ("operation", "lm = list_messages(userId='me', maxResults=100)"),
        ("operation", "count = len(lm.messages)"),
        ("condition", "count < 5"),
        ("operation", "raw = 'raw'"),
        ("subroutine", "send_message(userId='me', body={'raw': raw})"),
        ("subroutine", "print(count, 'email')"),
        ("end", "end function return"),
        ("loop", "for m in lm.messages"),
        ("operation", "gm = get_message(userId='me', id=m.id)"),
        ("operation", "comp = create_chat_completion(model='gpt-4.1-mini')"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Expected parent relationships (label -> parent_label or None)
    # CRITICAL: The condition "count < 5" comes BEFORE the loop, so it should NOT have the loop as parent
    expected_parents = {
        "input: event": None,
        "lm = list_messages(userId='me', maxResults=100)": None,
        "count = len(lm.messages)": None,
        "count < 5": None,  # This is the key fix - should NOT have loop as parent
        "raw = 'raw'": None,
        "send_message(userId='me', body={'raw': raw})": None,
        "print(count, 'email')": None,
        "end function return": None,
        "for m in lm.messages": None,
        "gm = get_message(userId='me', id=m.id)": "for m in lm.messages",
        "comp = create_chat_completion(model='gpt-4.1-mini')": None,
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
        ("input: event", "lm = list_messages(userId='me', maxResults=100)", None),
        ("lm = list_messages(userId='me', maxResults=100)", "count = len(lm.messages)", None),
        ("count = len(lm.messages)", "count < 5", None),
        ("count < 5", "raw = 'raw'", "if count < 5"),
        ("raw = 'raw'", "send_message(userId='me', body={'raw': raw})", None),
        ("send_message(userId='me', body={'raw': raw})", "print(count, 'email')", None),
        ("print(count, 'email')", "end function return", None),
        ("count < 5", "for m in lm.messages", "else"),
        ("for m in lm.messages", "comp = create_chat_completion(model='gpt-4.1-mini')", None),
    ])
    assert expected_edges == actual_edges

def test_export_from_code_nested_loop_inside_condition():
    """Test nested loop inside a condition inside an outer loop - ensures correct parentId assignment."""
    code = '''
@flow
def main() -> list[str]:
    results = []
    for item in items:
        process_item(item)
        if item.has_children:
            for child in item.children:
                process_child(child)
        finalize_item(item)
    return results
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input:"),
        ("operation", "results = []"),
        ("loop", "for item in items"),
        ("subroutine", "process_item(item)"),
        ("condition", "item.has_children"),
        ("loop", "for child in item.children"),
        ("subroutine", "process_child(child)"),
        ("subroutine", "finalize_item(item)"),
        ("end", "output:  results"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes

    # Expected parent relationships (label -> parent_label or None)
    expected_parents = {
        "input:": None,
        "results = []": None,
        "for item in items": None,  # Outer loop should NOT have a parent
        "process_item(item)": "for item in items",
        "item.has_children": "for item in items",
        "for child in item.children": "for item in items",  # Nested loop should have outer loop as parent
        "process_child(child)": "for item in items",
        "finalize_item(item)": "for item in items",
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
        ("input:", "results = []", None),
        ("results = []", "for item in items", None),
        ("for item in items", "output:  results", None),
        ("process_item(item)", "item.has_children", None),
        ("item.has_children", "for child in item.children", "if item.has_children"),
        ("item.has_children", "finalize_item(item)", "else"),
        ("for child in item.children", "process_child(child)", "loop"),  # Loop body entry
        ("for child in item.children", "finalize_item(item)", None),
        ("process_child(child)", "for child in item.children", None),  # Loop back
    ])
    assert expected_edges == actual_edges

def test_export_from_code_if_elif_else_multi_branch():
    """Test if/elif/else creates a single condition node with multi-branch edges."""
    code = '''
@flow
def main() -> list[str]:
    customer_ids = get_customer_ids()
    results = []
    if len(customer_ids) > 5:
        for customer_id in customer_ids:
            results.append(process_customer(customer_id))
    elif len(customer_ids) > 0:
        results.append(process_customer(customer_ids[0]))
    else:
        results.append("No customers found")
    notify_customers(customer_ids)
    return results
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input:"),
        ("operation", "customer_ids = get_customer_ids()"),
        ("operation", "results = []"),
        ("condition", "len(customer_ids) > 5"),  # Only ONE condition node
        ("loop", "for customer_id in customer_ids"),
        ("subroutine", "results.append(process_customer(customer_id))"),
        ("subroutine", "results.append(process_customer(customer_ids[0]))"),
        ("subroutine", "results.append('No customers found')"),
        ("subroutine", "notify_customers(customer_ids)"),
        ("end", "output:  results"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes, f"Expected {expected_nodes}, got {actual_nodes}"

    # Verify there's only ONE condition node (not two)
    condition_nodes = [n for n in result['nodes'] if n['type'] == 'condition']
    assert len(condition_nodes) == 1, f"Expected 1 condition node, got {len(condition_nodes)}"

    # Expected parent relationships (label -> parent_label or None)
    expected_parents = {
        "input:": None,
        "customer_ids = get_customer_ids()": None,
        "results = []": None,
        "len(customer_ids) > 5": None,
        "for customer_id in customer_ids": None,
        "results.append(process_customer(customer_id))": "for customer_id in customer_ids",
        "results.append(process_customer(customer_ids[0]))": None,
        "results.append('No customers found')": None,
        "notify_customers(customer_ids)": None,
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

    # Expected edges with multi-branch labels (source_label, target_label, edge_label)
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
        ("results = []", "len(customer_ids) > 5", None),
        # Multi-branch edges from single condition node
        ("len(customer_ids) > 5", "for customer_id in customer_ids", "if len(customer_ids) > 5"),
        ("len(customer_ids) > 5", "results.append(process_customer(customer_ids[0]))", "elif len(customer_ids) > 0"),
        ("len(customer_ids) > 5", "results.append('No customers found')", "else"),
        # Sequential edges after branches
        ("for customer_id in customer_ids", "notify_customers(customer_ids)", None),
        ("results.append(process_customer(customer_ids[0]))", "notify_customers(customer_ids)", None),
        ("results.append('No customers found')", "notify_customers(customer_ids)", None),
        ("notify_customers(customer_ids)", "output:  results", None),
    ])
    assert expected_edges == actual_edges, f"Expected edges:\n{sorted(expected_edges)}\n\nGot:\n{sorted(actual_edges)}"

    # Verify the multi-branch edge labels explicitly
    condition_edges = [e for e in result['edges'] if e['source'] == condition_nodes[0]['id']]
    edge_labels = sorted([e.get('label', '') for e in condition_edges])
    expected_labels = sorted([
        "if len(customer_ids) > 5",
        "elif len(customer_ids) > 0",
        "else"
    ])
    assert edge_labels == expected_labels, f"Expected edge labels {expected_labels}, got {edge_labels}"

def test_export_from_code_if_elif_elif_else_four_branches():
    """Test if/elif/elif/else creates a single condition node with 4 multi-branch edges."""
    code = '''
@flow
def main() -> str:
    score = get_score()
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    else:
        grade = "F"
    return grade
    '''
    flow = ReactFlow.from_code(code, field="main", simplify=False, inner=False)
    result = flow.export()

    # Expected nodes (type, label)
    expected_nodes = set([
        ("start", "input:"),
        ("operation", "score = get_score()"),
        ("condition", "score >= 90"),  # Only ONE condition node
        ("operation", "grade = 'A'"),
        ("operation", "grade = 'B'"),
        ("operation", "grade = 'C'"),
        ("operation", "grade = 'F'"),
        ("end", "output:  grade"),
    ])
    actual_nodes = set((n['type'], n['data']['label']) for n in result['nodes'])
    assert expected_nodes == actual_nodes, f"Expected {expected_nodes}, got {actual_nodes}"

    # Verify there's only ONE condition node (not three)
    condition_nodes = [n for n in result['nodes'] if n['type'] == 'condition']
    assert len(condition_nodes) == 1, f"Expected 1 condition node, got {len(condition_nodes)}"

    # Verify the condition has exactly 4 outgoing edges
    condition_edges = [e for e in result['edges'] if e['source'] == condition_nodes[0]['id']]
    assert len(condition_edges) == 4, f"Expected 4 edges from condition, got {len(condition_edges)}"

    # Expected parent relationships (label -> parent_label or None)
    expected_parents = {
        "input:": None,
        "score = get_score()": None,
        "score >= 90": None,
        "grade = 'A'": None,
        "grade = 'B'": None,
        "grade = 'C'": None,
        "grade = 'F'": None,
        "output:  grade": None,
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

    # Expected edges with multi-branch labels (source_label, target_label, edge_label)
    label_map = {n['id']: n['data']['label'] for n in result['nodes']}
    def edge_tuple(e):
        return (
            label_map.get(e['source'], e['source']),
            label_map.get(e['target'], e['target']),
            e.get('label', None)
        )
    actual_edges = set(edge_tuple(e) for e in result['edges'])
    expected_edges = set([
        ("input:", "score = get_score()", None),
        ("score = get_score()", "score >= 90", None),
        # Four multi-branch edges from single condition node
        ("score >= 90", "grade = 'A'", "if score >= 90"),
        ("score >= 90", "grade = 'B'", "elif score >= 80"),
        ("score >= 90", "grade = 'C'", "elif score >= 70"),
        ("score >= 90", "grade = 'F'", "else"),
        # Sequential edges after branches converge
        ("grade = 'A'", "output:  grade", None),
        ("grade = 'B'", "output:  grade", None),
        ("grade = 'C'", "output:  grade", None),
        ("grade = 'F'", "output:  grade", None),
    ])
    assert expected_edges == actual_edges, f"Expected edges:\n{sorted(expected_edges)}\n\nGot:\n{sorted(actual_edges)}"

    # Verify the 4 multi-branch edge labels explicitly
    edge_labels = sorted([e.get('label', '') for e in condition_edges])
    expected_labels = sorted([
        "if score >= 90",
        "elif score >= 80",
        "elif score >= 70",
        "else"
    ])
    assert edge_labels == expected_labels, f"Expected edge labels {expected_labels}, got {edge_labels}"

    # Additional verification: ensure labels are in correct order conceptually
    # (if first, elif middle, else last)
    labels_with_source_target = [(e.get('label', ''), label_map.get(e['target'], '')) for e in condition_edges]

    # Check that we have exactly one 'if', two 'elif', and one 'else'
    if_count = sum(1 for label, _ in labels_with_source_target if label.startswith('if '))
    elif_count = sum(1 for label, _ in labels_with_source_target if label.startswith('elif '))
    else_count = sum(1 for label, _ in labels_with_source_target if label == 'else')

    assert if_count == 1, f"Expected 1 'if' branch, got {if_count}"
    assert elif_count == 2, f"Expected 2 'elif' branches, got {elif_count}"
    assert else_count == 1, f"Expected 1 'else' branch, got {else_count}"

if __name__ == "__main__":
    pytest.main([__file__])
